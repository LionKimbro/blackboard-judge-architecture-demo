# Module — Interaction Organisms

## Source Evidence

`src/demo/app.py` — `evaluate_organisms()`, `organism_*`, and
`handle_*_state()` functions.

## Render Target

`src/bad_demo/organisms.py`

## OWNS

- Organism finite-state-machine records and organism-local held/data values.
- Gesture behavior for hover, object dragging, resize, marquee selection, and
  click selection.
- Emission of semantic world-mutation and volatile projection-preview effects.

## READS

- RAW and DERIVED facts.
- Current durable world objects and committed selection.
- Judge permission results.
- The current quantization fact and configured step when a gesture proposes
  geometry.  See [Quantization](../aspects/quantization.md).

## CALLS

- `judge.get_permission()`.
- Functions that help emit "effects."
- Functions that calculate geometry, that are not perception,
  such as clamped resize results or marquee rectangle details.

## MAY SAFELY ASSUME

- Raw facts and tokenizers have all completed, this cycle.
- The world model remains stable while all organisms run.
- The effect queue is empty when evaluation begins.

## ENSURES

- Organisms express interaction as episodes, normally IDLE → ARMED → ACTIVE.
- A committed interaction changes the world only by emitting an effect.
- In-progress feedback is emitted as volatile projection effects.
- Organisms are isolated from one another.  No organism encodes knowledge of a sibling organism's behavior or priority.

## DOES NOT OWN

- Hit-testing
- Button click or double-click detection
- Drag-threshold recognition
- Resource arbitration
- Direct world mutation
- (direct) Canvas drawing


## Included Organisms

- Hover highlight: stateless per-cycle preview when the pointer is available.
- Resize object: handle press, threshold commit, resize preview and final
  resize effect.
- Drag objects: press, threshold commit, object-or-selection preview and final
  move effect.
- Marquee select: empty-space press, threshold commit, candidate preview and
  final selection effect.
- Select object on click: a tokenizer-derived click over a draggable object
  emits the ordinary single-object selection effect.

## Pseudo-code

```python
IDLE = "IDLE"
ARMED = "ARMED"
DRAGGING = "DRAGGING"
SELECTING = "SELECTING"


organisms_in_registration_order = [
    hover_highlight,
    organism_select_object_on_click,
    resize_object,
    drag_objects,
    marquee_select,
]

note: When multiple organisms become eligible in the same cycle,
      registration order is priority. The first organism that
      successfully COMMITs a permission, wins; later organisms are
      denied and clear their own episode state.

def evaluate_organisms():
    EFFECTS.clear()

    for organism in organisms_in_registration_order:
        if organism.active:
            organism.fn()


def clear_current_organism(organism):
    state <- IDLE
    clear held ({})
    clear data ({})
```

### Hover Highlight

```python
def organism_hover_highlight():
    if the pointer isn't over a draggable model object, get out

    if Judge says pointer is held by another organism, get out

    emit an immediate projection:
        "hover-highlight",
        {"object-id": the pointer target},
```

Hover has no episode state and never claims the pointer.  Its effect exists for
this projection pass only.


### Drag Objects

```python
def organism_drag_objects(organism):
    IDLE state:
        if the left mouse button wasn't just pressed, get out.
        if the mouse pointer isn't pointing at a draggable model object, get out.
          (note: a tokenizer identifies this.)

        ask the judge if permission to use the pointer is available --
          that is, CHECK permission: "pointer"; if it isn't, get out.

        SUCCESS:
        state <- ARMED

        if the object under the pointer belongs to the committed selection:
            record all object-IDs in the committed selection
            record the starting X, Y positions of all selected objects
        otherwise:
            record the object-ID of the object under the pointer
            record its starting X, Y position and current geometry

        record the current mouse X, Y position (from RAW data)

    ARMED state:
        if the button is released, clear state to IDLE and get out.

        if we haven't passed the drag threshold, get out.

        ah, so we HAVE passed the drag threshold:
        ask the Judge to COMMIT permission to the pointer and all object-IDs
        being dragged; if it cannot, clear state to IDLE and get out.

        emit the world effect:
	    set-selection,
	    object-ids = the object(s) being dragged

        state <- DRAGGING

    DRAGGING state:
        calculate lawful proposed positions for every object being dragged:
            use the one shared drag delta.
            when quantization is enabled, snap that shared delta before
              constraining it.

        emit a drag-preview for all objects being dragged, at their proposed
          positions.

        if the left mouse button is released, emit:
            move-objects,
            object-ids,
            proposed positions
        ...and then clear state to IDLE.
```

The drag-preview payload is a proposed position for each affected object, not a
request to mutate the world.  Projection must use it to display every affected
object at its proposed position for this frame; see `projection.md`.


### Resize Object

```python
def organism_resize_object(organism):
    if organism.state == IDLE:
        if not DERIVED.button_1_pressed:
            return
        if DERIVED.pointer_handle_target is None:
            return
        if not judge.get_permission(CHECK, ["pointer"]):
            return

        organism.state = ARMED
        organism.held = DERIVED.pointer_handle_target
        organism.data = {
            "start-rect": copy_of_world_object(organism.held["object-id"]),
        }
        return

    if organism.state == ARMED:
        if DERIVED.button_1_released:
            clear_current_organism(organism)
            return
        if not DERIVED.drag_threshold_crossed:
            return
        if not judge.get_permission(COMMIT, ["pointer", organism.held["object-id"]]):
            clear_current_organism(organism)
            return
        organism.state = DRAGGING

    if organism.state == DRAGGING:
        calculate a lawful proposed rectangle from the starting rectangle,
          held handle, and current pointer position.
        when quantization is enabled, use a snapped pointer position to make
          that proposal.

        emit a resize-preview containing the proposed rectangle.
        if DERIVED.button_1_released:
            emit a resize-object world effect containing that same proposed
              rectangle.
            clear_current_organism(organism)
```

### Marquee Selection

```python
def organism_marquee_select(organism):
    IDLE state:
        if the left mouse button wasn't just pressed, get out.
        if the mouse pointer is over anything, get out

        ask the Judge if permission to use the pointer is available --
          that is, CHECK permission: "pointer"; if it isn't, get out.

        SUCCESS:
        state <- ARMED
        record the current mouse X, Y position as the marquee anchor.

    ARMED state:
        if the button is released:
            emit the world effect: set-selection, object-ids = []
            clear state to IDLE and get out.

        if we haven't passed the drag threshold, get out.

        ah, so we HAVE passed the drag threshold:
        ask the Judge to COMMIT permission to the pointer;
          if it cannot, clear state to IDLE and get out.

        state <- SELECTING

    SELECTING state:
        calculate the rectangle from the marquee anchor to the current mouse
          X, Y position.
        find the model objects that intersect that rectangle.

        emit a marquee-preview containing the rectangle and those candidate
          object IDs.

        if the left mouse button is released:
            emit the world effect: set-selection, object-ids = the candidates
            clear state to IDLE.
```

### Select Object on Click

```text
def organism_select_object_on_click(organism):
    if a click event just occurred, (identified in DERIVED)
    AND I can get permission to the pointer (CHECK),
    AND the mouse target is a draggable object (but not a handle)):
        emit the world effect "set-selection,"
	  supplying the object-id of the object
```

# Module — Interaction Organisms

## Source Evidence

`src/demo/app.py` — `evaluate_organisms()`, `organism_*`, and
`handle_*_state()` functions.

## Render Target

`src/bad_demo/organisms.py`

## OWNS

- Organism finite-state-machine records and organism-local held/data values.
- Gesture behavior for hover, single-object drag, resize, marquee selection,
  and selected-group drag.
- Emission of semantic world-mutation and volatile projection-preview effects.

## READS

- RAW and DERIVED facts.
- Current durable world objects and committed selection.
- Judge permission results.

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
- Drag-threshold recognition
- Resource arbitration
- Direct world mutation
- (direct) Canvas drawing

## Included Organisms

- Hover highlight: stateless per-cycle preview when the pointer is available.
- Resize object: handle press, threshold commit, resize preview and final
  resize effect.
- Drag object: press, threshold commit, position preview and final move effect.
- Marquee select: empty-space press, threshold commit, candidate preview and
  final selection effect.
- Drag selection group: selected-object press, threshold commit, group preview
  and final bounded move effect.

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
    drag_selection_group,
    drag_object,
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
    organism.state = IDLE
    organism.held = {}
    organism.data = {}
```

### Hover Highlight

```python
def organism_hover_highlight():
    if DERIVED.pointer_target is None:
        return

    if Judge says pointer is held by another organism:
        return

    emit_projection_preview(
        "hover-highlight",
        {"object-id": DERIVED.pointer_target},
    )
```

Hover has no episode state and never claims the pointer.  Its effect exists for
this projection pass only.

### Single-Object Drag

```python
def organism_drag_object(organism):
    IDLE state:
        if the left mouse button wasn't just pressed, get out.
	if the mouse pointer isn't pointing at a draggable model object, get out.
	  (note: a tokenizer identifies this.)

        ask the judge if permission to use the pointer is available --
	  that is, CHECK permission: "pointer";  if it isn't, get out

        SUCCESS:
	state <- ARMED
	record the object-ID of the relevant object under the pointer
	record the current mouse X, Y position (from RAW data)
	record the object's current geometry

    ARMED state:

        if the button is released, clear state to IDLE and get out.

        if we haven't passed the drag threshold, get out.

        ah, so we HAVE passed the drag threshold:
          if we can't COMMIT permission to pointer and holding the object-id, clear state to IDLE and get out.

        state <- DRAGGING

    DRAGGING state:
        calculate a proposed drag position, respecting clamping

        emit a drag-preview for this object, at the proposed x,y position

        if the left mouse button is released, emit:
	    move-object,
	    object-id,
	    x,
	    y
	...and then clear state to IDLE.
```

The drag-preview payload is a proposed object position, not a request to mutate
the world.  Projection must use it to display the object at the proposed
position for this frame; see `projection.md`.

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
        proposed_rect = compute_bounded_resize_rect(
            organism.data["start-rect"], organism.held["handle"], RAW.x, RAW.y,
        )
        emit_projection_preview("resize-preview", {
            "object-id": organism.held["object-id"],
            "rect": proposed_rect,
        })
        if DERIVED.button_1_released:
            emit_world_effect("resize-object", {
                "object-id": organism.held["object-id"],
                "handle": organism.held["handle"],
                "start-rect": organism.data["start-rect"],
                "x": RAW.x,
                "y": RAW.y,
            })
            clear_current_organism(organism)
```

### Marquee Selection

```python
def organism_marquee_select(organism):
    if organism.state == IDLE:
        if not DERIVED.button_1_pressed or DERIVED.pointer_target is not None:
            return
        if not judge.get_permission(CHECK, ["pointer"]):
            return
        organism.state = ARMED
        organism.data = {"anchor": {"x": RAW.x, "y": RAW.y}}
        return

    if organism.state == ARMED:
        if DERIVED.button_1_released:
            emit_world_effect("set-selection", {"object-ids": []})
            clear_current_organism(organism)
            return
        if not DERIVED.drag_threshold_crossed:
            return
        if not judge.get_permission(COMMIT, ["pointer"]):
            clear_current_organism(organism)
            return
        organism.state = SELECTING

    if organism.state == SELECTING:
        rect = rectangle_from(organism.data["anchor"], RAW)
        candidates = objects_intersecting(rect)
        emit_projection_preview("marquee-preview", {
            "rect": rect,
            "object-ids": candidates,
        })
        if DERIVED.button_1_released:
            emit_world_effect("set-selection", {"object-ids": candidates})
            clear_current_organism(organism)
```

### Selected-Group Drag

```python
def organism_drag_selection_group(organism):
    IDLE state:
        if the left mouse button wasn't just pressed, get out.
        if the mouse pointer isn't pointing at a draggable model object, get out.
          (note: a tokenizer identifies this.)
        if the object under the pointer is not in the committed selection,
          get out.
        if the committed selection does not contain multiple objects, get out.

        ask the judge if permission to use the pointer is available --
          that is, CHECK permission: "pointer"; if it isn't, get out.

        SUCCESS:
        state <- ARMED
        record the object-IDs in the committed selection
        record the current mouse X, Y position (from RAW data)
        record the starting X, Y positions of all selected objects

    ARMED state:
        if the button is released, clear state to IDLE and get out.

        if we haven't passed the drag threshold, get out.

        ah, so we HAVE passed the drag threshold:
          ask the Judge to COMMIT permission to the pointer and all selected
          object-IDs; if it cannot, clear state to IDLE and get out.

        state <- DRAGGING

    DRAGGING state:
        calculate a proposed group delta, respecting clamping for the whole
          selected group.

        emit a group-drag-preview for all selected objects, at their proposed
          positions.

        if the left mouse button is released, emit:
            move-group,
            object-ids,
            starting positions,
            dx,
            dy
        ...and then clear state to IDLE.
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

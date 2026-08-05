# Module — Projection

## Source Evidence

`src/demo/app.py` — `render_projection()`, `draw_*()` functions, and panel
line construction.

## Render Target

`src/bad_demo/projection.py`

## OWNS

- Canvas drawing for world objects, selection, resize handles, and transient
  previews.
- Visual manifestations of world objects, selection, resize handles, divider,
  and architecture panel.
- The presentation decision whether the Grid should be visible, based on the
  current "show grid" control value.
- Projection-private Canvas handles/state if retained-mode reconciliation is
  selected.

## READS

- Durable world state.
- Current cycle's volatile effects.
- Runtime facts only for explicitly presentational status display.
- Runtime's authoritative display configuration, from which it passes a
  grid-configuration request to Grid.

## CALLS

- Canvas interface operations.
- Geometry and selection display helpers.
- Grid's narrow presentation service to ensure and show or hide the background
  grid.

## MAY SAFELY ASSUME

- Effects-world has already applied all persistent effects.
- Canvas access occurs on the Tkinter main thread.

## ENSURES

- The Canvas visibly reflects the world and current-frame preview effects.
- Object previews temporarily override the rendered presentation of their
  referenced objects.  While such an override is present, the object's durable
  geometry is not separately requested at its original position.
- Long-lived visual items reconcile by logical key: create missing items, update
  changed items, and delete items no longer requested.
- Immediate Canvas items are tagged `immediate`, deleted at the start of the
  next projection pass, and recreated only when current volatile effects call
  for them.
- No drawing operation changes semantic world, organism, or coordination state.
- Volatile effects disappear when not re-emitted in the next cycle.
- Projection requests Grid visibility, but does not create, configure, tag, or
  layer grid-line Canvas items.
- "Show Grid" affects Projection only through Grid visibility
- "Quantization" affects Projection only through the geometry already
  supplied by previews or world state; Projection does not snap.

## DOES NOT OWN

- Input interpretation, gesture behavior, permission decisions, or world
  mutation.

## Decision

Use retained-mode reconciliation.  See
[retained-mode-projection ADR](../adr/retained-mode-projection.md).

## Preview Presentation Overrides

Drag and resize previews describe proposed object geometry for the current
frame.  Projection applies that geometry while building its retained desired
state, rather than drawing a second, immediate copy of the object.  On the next
pass, an absent preview returns the object's presentation to durable world
geometry; a committed world effect normally makes that geometry match the last
preview.

While an object has a drag preview, its ordinary manipulation handles are not
requested.  The drag itself is the active manipulation presentation.

Immediate effects remain appropriate for overlays that do not stand in for a
durable object visual, such as hover highlights and marquee outlines.  A
marquee preview also draws the hover-style halo around each of its candidate
objects; this is a presentation of marquee candidacy, not an emitted hover
fact.

## Narrative Pseudo-code

```python
def render_projection():
    if there is no usable Canvas, get out.

    remove all Canvas items tagged "immediate":
        these were last frame's overlays and previews.

    begin a requested presentation, keyed by stable logical names.

    begin with the durable world objects' normal presentation:
        background
        decide whether Grid should be visible from the current
          show-grid-checkbox value.
        take the gridded-area bounds and spacing from Runtime configuration.
        every model object's body and label
        selection styling
        resize handles for a singly selected object

    examine this frame's projection previews before asking the Canvas to
      reconcile anything:

        for each drag-preview:
            temporarily replace every affected object's requested X, Y
              position with its proposed position.
            do not request resize handles for an object being dragged.

        for each resize-preview:
            temporarily replace its object's requested rectangle with the
              proposed resized rectangle.

    reconcile the requested presentation with retained Canvas items:
        for a requested logical item that has no Canvas item, create one.
        for a requested logical item whose presentation changed, update it.
        for a retained logical item that is no longer requested, delete it.

    ask Grid to ensure its static items exist for the Runtime-supplied grid
      configuration, and apply Projection's requested visibility.  Grid then
      maintains its own background layer beneath the reconciled model objects.

    now draw this frame's true immediate overlays:
        a hover-highlight draws a halo around its object.

        a marquee-preview draws its marquee outline, then draws that same
          halo around every candidate object named by the preview.

    finish:
        do not change world state, input facts, organism state, or Judge state.
```

The requested presentation is projection-private information: it maps logical
visual names such as an object's body, label, or handle to the Canvas item and
appearance currently required for that name.  It is not part of the durable
world model.

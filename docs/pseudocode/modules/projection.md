# Module — Projection

## Source Evidence

`src/demo/app.py` — `render_projection()`, `draw_*()` functions, and panel
line construction.

## Render Target

`src/bad_demo/projection.py`

## OWNS

- All Canvas drawing operations.
- Visual manifestations of world objects, selection, resize handles, grid,
  transient previews, divider, and architecture panel.
- Projection-private Canvas handles/state if retained-mode reconciliation is
  selected.

## READS

- Durable world state.
- Current cycle's volatile effects.
- Runtime facts only for explicitly presentational status display.

## CALLS

- Canvas interface operations.
- Geometry and selection display helpers.

## MAY SAFELY ASSUME

- Effects-world has already applied all persistent effects.
- Canvas access occurs on the Tkinter main thread.

## ENSURES

- The Canvas visibly reflects the world and current-frame preview effects.
- Long-lived visual items reconcile by logical key: create missing items, update
  changed items, and delete items no longer requested.
- Immediate Canvas items are tagged `immediate`, deleted at the start of the
  next projection pass, and recreated only when current volatile effects call
  for them.
- No drawing operation changes semantic world, organism, or coordination state.
- Volatile effects disappear when not re-emitted in the next cycle.

## DOES NOT OWN

- Input interpretation, gesture behavior, permission decisions, or world
  mutation.

## Decision

Use retained-mode reconciliation.  See
[retained-mode-projection ADR](../adr/retained-mode-projection.md).

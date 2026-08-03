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
- No drawing operation changes semantic world, organism, or coordination state.
- Volatile effects disappear when not re-emitted in the next cycle.

## DOES NOT OWN

- Input interpretation, gesture behavior, permission decisions, or world
  mutation.

## Open Decision

Select either full redraw for behavioral fidelity to the source demo or
retained-mode reconciliation for fidelity to `docs/book/15_projection.md`.
See `../aspects/open-decisions.md`.


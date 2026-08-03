# Interface — Tkinter Canvas

## Provided By

Python `tkinter.Canvas`.

## Used For

- Receiving pointer motion, press, release, and leave input.
- Rendering the world objects, interaction overlays, grid, and architecture
  status panel.

## Relied-Upon Operations

- Bind pointer events and receive Canvas-relative `x` and `y` coordinates.
- Create and delete rectangle, line, and text items.
- Configure Canvas dimensions and visual styling.

## Behavioral Facts

- Canvas items are retained until changed or deleted.
- Canvas item handles and visual state are projection-private, not model state.
- The Canvas may display a state that lags a just-mutated world until the next
  projection pass; the world model remains authoritative.

## Project Rules

- Only the projection module issues Canvas drawing operations.
- Tokenizers use world geometry for current hit-testing in this demo, rather
  than treating Canvas items as semantic objects.
- The re-render must choose and document either full redraw or retained-mode
  reconciliation; see `../aspects/open-decisions.md`.

## Documentation

- `docs/book/15_projection.md`
- `C:\lion\github\lions-documents\raw\0010__lions-tkinter-development-conventions_v1.json`


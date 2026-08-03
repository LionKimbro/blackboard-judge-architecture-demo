# Module — Geometry and Query Helpers

## Source Evidence

`src/demo/app.py` — object lookup, rectangle, clamping, snapping, resizing,
selection-display, and group-bound helper functions.

## Render Target

`src/bad_demo/geometry.py`

## OWNS

- Pure or near-pure geometric calculations used by other modules.
- Object and handle query operations over the world geometry.
- Bounds, snapping, rectangle intersection, group movement limits, and resize
  rectangle calculations.

## READS

- Explicit geometry values, or the current world when an object lookup is the
  operation's subject.

## CALLS

- No architectural subsystem.

## MAY SAFELY ASSUME

- Object rectangles use x/y/w/h fields.
- The playfield bounds and minimum dimensions are provided by configuration or
  a shared constants region.

## ENSURES

- Shared geometric rules are implemented once and used consistently by
  tokenizers, organisms, effects-world, and projection.
- Helpers do not mutate world state or Canvas state.

## DOES NOT OWN

- Tokenizer registration, effect emission, interaction state, or rendering.


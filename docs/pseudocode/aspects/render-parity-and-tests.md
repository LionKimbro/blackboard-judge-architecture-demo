# Aspect — Render Parity and Tests

## Participating Modules

All render-target modules, with primary coverage in `runtime`, `organisms`,
`effects-world`, and `geometry`.

## Purpose

The first BAD render is an experiment in controlled reproduction.  It should
demonstrate that the bounded sketches preserve the original interaction
behavior, except for any explicitly accepted open decision.

## Source Evidence

`tests/test_app_logic.py` describes the existing behavioral baseline:

- motionless-duration accumulation;
- marquee selection and clearing selection;
- selection collapse when pressing objects;
- single and group drag, including bounds;
- resize handles, resize bounds, and minimum size;
- quantization state, drag, group drag, and resize.

## Rules

- Preserve or deliberately replace each baseline behavior with a test against
  `bad_demo`.
- Tests should call the runtime with normalized input rather than require live
  Tk windows whenever possible.
- Tests must use a replaceable monotonic clock.
- Add queue tests for pointer-motion tail coalescing, preserved sample order,
  and the boundary created by an intervening non-motion event.
- A deliberate architectural difference from the source must cite its ADR in
  the relevant test and module sketch.

## Does Not Require

- Byte-for-byte source similarity.
- Matching internal function names or dictionary layout when behavior and
  declared contracts are intentionally updated together.

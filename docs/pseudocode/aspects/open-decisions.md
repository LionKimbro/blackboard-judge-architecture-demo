# Aspect — Open Decisions

## Projection Strategy for the Re-render

### Evidence

- The original implementation's `render_projection()` clears and redraws the
  Canvas on every cycle.
- `docs/book/15_projection.md` specifies a retained-mode desired-state and
  reconciliation approach.

### Dilemma

Should the first BAD render reproduce the original full-redraw behavior for
maximum behavioral fidelity, or should it render the manual's reconciliation
model as an intentional architectural correction?

### Boundary

Do not decide this while rendering another module.  The projection sketch must
remain explicit about the selected strategy, and tests should demonstrate the
chosen result.

## Current DERIVED Field: Complete Defaults or Strict Production

### Evidence

- The original demo resets DERIVED using `make_initial_derived()`, which
  supplies every known field with a default value each cycle.
- `docs/book/02_data_contracts.md` recommends starting DERIVED as empty so a
  tokenizer that fails to produce a required fact causes a loud missing-key
  error.

### Dilemma

Should the first BAD render keep complete default fields for close source
reproduction, or use strict per-tokenizer field production for stronger
contract checking?

### Boundary

This is a data-contract decision, not a tokenizer-local implementation detail.
The facts aspect and tests must state the selected policy.

## Permission Terminology: Historical or Current

### Evidence

- The original demo uses `START` and `HOLD-RESOURCE` constants.
- `docs/book/34_appendix_historical-note.md` and the CIRA brief use `CHECK`
  and `COMMIT` for the same feasibility/commitment distinction.

### Dilemma

Should the first BAD render preserve the original names for closer provenance,
or use the newer terms while keeping their existing operational meaning?

### Boundary

The selected vocabulary must be consistent across the Judge, organisms, facts,
architecture panel, tests, and documentation.

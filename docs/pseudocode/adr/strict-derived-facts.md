# ADR — Recompute DERIVED Strictly Each Cycle

## Status

Accepted for the BAD-rendered demo.

## Decision

At the start of every tokenizer pass, current DERIVED is an empty mapping.
Each tokenizer writes the facts it owns.  A missing required fact should fail
loudly when a consumer reads it, rather than silently receiving a default.

`make_initial_derived()` remains useful only to establish the previous-frame
baseline before the first cycle.  It is not used as the current-cycle DERIVED
field template after the tokenizer pass begins.

## Consequences

- Tokenizer ownership is observable and testable.
- Tokenizers must collectively populate every fact that the current organisms
  and projection panel require.
- The first cycle retains a meaningful `DERIVED-PREV` baseline, while current
  DERIVED still results solely from the tokenizer pass.

## Evidence

- Original behavior: `src/demo/app.py` — `make_initial_derived()` and
  `run_tokenizers()`.
- Architecture target: `docs/book/02_data_contracts.md`.


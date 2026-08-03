# Aspect — Facts and Blackboard Contract

## Participating Modules

`runtime`, `tokenizers`, `judge`, `organisms`, `effects-world`, and
`projection`.

## Shared Facts

- `RAW` and `RAW-PREV`: normalized input snapshots containing pointer position,
  button state, monotonic time, Canvas presence, hovered object, and the
  quantization setting.
- `DERIVED` and `DERIVED-PREV`: tokenized perception including motion deltas,
  button edges, pointer target, resize-handle target, and drag threshold.
- `COORDINATION`: Judge-owned pointer/resource ownership and diagnostic notes.
- `EFFECTS`: the current cycle's transient queue of world-mutation and
  projection-preview requests.
- `world`: durable objects and committed selection.
- Organism records: name, active flag, FSM state, held values, local data, and
  behavior function.

## Rules

- Runtime snapshots RAW and DERIVED before it replaces current-cycle values.
- Tokenizers are the only DERIVED writers.  Organisms read DERIVED but do not
  repair or augment it.
- The effect queue starts empty for each organism pass and is consumed in the
  same cycle.
- World data changes only while routing world-mutation effects.
- Current implementation names use hyphenated dictionary keys; the render may
  normalize naming only if every affected contract and test is changed together.

## Source Evidence

`src/demo/app.py` — `reset_demo_state()`, `make_initial_raw()`,
`make_initial_derived()`, and the `run_cycle()` section.

## Sources

- `docs/book/02_data_contracts.md`
- `docs/book/10_raw.md`


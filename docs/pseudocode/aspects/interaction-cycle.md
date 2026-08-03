# Aspect — Interaction Cycle

## Participating Modules

`app-shell`, `runtime`, `tokenizers`, `judge`, `organisms`, `effects-world`,
and `projection`.

## Rule

One interaction cycle has this fixed order:

```text
preserve RAW and DERIVED snapshots
populate current RAW
run tokenizers
maintain Judge state
run every active organism in registration order
maintain Judge state again
route effects into durable world mutation and current-frame previews
project the resulting visible state
```

## Why the Order Matters

- Organisms all receive the same current perception.
- Organisms see a stable world; no organism observes a world mutation emitted
  earlier in the same pass.
- The Judge prevents competing committed gestures from sharing exclusive
  resources.
- Projection sees effects after durable mutations have been applied.

## System Rules

- Input callbacks and periodic ticks both enter through this cycle.
- A periodic tick is allowed to run with no changed pointer data so temporal
  tokenizers can update.
- No component may invoke a later architectural stage early or re-enter the
  cycle from inside an organism.

## Source Evidence

`src/demo/app.py` — `run_cycle()`.

## Sources

- `docs/book/00_overview.md`
- `docs/book/01_core_principles.md`
- `docs/book/10_raw.md`


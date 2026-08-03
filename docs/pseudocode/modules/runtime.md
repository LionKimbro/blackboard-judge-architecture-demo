# Module — Interaction Runtime

## Source Evidence

`src/demo/app.py` — state initialization, `run_cycle()`, snapshot handling,
and RAW population.

## Render Target

`src/bad_demo/runtime.py`

## OWNS

- Construction and reset of the demo's shared runtime, world, and organism
  records.
- Cycle ordering and snapshot replacement.
- RAW population from callback input and current UI setting.

## READS

- Normalized callback updates.
- The quantization control through a narrow app-shell adapter.
- Monotonic clock interface.

## CALLS

- Tokenizer pass.
- Judge maintenance.
- Organism evaluation.
- Effect routing.
- Projection refresh.

## MAY SAFELY ASSUME

- Calls arrive on the Tkinter main thread.
- Called layers follow the contracts in `../aspects/architecture-ownership.md`.

## ENSURES

- RAW-PREV and DERIVED-PREV represent the prior completed cycle.
- Tokenizers run before organisms.
- All organisms run against one stable world state.
- Effects route after organism execution and before projection.
- A caller may invoke the cycle with no changed pointer data so temporal facts
  can advance without new pointer motion.

## DOES NOT OWN

- Perceptual field definitions, organism behavior, Judge policy, effect meaning,
  or Canvas commands.

## Sketch

```text
function run_cycle(raw-update, flags=[]):
    preserve_previous_snapshots()
    populate_current_raw(raw-update)
    run_tokenizers()
    maintain_judge()
    evaluate_organisms()
    maintain_judge()
    route_effects()
    project_current_state()
```

The initial render may use this same cycle as a priming cycle; no separate
startup-only interaction path is required.

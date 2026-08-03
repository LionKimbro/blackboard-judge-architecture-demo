# Module — Tokenizers

## Source Evidence

`src/demo/app.py` — `run_tokenizers()` and `tokenizer_*` functions.

## Render Target

`src/bad_demo/tokenizers.py`

## OWNS

- The current DERIVED perceptual field.
- Tokenizer-local state required for temporal perception, such as drag anchors
  and last-motion time.
- The ordered tokenizer registry.

## READS

- RAW and RAW-PREV snapshots.
- DERIVED-PREV when a tokenizer needs a prior perceptual fact.
- Current world geometry for hit-testing and resize-handle detection.

## CALLS

- Geometry helpers for object and resize-handle hit tests.

## MAY SAFELY ASSUME

- Runtime has populated the current RAW snapshot and preserved prior snapshots.
- World state is stable until effect routing begins.

## ENSURES

- Organisms receive one shared, complete perceptual interpretation for the
  cycle.
- Each fact is produced by its designated tokenizer, not recalculated by
  organisms.

## DOES NOT OWN

- Gesture FSM state, resource claims, effect emission, world mutation, or
  Canvas drawing.

## Included Tokenizers

- Pointer motion: delta, moving flag, and motionless duration.
- Primary-button edges: pressed and released facts.
- Pointer target: current, entered, and left object target.
- Resize handles: selected-object handle under the pointer.
- Drag threshold: anchor on press and whether the threshold is crossed.

## Sketch

```text
function run_tokenizers():
    reset_current_derived_field()
    for tokenizer in tokenizer_registry_in_order:
        if tokenizer.active:
            tokenizer.compute_its_facts()
```


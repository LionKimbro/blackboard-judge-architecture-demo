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
- Current DERIVED begins empty, so a missing required tokenizer fact is visible
  rather than disguised by a default value.

## DOES NOT OWN

- Gesture FSM state, resource claims, effect emission, world mutation, or
  Canvas drawing.

## Included Tokenizers

- Pointer motion: delta, moving flag, and motionless duration.
- Primary-button edges: pressed and released facts.
- Primary-button click: a press, followed by a release, without mouse motion in between, and within a short time frame.
- Primary-button double-click: (similar)
- Pointer target: current, entered, and left object target.
- ...and if the pointer target is a draggable model object, or a manipulation handle, or neither.
- Resize handles: selected-object handle under the pointer.
- Drag threshold: anchor on press and whether the threshold is crossed.

## Sketch

```text
tokenizers = []

function initialize_tokenizers():
    clear tokenizers
    register the tokenizer records in their required evaluation order

function run_tokenizers():
    set_current_derived_to_empty_mapping()
    for tokenizer in tokenizers:
        if tokenizer.active:
            tokenizer.compute_its_facts()
```

See [strict-derived-facts ADR](../adr/strict-derived-facts.md).

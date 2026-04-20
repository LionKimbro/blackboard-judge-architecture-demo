# 10 — RAW

## Purpose

RAW is the uninterpreted input record for the current and previous interaction cycle. It is the sole source of truth about what the input hardware reported. Nothing in RAW is interpreted; it is a faithful transcription of events.

---

## Structure

```
RAW.current:
    x               : number    -- pointer x in canvas-local coordinates
    y               : number    -- pointer y in canvas-local coordinates
    time_ms         : number    -- monotonic clock, milliseconds
    inside_canvas   : bool      -- pointer is within the canvas widget
    button_1_down   : bool      -- primary button is currently held

RAW.previous:
    [identical fields, frozen copy of RAW.current from the prior cycle]
```

Application-specific fields (key states, modifier keys, scroll delta) may be added. They follow the same rules: faithful transcription, no interpretation.

---

## Lifecycle

```
function advance_snapshots():
    RAW.previous ← deep_copy(RAW.current)
    DERIVED.previous ← deep_copy(DERIVED.current)

function populate_raw(event_fields):
    RAW.current ← merge(RAW.current, event_fields)
    RAW.current.time_ms ← monotonic_ms()
```

`advance_snapshots()` runs before `populate_raw()` each cycle. This guarantees that tokenizers always have access to both the current and prior frame.

---

## Snapshot Invariant

`RAW.previous` is always the exact state of `RAW.current` from the immediately preceding cycle. It is never modified after the snapshot is taken. Tokenizers depend on this for reliable edge detection.

---

## Input Sources

RAW is populated from Tk event callbacks:

```
on <Motion>:
    populate_raw({ x: event.x, y: event.y, inside_canvas: True,
                   button_1_down: [carry from current] })
    run_cycle()

on <ButtonPress-1>:
    populate_raw({ x: event.x, y: event.y, inside_canvas: True,
                   button_1_down: True })
    run_cycle()

on <ButtonRelease-1>:
    populate_raw({ x: event.x, y: event.y, inside_canvas: True,
                   button_1_down: False })
    run_cycle()

on <Leave>:
    populate_raw({ inside_canvas: False,
                   button_1_down: [carry from current] })
    run_cycle()
```

A periodic timer also triggers cycles for time-based organisms:

```
on tick:
    populate_raw({})    -- no input changes; just advance time
    run_cycle()
```

---

## Constraints

- RAW is written only by the cycle runner, never by tokenizers, organisms, the judge, or projection.
- RAW contains no interpreted data. It does not contain hit-test results, derived button events, or spatial relationships.
- `RAW.current` and `RAW.previous` are always present and always structurally complete (no missing fields).

# Module — Input Event Queue

## Source Evidence

This is an intentional BAD-render change.  The original `src/demo/app.py`
invokes the interaction cycle directly from Tk callbacks.

## Render Target

`src/bad_demo/event_queue.py`

## OWNS

- The FIFO queue of normalized, pending input events.
- Event posting and queue-tail inspection.
- Coalescing adjacent pending pointer-motion events into one motion packet.

## READS

- Normalized event records supplied by Canvas Host Window.

## CALLS

- No architectural module.  Runtime reads/drains this queue.

## MAY SAFELY ASSUME

- Producers post events on the Tkinter main thread.
- Runtime is the sole consumer.

## ENSURES

- Callbacks report input without advancing application logic immediately.
- Pending events retain FIFO order.
- Every queued record describes raw or normalized toolkit input facts only; it
  never declares the semantic meaning, command, gesture, selection, or world
  change inferred from that input.
- Consecutive pending pointer motions become one event containing an ordered
  list of time-and-position samples.
- A non-motion event prevents coalescing across its position in the queue.

## DOES NOT OWN

- Tk bindings, timer scheduling, RAW state, tokenization, gesture behavior,
  world mutation, or projection.
- Semantic command/event interpretation.

## Event Shapes

```python
pointer_motion_event = {
    "type": "POINTER_MOTION",
    "samples": [
        {"x": 100, "y": 120, "ms": 123456},
    ],
}
```

Other input events use a `type` and only the data required for their meaning,
such as primary-button press/release, pointer leave, key press/release, or a
supporting-widget activation/value change.

## See Also

[Input Event Contract](../aspects/input-event-contract.md) is the authoritative
vocabulary and field contract for every event that may enter or leave this
queue.  Input Event Queue owns ordering and motion coalescing, not event-type
meaning.

## Sketch

```python
event_queue = []

def post_pointer_motion(x, y, ms):
    sample = {"x": x, "y": y, "ms": ms}

    if event_queue and event_queue[-1]["type"] == "POINTER_MOTION":
        event_queue[-1]["samples"].append(sample)
        return

    event_queue.append({"type": "POINTER_MOTION", "samples": [sample]})


def drain_events():
    pending = list(event_queue)
    event_queue.clear()
    return pending
```

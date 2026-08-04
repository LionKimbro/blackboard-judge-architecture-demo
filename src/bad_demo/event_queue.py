"""Raw input-event queue with adjacent pointer-motion coalescing."""


events = []


def post_event(event):
    """Append one raw input event without assigning it application meaning."""
    events.append(event)


def post_pointer_motion(x, y, ms):
    """Append a timestamped motion sample to the pending motion tail if present."""
    sample = {"x": x, "y": y, "ms": ms}
    if events and events[-1]["type"] == "POINTER_MOTION":
        events[-1]["samples"].append(sample)
        return
    events.append({"type": "POINTER_MOTION", "samples": [sample]})


def drain_events():
    """Return all pending input events in FIFO order and clear the queue."""
    pending = list(events)
    events.clear()
    return pending

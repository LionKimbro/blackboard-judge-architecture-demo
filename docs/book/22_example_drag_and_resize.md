# 22 — Example: Drag and Resize

## Overview

Two related gestures share this example to illustrate how the Judge prevents them from conflicting.

**Drag:** The user presses on an unselected object body and drags it to a new position.

**Resize:** The user presses on a visible corner handle of the currently-selected object and drags to change its size.

Both gestures follow the same IDLE → ARMED → ACTIVE/DRAGGING pattern. The Judge ensures only one can hold a given object at a time.

---

## Tokenizers Used

**hit-test tokenizer** — identifies the object under the pointer:
```
DERIVED.current.pointer_target ← "alpha"   -- if over object body
DERIVED.current.pointer_target ← None       -- if over empty space
```

**resize-handle tokenizer** — identifies a handle under the pointer:
```
-- Only meaningful when exactly one object is selected.
-- Checks each corner of the selected object's bounding box.

function tokenizer_resize_handles(data):
    if len(world.selection) != 1:
        DERIVED.current.pointer_handle_target ← None
        return
    id  ← world.selection[0]
    obj ← world.objects[id]
    for handle in ("nw", "ne", "sw", "se"):
        cx, cy ← handle_center(obj, handle)
        if distance(RAW.current.x, RAW.current.y, cx, cy) <= HANDLE_HIT_RADIUS:
            DERIVED.current.pointer_handle_target ← { object_id: id, handle: handle }
            return
    DERIVED.current.pointer_handle_target ← None
```

**button-state tokenizer** and **drag-threshold tokenizer** as usual.

---

## Drag Organism Pipeline

### Cycle 1 — Press on object body (not a handle)

```
state: IDLE
target ← DERIVED.current.pointer_target    -- "alpha" in this example
condition:
    button_1_pressed AND target is not None
    AND pointer_handle_target is None

get_permission("START", [target, "pointer"])
  -- target not held → granted

emit_effect("persistent", "set-selection", { object_ids: [target] })

organism.held ← { object_id: target }
organism.data ← {
    press_point: { x: RAW.x, y: RAW.y },
    grab_offset: { x: RAW.x - world.objects[target].x,
                   y: RAW.y - world.objects[target].y }
}
organism.state ← "ARMED"
```

### Cycles 2–N — Below threshold

```
state: ARMED
condition: button_1_released is False AND drag_threshold_crossed is False
-- Wait.
```

Release before threshold:
```
condition: button_1_released is True
-- Treat as a click. Selection was already set.
clear(organism)
```

### Cycle N+1 — Threshold crossed

```
state: ARMED
condition: drag_threshold_crossed is True

get_permission("HOLD-RESOURCE", [organism.held.object_id, "pointer"])
  -- target not held by another organism → granted

organism.state ← "DRAGGING"
```

### Cycles N+2 … — Dragging

```
state: DRAGGING

target ← organism.held.object_id
grab   ← organism.data.grab_offset
x ← RAW.current.x - grab.x
y ← RAW.current.y - grab.y

emit_effect("volatile", "drag-preview", { object_id: target,
                                          x: x, y: y,
                                          pointer_x: RAW.current.x,
                                          pointer_y: RAW.current.y })
```

The object remains at its original position during the drag. The volatile effect signals the projection system to render a ghost at the computed destination each cycle.

### Final cycle — Release

```
condition: button_1_released is True

target ← organism.held.object_id
grab   ← organism.data.grab_offset
x ← RAW.current.x - grab.x
y ← RAW.current.y - grab.y

emit_effect("persistent", "move-object", { object_id: target, x: x, y: y })
clear(organism)
-- lease released; pointer and target resource freed
```

---

## Resize Organism Pipeline

Resize runs concurrently with drag (both organisms are always evaluated each cycle). The Judge prevents conflict.

### Cycle 1 — Press on a handle

```
state: IDLE
handle_target ← DERIVED.current.pointer_handle_target  -- e.g. { object_id: "alpha", handle: "se" }
condition:
    button_1_pressed
    AND handle_target is not None

target ← handle_target.object_id
handle ← handle_target.handle
obj    ← world.objects[target]

get_permission("START", [target, "pointer"])
  -- If drag-object already holds target: denied → clear, return.
  -- Otherwise: granted.

organism.held ← { object_id: target, handle: handle }
organism.data ← {
    press_point: { x: RAW.x, y: RAW.y },
    start_rect:  { x: obj.x, y: obj.y, w: obj.w, h: obj.h }
}
organism.state ← "ARMED"
```

### Threshold and HOLD-RESOURCE (same as drag):

```
get_permission("HOLD-RESOURCE", [organism.held.object_id, "pointer"])
  -- If drag-object holds the target: denied → clear.
  -- Otherwise: granted.

organism.state ← "DRAGGING"
```

### Dragging cycles:

```
emit_effect("persistent", "resize-object", {
    object_id:  organism.held.object_id,
    handle:     organism.held.handle,
    start_rect: organism.data.start_rect,
    pointer_x:  RAW.current.x,
    pointer_y:  RAW.current.y
})
```

Effect application computes the new rect from the handle, start_rect, and pointer position:

```
function apply_resize(payload):
    obj        ← world.objects[payload.object_id]
    start      ← payload.start_rect
    left, top  ← start.x, start.y
    right      ← start.x + start.w
    bottom     ← start.y + start.h

    if "w" in payload.handle:
        left  ← clamp(payload.pointer_x, MIN, right - MIN_SIZE)
    if "e" in payload.handle:
        right ← clamp(payload.pointer_x, left + MIN_SIZE, MAX)
    if "n" in payload.handle:
        top   ← clamp(payload.pointer_y, MIN, bottom - MIN_SIZE)
    if "s" in payload.handle:
        bottom ← clamp(payload.pointer_y, top + MIN_SIZE, MAX)

    obj.x ← left
    obj.y ← top
    obj.w ← right - left
    obj.h ← bottom - top
```

---

## Judge Interaction — Conflict Scenario

Suppose drag-object has just claimed `HOLD-RESOURCE` on `target` (it is in DRAGGING state). In the same cycle, resize-object attempts `START` on the same object:

```
get_permission("START", [target, "pointer"])
  -- resource_holds[target] == "drag-object" ≠ "resize-object"
  -- denied
  → clear(resize-object organism)
```

Resize cannot start while drag holds the object. The converse is also true: if resize holds `target`, drag is denied START.

---

## PROJECTION

### During drag:

```
"object:alpha:body"          → stays at original position
"object:alpha:label"         → stays with body
"overlay:drag-preview:alpha" → ghost of object rendered at computed destination;
                               coords update via canvas.coords() each cycle
```

### During resize:

```
"object:alpha:body"      → changes size each cycle
"object:alpha:handle:nw" → position changes as object resizes
"object:alpha:handle:ne" → position changes
"object:alpha:handle:sw" → position changes
"object:alpha:handle:se" → position changes (the one being dragged)
```

Reconcile calls `canvas.coords()` on each existing item whose position has changed. No items are created or deleted during the drag/resize; only coords and properties are updated.

---

## Key Invariants Demonstrated

- Resize handle hit-testing is a tokenizer responsibility (`pointer_handle_target`), not done by the resize organism itself.
- Two organisms compete for the same resource; the Judge resolves it with no application-specific logic.
- `apply_resize` in `route_effects()` does the geometry computation, not the organism. The organism names the intent; the effect application implements it.
- Projection updates existing canvas items in place rather than recreating them, enabling smooth animation.

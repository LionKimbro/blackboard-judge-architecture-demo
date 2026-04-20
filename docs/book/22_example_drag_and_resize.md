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
condition:
    button_1_pressed AND pointer_target == "alpha"
    AND pointer_handle_target is None
    AND "alpha" not in world.selection

get_permission("START", ["alpha"])
  -- "alpha" not held → granted

emit_effect("persistent", "set-selection", { object_ids: ["alpha"] })

organism.held ← { object_id: "alpha" }
organism.data ← {
    press_point: { x: RAW.x, y: RAW.y },
    grab_offset: { x: RAW.x - world.objects["alpha"].x,
                   y: RAW.y - world.objects["alpha"].y }
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

get_permission("HOLD-RESOURCE", ["alpha"])
  -- "alpha" not held by another organism → granted
  -- pointer_owner ← "drag-object", resource_holds["alpha"] ← "drag-object"

organism.state ← "DRAGGING"
```

### Cycles N+2 … — Dragging

```
state: DRAGGING

grab ← organism.data.grab_offset
x ← RAW.current.x - grab.x
y ← RAW.current.y - grab.y

emit_effect("persistent", "move-object", { object_id: "alpha", x: x, y: y })
emit_effect("volatile",   "drag-preview", { object_id: "alpha",
                                             pointer_x: RAW.current.x,
                                             pointer_y: RAW.current.y })
```

### Final cycle — Release

```
condition: button_1_released is True
clear(organism)
-- lease released; pointer_owner ← None; resource_holds["alpha"] removed
```

---

## Resize Organism Pipeline

Resize runs concurrently with drag (both organisms are always evaluated each cycle). The Judge prevents conflict.

### Cycle 1 — Press on a handle

```
state: IDLE
condition:
    button_1_pressed
    AND pointer_handle_target == { object_id: "alpha", handle: "se" }

get_permission("START", ["alpha"])
  -- If drag-object already holds "alpha": denied → clear, return.
  -- Otherwise: granted.

organism.held ← { object_id: "alpha", handle: "se" }
organism.data ← {
    press_point: { x: RAW.x, y: RAW.y },
    start_rect:  { x: obj.x, y: obj.y, w: obj.w, h: obj.h }
}
organism.state ← "ARMED"
```

### Threshold and HOLD-RESOURCE (same as drag):

```
get_permission("HOLD-RESOURCE", ["alpha"])
  -- If drag-object holds "alpha": denied → clear.
  -- Otherwise: granted.

organism.state ← "DRAGGING"
```

### Dragging cycles:

```
emit_effect("persistent", "resize-object", {
    object_id:  "alpha",
    handle:     "se",
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

Suppose drag-object has just claimed `HOLD-RESOURCE` on `"alpha"` (it is in DRAGGING state). In the same cycle, resize-object attempts `START` on `"alpha"`:

```
get_permission("START", ["alpha"])
  -- resource_holds["alpha"] == "drag-object" ≠ "resize-object"
  -- denied
  → clear(resize-object organism)
```

Resize cannot start while drag holds the object. The converse is also true: if resize holds `"alpha"`, drag is denied START.

---

## PROJECTION

### During drag:

```
"object:alpha:body"      → moves each cycle (coords update via canvas.coords())
"object:alpha:label"     → moves with body
"overlay:drag-preview:alpha" → line from pointer to object center
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

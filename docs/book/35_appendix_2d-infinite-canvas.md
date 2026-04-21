# 35 — Appendix: 2-D Infinite Canvas with Panning

## Overview

An infinite canvas allows objects to exist anywhere in an unbounded 2-D world space. The user pans the view by dragging, shifting the visible window over that space. This appendix describes how to extend the architecture to support panning: what changes in the world model, how coordinate conversion works across all layers, and how the pan organism fits into the pipeline alongside other gesture organisms.

Zoom (scale) is addressed briefly at the end. The core concepts are the same; panning alone is the minimal case.

---

## Two Coordinate Systems

Every point in a panned canvas exists in one of two spaces:

**World space** — the intrinsic coordinate system where objects live. An object at world position `(200, 150)` stays there regardless of where the user has panned.

**Screen space** — the coordinate system of the Tkinter Canvas widget. `(0, 0)` is always the top-left corner of the visible canvas area. RAW input (`RAW.current.x`, `RAW.current.y`) is always in screen space; Tk event coordinates are always in screen space.

The relationship between them is a simple translation defined by the viewport offset:

```
function world_to_screen(wx, wy):
    return wx + viewport.offset_x, wy + viewport.offset_y

function screen_to_world(sx, sy):
    return sx - viewport.offset_x, sy - viewport.offset_y
```

The viewport offset starts at `(0, 0)`. Panning right increases `offset_x`; panning down increases `offset_y`. Objects appear to move in the direction of the pan.

---

## Viewport in the World Model

The viewport is part of the world model:

```
world:
    objects   : { id → object }
    selection : [id]
    viewport  : { offset_x: float, offset_y: float }
```

It is durable persistent state — it survives across cycles and is mutated only via effects. It is not RAW (it doesn't come from input), not DERIVED (it isn't recomputed each cycle from RAW), and not a rendering artifact. It represents where the user is looking, which is a fact about the world.

The `pan-viewport` persistent effect mutates it:

```
function apply_pan_viewport(payload):
    world.viewport.offset_x += payload.dx
    world.viewport.offset_y += payload.dy
```

---

## Hit Testing

The hit-test tokenizer receives RAW screen coordinates and must test them against objects whose positions are stored in world coordinates. It converts each object's world position to screen before comparing:

```
function tokenizer_hit_test():
    sx ← RAW.current.x
    sy ← RAW.current.y

    for id, obj in world.objects (reverse draw order):
        screen_x, screen_y ← world_to_screen(obj.x, obj.y)
        if distance(sx, sy, screen_x, screen_y) <= HIT_RADIUS:
            DERIVED.current.pointer_target ← id
            return

    DERIVED.current.pointer_target ← None
```

The organism that reads `DERIVED.current.pointer_target` never sees coordinates — it sees an object id. The coordinate conversion is entirely the tokenizer's concern.

---

## Pan Organism Pipeline

Panning is a standard IDLE → ACTIVE gesture. It claims the `"pointer"` resource and a `"viewport"` resource so that no other gesture can compete with or be confused by a simultaneous pan.

### Trigger

The trigger condition is application-defined. Common choices:
- Middle mouse button drag (no modifier key needed)
- Shift + drag on empty space (as in the nodebrowser reference implementation)

The examples below use Shift + press on empty space.

### Cycle 1 — Press

```
state: IDLE
condition:
    button_1_pressed
    AND shift_down
    AND pointer_target is None

get_permission("CHECK", ["pointer", "viewport"])
  -- granted

organism.state ← "ACTIVE"
-- No data to record; delta is computed fresh each cycle from pointer_dx/pointer_dy.
```

No ARMED phase is needed: there is no ambiguity between a pan and a click. The intent is clear at press time. The organism goes directly to ACTIVE.

### Cycles 2–N — Dragging

```
state: ACTIVE
condition: button_1_released is False

dx ← DERIVED.current.pointer_dx    -- RAW.current.x - RAW.previous.x
dy ← DERIVED.current.pointer_dy    -- RAW.current.y - RAW.previous.y

if dx != 0 or dy != 0:
    emit_effect("persistent", "pan-viewport", { dx: dx, dy: dy })
```

The pan delta is consumed directly from `DERIVED.current.pointer_dx` / `pointer_dy` — the pointer-delta tokenizer's output. The organism never touches RAW coordinates.

No COMMIT call is needed for panning unless the application has a competing gesture that also claims `"viewport"`. In practice, viewport ownership is unique, so CHECK alone is sufficient to prevent double-panning.

### Final cycle — Release

```
state: ACTIVE
condition: button_1_released is True

clear(organism)
```

---

## Object Drag in a Panned World

Because the viewport transform is a pure translation (no scale), pointer motion in screen space equals motion in world space. The pan offset cancels out:

```
world_dx = screen_dx    -- true only when scale == 1
world_dy = screen_dy
```

A node drag organism computes its delta from pointer movement:

```
dx ← RAW.current.x - grab_offset.x - world.objects[target].x... 
```

Wait — the grab offset and the drag delta should both be computed in *world* space to be robust, especially if zoom is added later. The correct pattern:

```
-- At COMMIT time, record the grab offset in world space:
organism.data.grab_offset ← {
    x: screen_to_world(RAW.current.x, RAW.current.y).x - world.objects[target].x,
    y: screen_to_world(RAW.current.x, RAW.current.y).y - world.objects[target].y
}

-- Each dragging cycle:
world_x ← screen_to_world(RAW.current.x, RAW.current.y).x - organism.data.grab_offset.x
world_y ← screen_to_world(RAW.current.x, RAW.current.y).y - organism.data.grab_offset.y

emit_effect("persistent", "move-object", { object_id: target, x: world_x, y: world_y })
```

This correctly places the object at the world position under the pointer regardless of pan state. If the viewport moves mid-drag (e.g., auto-scroll), the object follows correctly.

---

## Object Creation

When an organism creates an object from a pointer position, it converts the click position to world coordinates before storing:

```
world_x, world_y ← screen_to_world(RAW.current.x, RAW.current.y)
emit_effect("persistent", "create-object", { x: world_x, y: world_y })
```

The object is stored at its world position. All subsequent hit-testing and projection use that position with the current viewport offset applied.

---

## Marquee Selection

The marquee drag rect is captured in screen coordinates (from RAW). When testing which objects fall inside it, convert each object's world position to screen before testing — or convert the rect corners to world before testing. Either works; screen-space comparison is simpler:

```
-- In the region-candidates tokenizer:
function tokenizer_region_candidates():
    rect ← DERIVED.current.drag_rect    -- screen-space rect from press point to pointer
    if rect is None:
        DERIVED.current.region_candidates ← []
        return

    candidates ← []
    for id, obj in world.objects:
        sx, sy ← world_to_screen(obj.x, obj.y)
        if rect.x1 <= sx <= rect.x2 and rect.y1 <= sy <= rect.y2:
            candidates.append(id)
    DERIVED.current.region_candidates ← candidates
```

This tokenizer re-runs every cycle, so the candidate set updates as the viewport changes (e.g., during an auto-scroll).

---

## Projection

Projection renders world objects to screen coordinates by applying `world_to_screen` to every position before passing coordinates to the canvas:

```
function add_object_items(desired, id, obj):
    sx, sy ← world_to_screen(obj.x, obj.y)
    desired["object:{id}:body"] ← {
        type: "oval",
        coords: [sx - RADIUS, sy - RADIUS, sx + RADIUS, sy + RADIUS],
        ...
    }
```

When the viewport changes, every canvas item's coordinates change. Reconcile calls `canvas.coords()` on each existing item to update positions in place — no items are created or destroyed by panning.

---

## Judge Resources

The pan organism should claim two resources:

- `"pointer"` — prevents any other pointer gesture from starting while panning
- `"viewport"` — prevents a second organism from also emitting `pan-viewport` effects in the same cycle

Registration order places the pan organism before drag and marquee organisms. This ensures that a Shift+drag-on-empty gesture is claimed by pan before drag organisms can CHECK.

---

## Extending to Zoom

If zoom is added, the world model gains a `scale` field:

```
world.viewport:
    offset_x : float
    offset_y : float
    scale    : float    -- default 1.0
```

The conversion functions become:

```
function world_to_screen(wx, wy):
    return wx * scale + offset_x, wy * scale + offset_y

function screen_to_world(sx, sy):
    return (sx - offset_x) / scale, (sy - offset_y) / scale
```

Zoom-to-point (keeping the pointer position fixed in world space as scale changes) requires adjusting the offset simultaneously:

```
function apply_zoom(pointer_sx, pointer_sy, new_scale):
    -- World point under pointer before zoom:
    wx ← (pointer_sx - viewport.offset_x) / viewport.scale
    wy ← (pointer_sy - viewport.offset_y) / viewport.scale

    viewport.scale ← new_scale

    -- Recompute offset so the same world point stays under pointer:
    viewport.offset_x ← pointer_sx - wx * new_scale
    viewport.offset_y ← pointer_sy - wy * new_scale
```

With zoom active, object drag must convert pointer delta to world delta:

```
world_dx ← screen_dx / viewport.scale
world_dy ← screen_dy / viewport.scale
```

The grab-offset pattern described above (using `screen_to_world` at grab time) handles this automatically.

---

## Viewport Stability Within a Cycle

The viewport is part of the world model and is therefore stable for the duration of a cycle. `pan-viewport` effects are queued; the offset does not change until `route_effects()` runs after all organisms have completed. Every organism in a given cycle calls `screen_to_world` against the same `offset_x` / `offset_y`. There is no risk of a pan organism's effect corrupting another organism's coordinate calculation in the same cycle.

---

## Key Invariants

- RAW is always in screen space. No layer changes this.
- World positions are stored in world space. No layer stores screen coordinates in the world model.
- `world_to_screen` and `screen_to_world` are the sole crossing points. They are pure functions of `viewport`.
- The tokenizer performs coordinate conversion for hit testing and spatial queries. Organisms receive object ids and world-space positions from DERIVED; they do not convert coordinates themselves.
- Panning mutates `world.viewport` via a persistent effect — the same mechanism as all other world model mutations.

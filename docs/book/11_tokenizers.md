# 11 — Tokenizers

## Purpose

Tokenizers translate raw input into interpreted perceptual facts. They are the only layer that performs this translation. All perceptual logic lives here and nowhere else.

---

## Protocol

```
tokenizer:
    name    : string
    active  : bool
    data    : dict      -- tokenizer-local persistent state (use sparingly)
    fn      : function

function run_tokenizers():
    DERIVED.current ← defaults()
    for each tokenizer in tokenizers:
        if tokenizer.active:
            tokenizer.fn(tokenizer.data)
```

### Rules

- A tokenizer reads `RAW.current`, `RAW.previous`, and `DERIVED.previous`.
- A tokenizer writes fields in `DERIVED.current`.
- A tokenizer does **not** emit effects.
- A tokenizer does **not** hold behavioral state (no FSM, no action memory).
- A tokenizer may hold minimal tracking state in `tokenizer.data` (e.g., press anchor for threshold detection). This state is purely perceptual bookkeeping.

---

## Canonical Tokenizers

### 1. Pointer Motion

Computes frame-to-frame pointer delta and movement state.

```
function tokenizer_pointer_motion(data):
    dx ← RAW.current.x - RAW.previous.x
    dy ← RAW.current.y - RAW.previous.y
    moving ← (dx != 0) or (dy != 0)

    DERIVED.current.dx ← dx
    DERIVED.current.dy ← dy
    DERIVED.current.moving ← moving

    if moving:
        data.last_motion_ms ← RAW.current.time_ms
        DERIVED.current.motionless_duration_ms ← 0
    else:
        last ← data.get("last_motion_ms", RAW.current.time_ms)
        DERIVED.current.motionless_duration_ms ← max(0, RAW.current.time_ms - last)
```

---

### 2. Button State (Edge Detection)

Produces single-frame pressed and released signals from the raw button state.

```
function tokenizer_button_1(data):
    was_down ← RAW.previous.button_1_down
    is_down  ← RAW.current.button_1_down

    DERIVED.current.button_1_pressed  ← is_down and not was_down
    DERIVED.current.button_1_released ← was_down and not is_down
```

---

### 3. Hit-Testing

Determines which object (if any) is under the pointer, and detects enter/leave transitions.

```
function tokenizer_hit_test(data):
    current_target ← find_topmost_object_at(RAW.current.x, RAW.current.y)
    previous_target ← DERIVED.previous.pointer_target

    DERIVED.current.pointer_target ← current_target

    if current_target != previous_target:
        DERIVED.current.entered_target ← current_target
        DERIVED.current.left_target    ← previous_target
    else:
        DERIVED.current.entered_target ← None
        DERIVED.current.left_target    ← None
```

`find_topmost_object_at` queries the world model for spatial containment. It returns an object id or None.

---

### 4. Drag Threshold

Produces a stable `drag_threshold_crossed` signal once the pointer moves far enough from the press point.

```
DRAG_THRESHOLD ← 8  -- pixels

function tokenizer_drag_threshold(data):
    if DERIVED.current.button_1_pressed:
        data.press_point ← { x: RAW.current.x, y: RAW.current.y }
        data.crossed ← False

    if DERIVED.current.button_1_released:
        data.press_point ← None
        data.crossed ← False
        DERIVED.current.drag_threshold_crossed ← False
        return

    if data.press_point is None or not RAW.current.button_1_down:
        DERIVED.current.drag_threshold_crossed ← False
        return

    dx ← RAW.current.x - data.press_point.x
    dy ← RAW.current.y - data.press_point.y
    data.crossed ← (dx*dx + dy*dy) >= (DRAG_THRESHOLD * DRAG_THRESHOLD)
    DERIVED.current.drag_threshold_crossed ← data.crossed
```

Once `crossed` becomes True it remains True until the button is released. This prevents threshold jitter.

---

### 5. Region / Marquee Candidates

Computes the set of objects whose bounds intersect a given rectangle. Used during marquee selection.

```
function tokenizer_region_candidates(data):
    -- Only meaningful when a drag rect exists.
    -- This tokenizer is typically driven by organism-supplied context,
    -- or computed inline in the marquee organism.
    -- When implemented as a tokenizer, it reads DERIVED.current.drag_rect
    -- (written by drag-threshold tokenizer) and writes candidate_ids.

    rect ← DERIVED.current.drag_rect
    if rect is None:
        DERIVED.current.region_candidates ← []
        return

    DERIVED.current.region_candidates ← [
        id for id, obj in world.objects
        if rect_intersects(rect, obj)
    ]
```

---

### 6. Selection Candidates (application-specific example)

Produces the subset of currently-selected objects that are under the pointer, used to decide group drag vs. single drag.

```
function tokenizer_selection_candidates(data):
    target ← DERIVED.current.pointer_target
    if target is None:
        DERIVED.current.pointer_on_selected ← False
        return
    DERIVED.current.pointer_on_selected ← (target in world.selection)
```

---

## Tokenizer Ordering

Tokenizers run in registration order. Dependencies must be respected:

- `button_1` must run before `drag_threshold` (threshold reads `button_1_pressed`).
- `hit_test` must run before any tokenizer that reads `pointer_target`.
- `drag_threshold` may run before or after `hit_test`; they are independent.

---

## What Tokenizers Must Not Do

- Call `emit_effect()`.
- Change organism state.
- Access `coordination` (the judge's resource table).
- Encode application behavior (e.g., "if hovering over a selected object, do X").

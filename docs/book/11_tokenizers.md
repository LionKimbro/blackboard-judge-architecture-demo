# 11 — Tokenizers

## Purpose

Tokenizers compute perceptual facts from RAW and the world model. They are the only layer that performs this translation. All perceptual logic lives here and nowhere else.

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

- A tokenizer reads `RAW.current`, `RAW.previous`, `DERIVED.previous`, and the world model.
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

## 7. Click and Temporal Pattern Detection

Tokenizers may recognize temporal patterns in input, including click, double-click, long press, and more complex sequences. These are perceptual classifications, not behavioral decisions.

### Principles

- Temporal patterns are computed from `RAW.current`, `RAW.previous`, `DERIVED.previous`, and tokenizer-local timing state.
- Tokenizers must not delay or suppress events to resolve ambiguity.
- Multiple overlapping patterns may be true within the same frame.
- Interpretation of overlapping patterns (e.g., suppressing single-click in favor of double-click) is the responsibility of organisms.

---

### Canonical Click Tokenizer

Detects a short press-release interaction.

```
CLICK_MAX_DURATION_MS ← 150

function tokenizer_click(data):
    DERIVED.current.single_click ← False

    if DERIVED.current.button_1_pressed:
        data.press_time   ← RAW.current.time_ms
        data.press_target ← DERIVED.current.pointer_target
        data.press_pos    ← { x: RAW.current.x, y: RAW.current.y }

    if DERIVED.current.button_1_released and data.press_time is not None:
        duration ← RAW.current.time_ms - data.press_time
        if duration <= CLICK_MAX_DURATION_MS:
            DERIVED.current.single_click    ← True
            DERIVED.current.click_target    ← data.press_target
            DERIVED.current.click_position  ← data.press_pos
        data.press_time   ← None
        data.press_target ← None
```

---

### Canonical Double-Click Tokenizer

Detects two clicks close in time and space. Depends on `single_click` from the click tokenizer; must run after it.

```
DOUBLE_CLICK_MS      ← 300
CLICK_TOLERANCE_PX   ← 6

function tokenizer_double_click(data):
    DERIVED.current.double_click ← False

    if not DERIVED.current.single_click:
        return

    now            ← RAW.current.time_ms
    last_time      ← data.get("last_click_time")
    last_pos       ← data.get("last_click_pos")
    last_target    ← data.get("last_click_target")
    current_pos    ← DERIVED.current.click_position
    current_target ← DERIVED.current.click_target

    if last_time is not None:
        dt ← now - last_time
        dx ← current_pos.x - last_pos.x
        dy ← current_pos.y - last_pos.y
        close_enough ← (dx*dx + dy*dy) <= (CLICK_TOLERANCE_PX * CLICK_TOLERANCE_PX)
        if dt <= DOUBLE_CLICK_MS and close_enough and current_target == last_target:
            DERIVED.current.double_click ← True
            data.last_click_time ← None
            return

    data.last_click_time   ← now
    data.last_click_pos    ← current_pos
    data.last_click_target ← current_target
```

---

### Long Press

Detects a press held beyond a time threshold.

```
LONG_PRESS_MS ← 500

function tokenizer_long_press(data):
    DERIVED.current.long_press ← False

    if DERIVED.current.button_1_pressed:
        data.press_time ← RAW.current.time_ms

    if RAW.current.button_1_down and data.press_time is not None:
        if RAW.current.time_ms - data.press_time >= LONG_PRESS_MS:
            DERIVED.current.long_press ← True

    if DERIVED.current.button_1_released:
        data.press_time ← None
```

---

### Notes on Overlapping Patterns

Temporal patterns are not mutually exclusive. A `single_click` may be followed by a `double_click`. A `long_press` may overlap with drag initiation. Tokenizers report what is true; organisms decide what to act on.

---

## Extension: Complex Input Languages

The tokenizer layer may be extended to recognize richer temporal or combinatorial input patterns, including:

- Key chords (multi-key combinations held simultaneously)
- Tap sequences (e.g., timed multi-tap patterns)
- Gesture sequences (e.g., hold → tap → release)
- Keyset input (e.g., Engelbart-style multi-finger chords on A, S, D, F, Space)
- Multi-button or multi-pointer interactions

These belong in the tokenizer layer as long as they classify input patterns, do not encode application behavior, and produce inspectable facts in `DERIVED`. The complexity of the pattern recognition is not a disqualifier — the criterion is purely whether the output is a perceptual fact or a behavioral decision.

---

## What Tokenizers Must Not Do

- Call `emit_effect()`.
- Change organism state.
- Access `coordination` (the judge's resource table).
- Encode application behavior (e.g., "if hovering over a selected object, do X").

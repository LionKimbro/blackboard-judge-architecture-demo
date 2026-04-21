# 20 — Example: Marquee Selection

## Overview

The user presses on empty space and drags to draw a selection rectangle. Objects intersecting the rectangle are highlighted as candidates during the drag. On release, they become the selection.

---

## Pipeline Trace

### RAW (each cycle)

```
RAW.current:
    x, y            -- pointer position
    button_1_down   -- True while dragging
    time_ms
    inside_canvas   -- True

RAW.previous:
    [prior cycle snapshot]
```

---

### DERIVED — Tokenizers Used

**button-state tokenizer:**
```
DERIVED.current.button_1_pressed  ← True   (first cycle: press)
DERIVED.current.button_1_released ← True   (final cycle: release)
```

**hit-test tokenizer:**
```
DERIVED.current.pointer_target ← None   (pointer is on empty space)
```

**drag-threshold tokenizer:**
```
-- After press:
DERIVED.current.drag_threshold_crossed ← False

-- After pointer moves far enough:
DERIVED.current.drag_threshold_crossed ← True   (and stays True until release)
```

**region-candidates tokenizer:**
```
-- Each cycle while a drag rect exists:
DERIVED.current.region_candidates ← [ids of objects intersecting the current drag rect]

-- When no drag rect:
DERIVED.current.region_candidates ← []
```

---

### ORGANISMS

**marquee-select organism** is the only organism that acts here.

#### Cycle 1 — Press on empty space

```
state: IDLE
condition: button_1_pressed AND pointer_target is None

get_permission("START", ["pointer"])
  -- pointer_owner is None → granted

organism.data ← { press_point: { x: RAW.x, y: RAW.y } }
organism.state ← "ARMED"
```

#### Cycles 2–N — Held, below threshold

```
state: ARMED
condition: button_1_released is False AND drag_threshold_crossed is False

-- Wait. No effects emitted.
```

#### Cycle N+1 — Threshold crossed

```
state: ARMED
condition: drag_threshold_crossed is True

organism.state ← "SELECTING"
-- No HOLD-RESOURCE needed; "pointer" was acquired at START.
```

#### Cycles N+2 … — Dragging

```
state: SELECTING

hits ← DERIVED.current.region_candidates

emit_effect("volatile", "show-marquee", { rect: DERIVED.current.drag_rect, candidate_ids: hits })

-- world model unchanged this cycle
```

#### Final cycle — Release

```
state: SELECTING
condition: button_1_released is True

hits ← DERIVED.current.region_candidates

emit_effect("volatile", "show-marquee", { rect: DERIVED.current.drag_rect, candidate_ids: hits })
emit_effect("persistent", "set-selection", { object_ids: hits })

clear(organism)
-- organism.state ← IDLE, lease released
```

---

### EFFECTS

Volatile (each dragging cycle):
```
{ kind: "volatile", name: "show-marquee",
  payload: { rect: {x1,y1,x2,y2}, candidate_ids: ["alpha", "bravo"] } }
```

Persistent (on release):
```
{ kind: "persistent", name: "set-selection",
  payload: { object_ids: ["alpha", "bravo"] } }
```

---

### WORLD MODEL

Before: `world.selection = []`

After `route_effects()` applies the persistent effect:
`world.selection = ["alpha", "bravo"]`

The world model is unchanged during the dragging cycles; only volatile effects are emitted.

---

### PROJECTION

#### During drag (each cycle):

`compute_desired_state` includes:

```
"object:alpha:body"  → rect with unselected outline
"object:bravo:body"  → rect with unselected outline
"object:charlie:body" → rect with unselected outline
"overlay:marquee"    → dashed rectangle from press_point to current pointer
```

If candidates are highlighted visually, the desired state adds:
```
"overlay:candidate:alpha"  → highlighted border around alpha
"overlay:candidate:bravo"  → highlighted border around bravo
```

`reconcile()` updates `"overlay:marquee"` coords each cycle (pointer is moving). The candidate overlays are created when they appear and deleted when objects leave the rect.

#### On release:

`world.selection` now contains `["alpha", "bravo"]`.

`compute_desired_state` includes:
```
"object:alpha:body"  → rect with selected outline
"object:bravo:body"  → rect with selected outline
"object:charlie:body" → rect with unselected outline
```

`"overlay:marquee"` is absent from desired → reconcile deletes the canvas item.

---

## Key Invariants Demonstrated

- Region intersection (`region_candidates`) is computed by the region-candidates tokenizer, not by the organism. The organism reads `DERIVED.current.region_candidates` — it performs no spatial reasoning itself.
- The world model is not modified until release.
- The marquee rectangle is a volatile effect; it vanishes automatically next cycle unless re-emitted.
- The organism does not touch the canvas directly.

# 30 — Failure Modes

## Overview

These are the five canonical violations of the architecture. Each one erodes a layer boundary and produces a system that is increasingly difficult to reason about, test, and extend.

---

## 1. Tokenizers Containing Behavior

**Description:** A tokenizer encodes application-specific behavior, makes decisions, or encapsulates logic that only makes sense in the context of a specific gesture.

**Example:**
```
function tokenizer_hover(data):
    target ← find_topmost_object_at(RAW.current.x, RAW.current.y)
    DERIVED.current.pointer_target ← target

    -- VIOLATION: behavior inside tokenizer
    if target is not None and not RAW.current.button_1_down:
        emit_effect("volatile", "hover-highlight", { object_id: target })
```

**Why this is wrong:** The decision to emit a hover highlight depends on application context — whether the pointer is free, whether any other gesture is active, whether the object is of a type that should highlight. These are behavioral concerns that belong in an organism. The tokenizer cannot consult the Judge, cannot respect resource ownership, and cannot be disabled selectively.

**Symptom:** Hover highlights appear even when a drag is in progress. Removing the hover effect requires modifying the tokenizer, which changes perception for every consumer.

**Correct form:** Tokenizer writes `DERIVED.current.pointer_target`. A separate hover-highlight organism reads it and, after consulting the Judge, emits the volatile effect.

---

## 2. Organisms Redefining Perception

**Description:** An organism performs hit-testing, spatial queries, or temporal edge detection that duplicates or contradicts what tokenizers produce.

**Example:**
```
function handle_drag_idle(organism):
    -- VIOLATION: organism performs its own hit-test
    x, y ← RAW.current.x, RAW.current.y
    for id, obj in world.objects:
        if obj.x <= x <= obj.x + obj.w and obj.y <= y <= obj.y + obj.h:
            target ← id
            break
    else:
        return
    ...
```

**Why this is wrong:** Now there are two hit-test implementations. They may disagree (e.g., different iteration order, different boundary conditions). When the hit-test logic needs to change — for z-order, for invisible objects, for hit-slop — it must be changed in multiple places. The tokenizer's output becomes redundant and untrusted.

**Symptom:** Organisms disagree with each other about what is under the pointer. Fixing one requires finding and updating all private hit-test copies.

**Correct form:** The organism reads `DERIVED.current.pointer_target` produced by the hit-test tokenizer.

---

## 3. Organisms Encoding Coordination Logic

**Description:** An organism encodes priority or yielding rules relative to other organisms — checking conditions that have no bearing on whether the organism is applicable, but instead encode assumptions about what other organisms are doing or should win.

**Example:**
```
function handle_drag_idle(organism):
    target ← DERIVED.current.pointer_target
    if target is None:
        return

    -- VIOLATION: organism encodes priority logic about group-drag
    if target in world.selection:
        return   -- "let group-drag handle it"

    get_permission("CHECK", [target, "pointer"])
    ...
```

**Why this is wrong:** The organism is now making a decision that belongs to the Judge: "group-drag should take precedence when the target is selected." This hides coordination policy inside an organism, creates invisible coupling between organisms, and makes both harder to reuse. If the priority rule changes, the organism must change — even though it is otherwise unaffected. If a new organism is added, all existing organisms that might yield to it must be updated.

**Symptom:** Removing or reordering organisms changes behavior in ways that are hard to trace. Organisms contain conditions that only make sense in relation to other organisms. Priority bugs are found scattered across organism handlers rather than in one place.

**Correct form:** An organism determines applicability from `RAW` and `DERIVED` only — the perceptual facts about what is happening in the world. All conflict resolution is the Judge's responsibility, expressed through resource contention and registration order (or an explicit bid policy). No organism contains the phrase "let X handle it."

When the Judge feels too complex, the answer is to refine the coordination model — resource granularity, request types, phases, bid policy — not to push priority logic into organisms. Organisms remain reusable and unaware of each other; the Judge gets better tools.

**Note on the Judge's role:** The Judge *does* own conflict-resolution policy. Resource rules, registration order, and bid-based priority are all legitimate Judge concerns. The Judge may also consult `RAW` or `DERIVED` — for example, using `shift_down` or `pointer_target` to inform a priority decision — provided that policy remains centralized and organisms remain unaware of each other. What the Judge must not do is depend on organism names or embed per-gesture special cases: rules of the form "if the requesting organism is drag-object and the target is selected, deny" couple the Judge to specific organism identities and make the policy opaque. Prefer resource granularity, registration order, and bids over modifier-key or name-based branching in the Judge. When the Judge does read RAW/DERIVED, it should be for general policy (e.g., a global mode flag), not for gesture-specific routing.

---

## 4. Projection Mutating the World Model

**Description:** The projection system writes back to the world model — for example, to record visual state, to clamp positions for display purposes, or to store rendering artifacts.

**Example:**
```
function compute_desired_state(world, volatile_effects):
    for id, obj in world.objects:
        -- VIOLATION: clamping in projection writes to world model
        obj.x ← clamp(obj.x, 0, CANVAS_W)
        obj.y ← clamp(obj.y, 0, CANVAS_H)
        desired["object:{id}:body"] ← ...
```

**Why this is wrong:** The world model is now modified by rendering. Object positions change as a side effect of drawing. If the projection runs multiple times (e.g., for resize), positions are clamped multiple times. The world model is no longer a reliable record of what organisms set. Undo/redo and serialization capture a corrupted state.

**Symptom:** Object positions drift over time. Saving and loading produces different results than the live canvas. Clamping that should be a display concern instead becomes durable state.

**Correct form:** Clamping belongs in `route_effects()` when applying persistent effects. The projection system reads positions and renders them as-is.

---

## 5. Duplication of Perceptual Logic

**Description:** The same perceptual computation — drag threshold, hover, hit-testing — appears in multiple places: in a tokenizer, in an organism's idle handler, and in a projection helper.

**Example:**
```
-- In tokenizer:
DERIVED.current.drag_threshold_crossed ← dist >= DRAG_THRESHOLD

-- In organism_drag_object:
dx ← RAW.current.x - organism.data.press_point.x
dy ← RAW.current.y - organism.data.press_point.y
if sqrt(dx*dx + dy*dy) >= DRAG_THRESHOLD:   -- VIOLATION: duplicated
    ...

-- In projection:
if sqrt(...) >= DRAG_THRESHOLD:             -- VIOLATION: again
    draw_drag_indicator(...)
```

**Why this is wrong:** The threshold value must be changed in three places. The implementations may use different metrics (Euclidean vs. Chebyshev). The meaning of "drag has started" is now fragmented. If the tokenizer is disabled (e.g., for testing), the organism and projection still have their own copies.

**Symptom:** Behavior differs subtly between organisms. Changing the drag threshold requires a search-and-replace across the codebase. Some organisms respond at a different threshold than others.

**Correct form:** The tokenizer is the single source for `drag_threshold_crossed`. All consumers read that one field.

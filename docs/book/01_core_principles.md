# 01 — Core Principles

## The Five Invariants

These invariants are non-negotiable. Violations produce systems that are difficult to debug, extend, or reason about.

---

### 1. Tokenizers define all perception

Tokenizers are the only place where raw input is interpreted into perceptual meaning. No other layer may perform hit-testing, edge detection, spatial reasoning, or temporal pattern recognition.

**Correct:** An organism reads `DERIVED["drag-threshold-crossed"]` to know whether a drag has started.  
**Correct:** An organism reads `RAW["x"]` and `RAW["y"]` to compute a new object position during a drag.  
**Violation:** An organism computes distance from the press point itself to decide whether a drag has started.

---

### 2. Organisms emit only effects

An organism's sole output is a set of effects appended to the effect queue. It does not directly modify the world model, the canvas, or any shared state.

**Correct:** An organism calls `emit_effect("move-node", {...})`.  
**Violation:** An organism writes `world["objects"]["alpha"]["x"] = 100`.

---

### 3. The world model is mutated only via persistent effects

No layer other than the effect router may write to the world model. This includes tokenizers, organisms, the judge, and the projection system.

**Correct:** `route_effects()` applies a `"move-object"` effect to the world model.  
**Violation:** The projection system adjusts a position for rendering and leaves it in world state.

---

### 4. The Judge contains no behavior logic

The Judge tracks who owns what. It does not interpret gestures, understand sequences of events, or encode application rules. Its decisions are based solely on the current resource ownership table.

**Correct:** Judge grants `START` if the pointer is unowned.  
**Violation:** Judge checks whether the press point was inside a selection to decide who wins.

---

### 5. Projection performs reconciliation, not immediate drawing

The projection system computes a complete desired visual state, compares it to the current canvas state, and applies only the necessary operations. It does not issue canvas commands in response to events directly.

**Correct:** Projection diffs desired vs. current canvas state and issues targeted create/update/delete.  
**Violation:** An organism calls `canvas.create_rectangle(...)` directly.

---

## Separation of Concerns

```
Perception   →  Tokenizers
Behavior     →  Organisms
Coordination →  Judge
State        →  World Model
Rendering    →  Projection
```

Each domain has exactly one responsible layer. When a concern appears in the wrong layer, it creates a dependency that erodes the architecture.

---

## Why This Matters

Complex canvas applications accumulate interaction behaviors over time. Without explicit boundaries, behaviors bleed into each other. A hover effect starts checking button state. A drag handler tests hit geometry. Selection logic starts living in the renderer.

This architecture makes the system legible at each layer independently:

- Tokenizers can be read without knowing any behaviors.
- Organisms can be read without knowing how the canvas works.
- The projection system can be read without knowing what triggered the current frame.

---

## Cycle Discipline

Every architectural layer runs once per cycle, in order:

```
tokenizers → judge → organisms → route_effects → projection
```

No layer runs more than once. No layer calls into another layer out of order. No layer inspects the output of a later layer.

The judge is consulted *by organisms during their run*, not as a separate phase before or after. Organisms call `get_permission()` as part of their own logic.

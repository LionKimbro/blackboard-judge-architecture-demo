# 21 — Example: Node Linking

## Overview

The user holds a modifier key (Shift), presses on a source node, and drags to a target node. On release over a valid target, an edge is created. A preview edge follows the pointer during the drag. If the edge already exists, it is deleted instead (toggle behavior).

---

## Pipeline Trace

### RAW (each cycle)

```
RAW.current:
    x, y            -- pointer position
    button_1_down   -- True while dragging
    shift_down      -- True throughout this gesture
    time_ms
    inside_canvas   -- True

RAW.previous:
    [prior cycle snapshot]
```

---

### DERIVED — Tokenizers Used

**button-state tokenizer:**
```
DERIVED.current.button_1_pressed  ← True   (first cycle)
DERIVED.current.button_1_released ← True   (final cycle)
```

**hit-test tokenizer:**
```
DERIVED.current.pointer_target ← "node-A"   (source node, on press)
DERIVED.current.pointer_target ← "node-B"   (target node, during final drag)
DERIVED.current.pointer_target ← None        (mid-drag, over empty space)
```

**drag-threshold tokenizer:**
```
DERIVED.current.drag_threshold_crossed ← True   (after pointer moves)
```

---

### ORGANISMS

**edge-create organism** is the acting organism.

Other organisms (node-drag, group-drag, marquee-select) are also present. Their START requests will be denied once edge-create claims the pointer.

#### Cycle 1 — Shift + Press on node-A

```
state: IDLE
condition:
    RAW.shift_down is True
    AND button_1_pressed is True
    AND pointer_target == "node-A"  (not None)

get_permission("START", ["pointer", "edge-create"])
  -- pointer_owner is None → granted

organism.data ← { source_id: "node-A" }
organism.state ← "ARMED"
```

#### Cycles 2–N — Below threshold

```
state: ARMED
condition: drag_threshold_crossed is False

-- No effects. Waiting.
```

#### Cycle N+1 — Threshold crossed

```
state: ARMED
condition: drag_threshold_crossed is True

get_permission("HOLD-RESOURCE", ["pointer", "edge-create"])
  -- granted; pointer locked to edge-create organism

organism.state ← "ACTIVE"
```

#### Cycles N+2 … — Dragging

```
state: ACTIVE

source_id ← organism.data.source_id
target_id ← DERIVED.current.pointer_target   -- None or a node id

will_create ← (target_id is not None
               AND target_id != source_id
               AND not has_edge(source_id, target_id))
will_delete ← (target_id is not None
               AND target_id != source_id
               AND has_edge(source_id, target_id))

preview_color ←
    if will_create: "#6dff8a"
    elif will_delete: "#ff6b6b"
    else: "#7fdfff"

emit_effect("volatile", "edge-preview", {
    from_id:    source_id,
    to_x:       RAW.current.x,
    to_y:       RAW.current.y,
    color:      preview_color
})
```

#### Final cycle — Release

```
state: ACTIVE
condition: button_1_released is True

target_id ← DERIVED.current.pointer_target

if target_id is not None AND target_id != source_id:
    if has_edge(source_id, target_id):
        emit_effect("persistent", "delete-edge", { from_id: source_id, to_id: target_id })
    else:
        emit_effect("persistent", "create-edge", { from_id: source_id, to_id: target_id })

clear(organism)
```

---

### EFFECTS

Volatile (each active drag cycle):
```
{ kind: "volatile", name: "edge-preview",
  payload: { from_id: "node-A", to_x: 340, to_y: 220, color: "#6dff8a" } }
```

Persistent (on release, if valid target):
```
{ kind: "persistent", name: "create-edge",
  payload: { from_id: "node-A", to_id: "node-B" } }
```

or:
```
{ kind: "persistent", name: "delete-edge",
  payload: { from_id: "node-A", to_id: "node-B" } }
```

---

### WORLD MODEL

Before: `world.edges = [{ from: "node-A", to: "node-C" }]`

After `route_effects()`:
`world.edges = [{ from: "node-A", to: "node-C" }, { from: "node-A", to: "node-B" }]`

---

### PROJECTION

#### During drag:

`compute_desired_state` includes:

```
"node:node-A:body"      → circle at node-A's position
"node:node-B:body"      → circle at node-B's position
"edge:node-A:node-C"    → bezier line from node-A to node-C

"overlay:edge-preview"  → bezier preview line from node-A to pointer position,
                           color = will_create/will_delete/neutral
```

The preview line is redrawn each cycle as the pointer moves. `reconcile()` calls `canvas.coords()` and `canvas.itemconfig()` on the existing item rather than deleting and recreating it.

#### On release (edge created):

`"edge:node-A:node-B"` appears in desired → created by reconcile.  
`"overlay:edge-preview"` absent from desired → deleted by reconcile.

---

## Interaction With Other Organisms

When the pointer is over a node with Shift held, `node-drag` and `group-drag` organisms see their START requests denied because `edge-create` already holds the pointer. This is implicit priority by organism order: `edge-create` must be registered before `node-drag` and `group-drag`.

If `edge-create` is registered after them, it would need to check Shift state and deny itself, or the other organisms would need to check Shift and yield. The cleanest design: `edge-create` appears first and claims the pointer on Shift+press-on-node; later organisms see the pointer as owned and do not attempt to start.

---

## Key Invariants Demonstrated

- Color logic (will-create vs. will-delete) lives in the organism, not the tokenizer. It is behavioral reasoning, not perception.
- `has_edge()` is a world model query, called by the organism each cycle.
- The preview edge is a volatile effect; it does not survive to the next cycle unless re-emitted.
- The world model is not modified until release.

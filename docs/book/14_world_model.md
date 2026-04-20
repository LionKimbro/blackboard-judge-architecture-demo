# 14 — World Model

## Purpose

The world model is the authoritative persistent state of the application. It contains the objects, relationships, and selection state that survive across interaction cycles. It is the ground truth that the projection system renders.

---

## Constraints

- The world model is **read** by organisms (to make decisions) and by the projection system (to compute desired visual state).
- The world model is **written** only by `route_effects()`, which applies persistent effects.
- No other layer — not tokenizers, not organisms directly, not the projection system — may modify the world model.
- Effects are applied in the order they were emitted during the cycle.
- Within a cycle, the world model is stable from the perspective of organisms and tokenizers. Mutations occur only after all organisms have run, during `route_effects()`.

---

## Minimal Structure

The architecture does not prescribe world model contents. Each application defines its own. A typical canvas application uses:

```
world:
    objects     : { id → object }
    selection   : [id, ...]         -- currently selected object ids
    [application-specific fields]

object:
    id      : string
    x       : number                -- position
    y       : number
    w       : number                -- size (for rect-shaped objects)
    h       : number
    [application-specific fields]
```

Graph applications use:

```
world:
    nodes   : { id → node }
    edges   : [{ from: id, to: id }, ...]
    selection : { single: id | None, group: [id, ...] }

node:
    id  : string
    x   : number
    y   : number
    [label, color, etc.]
```

---

## Effect Application

`route_effects()` iterates the effect queue and applies persistent effects to the world model:

```
function route_effects(effects):
    for effect in effects:
        if effect.kind == "persistent":
            apply_persistent_effect(effect)
        -- volatile effects are left for projection to consume


function apply_persistent_effect(effect):
    if effect.name == "move-object":
        obj ← world.objects[effect.payload.object_id]
        obj.x ← effect.payload.x
        obj.y ← effect.payload.y

    elif effect.name == "resize-object":
        apply_resize(effect.payload)

    elif effect.name == "set-selection":
        world.selection ← list(effect.payload.object_ids)

    elif effect.name == "move-group":
        apply_group_move(effect.payload)

    elif effect.name == "create-node":
        id ← effect.payload.id or generate_id()
        world.nodes[id] ← { id: id, x: effect.payload.x, y: effect.payload.y }

    elif effect.name == "delete-nodes":
        for id in effect.payload.object_ids:
            world.nodes.pop(id)
        world.edges ← [e for e in world.edges
                        if e.from not in deleted and e.to not in deleted]

    elif effect.name == "create-edge":
        world.edges.append({ from: effect.payload.from_id,
                              to:   effect.payload.to_id })

    elif effect.name == "delete-edge":
        world.edges ← [e for e in world.edges
                        if not (e.from == payload.from_id and e.to == payload.to_id)]
```

---

## Organisms Reading the World Model

Organisms may read the world model to make decisions. Examples:

- Checking whether a resource (object id) still exists before claiming it.
- Reading selection state to decide which objects to include in a group drag.
- Reading object geometry to compute grab offsets.

Organisms must treat world model reads as advisory. The world model may change between cycles. An organism should not cache world model values across cycles; re-read each cycle.

---

## The Canvas Is Not the World Model

The canvas is a projection of the world model, not part of it. It is a rendering artifact produced each cycle from world state and volatile effects.

Tokenizers may use canvas queries (e.g., `canvas.find_closest()`, `canvas.find_overlapping()`) as an implementation convenience for hit-testing. This is acceptable, but such queries are indirect: the canvas was constructed from the world model, so its geometry is derivative of world state, not independent of it. When the two disagree — for example, if the canvas has not yet been reconciled after a world mutation — the world model is authoritative.

Prefer world model geometry queries where they are straightforward. Reserve canvas queries for cases where the canvas provides something the world model does not, such as pixel-accurate hit-testing on complex or curved shapes.

---

## Derived State

Some values that appear to be "world state" are better computed fresh from the world model each cycle rather than stored. For example:

- "Objects intersecting the marquee rect" — computed by `objects_in_rect()` each cycle; not stored.
- "Objects in selection that are visible" — computed each cycle during projection.

Store in the world model only what must survive across cycles and cannot be derived from other world model fields. If a value can be recomputed cheaply and deterministically from world state and RAW, it should not be stored — compute it fresh each cycle instead.

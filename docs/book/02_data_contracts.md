# 02 — Data Contracts

## Purpose

This file defines the data structures passed between layers. Every field listed here is a contract: producers must write it, consumers must read only what they are permitted to read.

---

## RAW

Populated once per cycle before tokenizers run. Always contains both `current` and `previous`.

```
RAW.current:
    x                   : number    -- pointer x in canvas coordinates
    y                   : number    -- pointer y in canvas coordinates
    time_ms             : number    -- monotonic millisecond clock
    inside_canvas       : bool      -- pointer is within the canvas bounds
    button_1_down       : bool      -- primary mouse button is held
    [application fields, e.g. key states, modifier states]

RAW.previous:
    [same fields as RAW.current, frozen from prior cycle]
```

RAW is read-only to all layers except the cycle runner that populates it.

---

## DERIVED

Produced by tokenizers. Reset to defaults at the start of each tokenizer pass. Each tokenizer writes only its own fields.

```
DERIVED.current:
    -- from pointer-motion tokenizer
    dx                      : number    -- RAW.current.x - RAW.previous.x
    dy                      : number    -- RAW.current.y - RAW.previous.y
    moving                  : bool      -- dx != 0 or dy != 0
    motionless_duration_ms  : number    -- ms since last movement

    -- from button-state tokenizer
    button_1_pressed        : bool      -- button went down this cycle
    button_1_released       : bool      -- button went up this cycle

    -- from hit-test tokenizer
    pointer_target          : id | None -- topmost object under pointer
    entered_target          : id | None -- object pointer just entered
    left_target             : id | None -- object pointer just left

    -- from drag-threshold tokenizer
    drag_threshold_crossed  : bool      -- pointer moved past threshold since press

    -- from resize-handle tokenizer (application-specific example)
    pointer_handle_target   : {object_id, handle_name} | None

DERIVED.previous:
    [same fields, frozen from prior cycle]
```

DERIVED is read-only to organisms. Tokenizers write DERIVED; organisms only read it.

---

## EFFECTS

The effect queue is populated by organisms during their run and consumed by `route_effects()`. It is cleared at the start of each organism evaluation pass.

Each effect is a record:

```
effect:
    kind    : "persistent" | "volatile"
    source  : organism_name     -- for debugging
    name    : string            -- effect type identifier
    payload : dict              -- effect-specific data
```

### Persistent Effects (examples)

```
{ kind: "persistent", name: "move-object",     payload: { object_id, x, y } }
{ kind: "persistent", name: "resize-object",   payload: { object_id, handle, start_rect, pointer_x, pointer_y } }
{ kind: "persistent", name: "set-selection",   payload: { object_ids: [id, ...] } }
{ kind: "persistent", name: "create-node",     payload: { x, y } }
{ kind: "persistent", name: "delete-nodes",    payload: { object_ids: [id, ...] } }
{ kind: "persistent", name: "create-edge",     payload: { from_id, to_id } }
```

### Volatile Effects (examples)

```
{ kind: "volatile", name: "show-marquee",    payload: { rect: {x1,y1,x2,y2}, candidate_ids: [...] } }
{ kind: "volatile", name: "hover-highlight", payload: { object_id } }
{ kind: "volatile", name: "drag-preview",    payload: { object_id, pointer_x, pointer_y } }
{ kind: "volatile", name: "edge-preview",    payload: { from_id, to_x, to_y } }
```

Volatile effects exist for one frame only. They are consumed by the projection system and discarded.

---

## COORDINATION (Judge state)

Maintained by the Judge. Readable by organisms only through `get_permission()`.

```
coordination:
    pointer_owner   : organism_name | None  -- who currently owns the pointer
    resource_holds  : { resource_id → organism_name }  -- held resources
    leases          : { organism_name → lease }

lease:
    resources   : set of resource_id
    kind        : "exclusive"
    valid       : bool
```

Organisms do not read `coordination` directly. They call `get_permission()` and receive a boolean.

---

## WORLD MODEL

Application-defined persistent state. Structure depends on the application; the architecture imposes only that:

- It is readable by organisms (for decision-making, e.g. checking if an object exists).
- It is writable only by `route_effects()`.

Typical minimal structure:

```
world:
    objects     : { id → object }
    selection   : [id, ...]

object:
    id          : string
    x, y        : number
    w, h        : number
    [application fields]
```

---

## CANVAS STATE (Projection layer)

Maintained by the projection system. Not shared with any other layer.

```
canvas_state:
    { logical_key → canvas_item }

canvas_item:
    item_id     : int           -- Tk canvas item handle
    type        : string        -- "rectangle", "oval", "line", "text", ...
    properties  : dict          -- fill, outline, coords, etc.
```

The projection system is the sole owner of `canvas_state`. No other layer reads or writes it.

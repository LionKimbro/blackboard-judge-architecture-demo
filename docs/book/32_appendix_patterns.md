# 32 — Appendix: Patterns

## Pattern 1: Standard Three-Phase Organism (IDLE → ARMED → ACTIVE)

The canonical structure for gesture organisms that require intent confirmation.

```
function organism_GESTURE(organism):
    if organism.state == "IDLE":
        -- Detect triggering condition.
        if not [trigger condition]:
            return
        if not get_permission("CHECK", [resources]):
            return
        organism.held ← [committed context]
        organism.data ← [working data]
        organism.state ← "ARMED"

    elif organism.state == "ARMED":
        -- Await confirmation or cancellation.
        if button_1_released:
            [optional: emit click effect]
            clear(organism)
            return
        if not drag_threshold_crossed:
            return
        if not get_permission("COMMIT", [resources]):
            clear(organism)
            return
        organism.state ← "ACTIVE"

    elif organism.state == "ACTIVE":
        -- Emit effects each cycle while active.
        emit_effect("persistent", [effect], [payload])
        emit_effect("volatile",   [effect], [payload])
        if [completion condition]:
            [optional: emit terminal effect]
            clear(organism)

    else:
        clear(organism)
```

---

## Pattern 2: Stateless Per-Cycle Organism

For organisms that emit a volatile effect each cycle based on current conditions, with no episode tracking.

```
function organism_HIGHLIGHT(organism):
    -- No state machine. Evaluates conditions each cycle.

    condition ← [some DERIVED or world model condition]
    if not condition:
        return

    emit_effect("volatile", [effect], [payload])
```

Used for: hover highlighting, cursor changes, transient indicators.

---

## Pattern 3: Tokenizer With Anchor State

For tokenizers that must remember a press point to compute a derived value (drag threshold, motionless duration).

```
function tokenizer_THRESHOLD(data):
    -- On press: record anchor.
    if DERIVED.current.button_1_pressed:
        data.anchor ← { x: RAW.current.x, y: RAW.current.y }
        data.crossed ← False

    -- On release: clear anchor.
    if DERIVED.current.button_1_released:
        data.anchor ← None
        data.crossed ← False
        DERIVED.current.threshold_crossed ← False
        return

    -- While held: compute from anchor.
    if data.anchor is None or not RAW.current.button_1_down:
        DERIVED.current.threshold_crossed ← False
        return

    dist ← distance(RAW.current, data.anchor)
    data.crossed ← data.crossed or (dist >= THRESHOLD)
    DERIVED.current.threshold_crossed ← data.crossed
    -- Once crossed, stays crossed until release (sticky threshold).
```

---

## Pattern 4: Effect Router

Separates persistent and volatile effects after organisms run.

```
function route_effects(effects):
    persistent ← [e for e in effects if e.kind == "persistent"]
    volatile   ← [e for e in effects if e.kind == "volatile"]

    for effect in persistent:
        apply_persistent_effect(effect)

    return volatile   -- passed to render_projection()
```

Volatile effects are returned (or stored) for the projection system to consume during the same cycle. They are not retained across cycles.

---

## Pattern 5: Projection Desired-State Builder

Separates world-object rendering from volatile overlay rendering.

```
function compute_desired_state(world, volatile_effects):
    desired ← {}

    -- Stable world objects
    for id, obj in world.objects:
        add_object_items(desired, id, obj, world.selection)

    -- Selection handles (application-specific)
    if len(world.selection) == 1:
        add_handle_items(desired, world.objects[world.selection[0]])

    -- Volatile overlays
    for effect in volatile_effects:
        add_overlay_items(desired, effect, world)

    return desired


function add_object_items(desired, id, obj, selection):
    is_selected ← id in selection
    desired["object:{id}:body"] ← {
        type: "rectangle",
        coords: [obj.x, obj.y, obj.x + obj.w, obj.y + obj.h],
        properties: { fill: obj.fill,
                      outline: "#1f4f7a" if is_selected else "#24323a",
                      width:   4 if is_selected else 2 }
    }
    desired["object:{id}:label"] ← {
        type: "text",
        coords: [obj.x + 8, obj.y + 8],
        properties: { text: obj.label, anchor: "nw" }
    }


function add_overlay_items(desired, effect, world):
    if effect.name == "hover-highlight":
        obj ← world.objects[effect.payload.object_id]
        desired["overlay:hover:{effect.payload.object_id}"] ← { ... }
    elif effect.name == "show-marquee":
        desired["overlay:marquee"] ← { ... }
    elif effect.name == "drag-preview":
        desired["overlay:drag-preview:{effect.payload.object_id}"] ← { ... }
    ...
```

---

## Pattern 6: Snapshot Positions for Group Move

Captures world-model positions at gesture start, used to compute deltas during the drag without accumulating float drift.

```
function snapshot_positions(object_ids):
    return { id: { x: world.objects[id].x, y: world.objects[id].y }
             for id in object_ids }

-- In organism ARMED → ACTIVE transition:
organism.data.start_positions ← snapshot_positions(organism.held.object_ids)

-- In organism ACTIVE, each cycle:
press ← organism.data.press_point
dx ← RAW.current.x - press.x
dy ← RAW.current.y - press.y

emit_effect("persistent", "move-group", {
    object_ids:      organism.held.object_ids,
    start_positions: organism.data.start_positions,
    dx:              dx,
    dy:              dy
})

-- In route_effects, apply_group_move:
for id in payload.object_ids:
    obj ← world.objects[id]
    start ← payload.start_positions[id]
    obj.x ← start.x + payload.dx
    obj.y ← start.y + payload.dy
```

This avoids accumulating rounding errors from repeated `obj.x += delta` calls during a long drag.

---

## Pattern 7: Logical Key Naming Convention

Use a consistent, hierarchical naming scheme for canvas state keys.

```
"object:{id}:body"              -- main shape of a world object
"object:{id}:label"             -- text label of a world object
"object:{id}:handle:{name}"     -- interactive handle on a world object
"edge:{from_id}:{to_id}"        -- edge between two objects
"overlay:{type}"                -- unique volatile overlay (e.g., marquee)
"overlay:{type}:{id}"           -- object-specific volatile overlay
"bg:{name}"                     -- background elements (grid, borders)
```

Sorted alphabetically, `bg:` comes before `object:`, which comes before `overlay:`. This means if items are created in key-sorted order, z-order is correct by default: backgrounds behind objects, objects behind overlays.

---

## Pattern 8: Periodic Tick

Enables time-based organisms to progress without user input.

```
TICK_INTERVAL_MS ← 100

function schedule_tick():
    root.after(TICK_INTERVAL_MS, handle_tick)

function handle_tick():
    populate_raw({})    -- no input changes, time advances
    run_cycle()
    schedule_tick()
```

Called once at startup. Self-rescheduling keeps the interval stable. Organisms check `RAW.current.time_ms` and `DERIVED.current.motionless_duration_ms` to implement time-based behavior.

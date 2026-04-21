# 12 — Organisms

## Purpose

Organisms are stateful processes that recognize interaction episodes over time and emit effects. Each organism is a finite state machine. Organisms read RAW and DERIVED; they do not perform perception themselves. Organisms coordinate resource access through the Judge.

---

## Organism Record

```
organism:
    name    : string            -- unique identifier
    active  : bool
    state   : string            -- current FSM state, starts at "IDLE"
    held    : dict              -- resources currently committed to
    data    : dict              -- working memory for the current episode
    fn      : function
```

---

## Standard Template

```
function organism_NAME(organism):
    if organism.state == "IDLE":
        handle_idle(organism)
        return

    if organism.state == "ARMED":
        handle_armed(organism)
        return

    if organism.state == "ACTIVE":
        handle_active(organism)
        return

    -- unknown state: reset
    clear(organism)


function handle_idle(organism):
    -- Wait for triggering condition.
    -- If condition met, request CHECK from Judge.
    -- On grant: record held resources, advance to ARMED or ACTIVE.
    -- On denial: stay IDLE.

function handle_armed(organism):
    -- Gesture is pending confirmation (e.g., waiting for drag threshold).
    -- On confirmation: advance to ACTIVE.
    -- On cancellation (release before threshold): emit any cancel effects, clear.

function handle_active(organism):
    -- Gesture is underway.
    -- Each cycle: emit appropriate effects.
    -- On completion condition: emit terminal effects, clear.

function clear(organism):
    organism.state ← "IDLE"
    organism.held  ← {}
    organism.data  ← {}
```

### Permission Calls

- `get_permission("CHECK", resources)` — called in IDLE when first arming. Soft feasibility test: verifies resources are uncontested, but does not lock them.
- `get_permission("COMMIT", resources)` — called when the gesture escalates (e.g., threshold crossed). Hard lock: claims resources exclusively. This is where conflicts between simultaneously-ARMED organisms are resolved.

Both calls return a boolean. On denial, the organism calls `clear()` and returns.

---

## Example 1: Hover Highlight

Emits a volatile hover effect when the pointer is over an object and no other organism owns the pointer.

```
function organism_hover_highlight(organism):
    -- This organism has no ARMED or ACTIVE states.
    -- It emits a volatile effect every cycle when the condition holds.

    target ← DERIVED.current.pointer_target

    if target is None:
        return

    if not get_permission("CHECK", []):
        return

    emit_effect("volatile", "hover-highlight", { object_id: target })
```

Note: hover-highlight does not need to hold a resource lock between cycles. It simply checks each cycle whether it may emit.

---

## Example 2: Drag Object

Recognizes press → threshold → drag → release over a single object.

```
STATES: IDLE, ARMED, DRAGGING

function organism_drag_object(organism):
    if organism.state == "IDLE":
        handle_drag_idle(organism)
    elif organism.state == "ARMED":
        handle_drag_armed(organism)
    elif organism.state == "DRAGGING":
        handle_dragging(organism)
    else:
        clear(organism)


function handle_drag_idle(organism):
    if not DERIVED.current.button_1_pressed:
        return
    target ← DERIVED.current.pointer_target
    if target is None:
        return

    if not get_permission("CHECK", [target, "pointer"]):
        clear(organism)
        return

    organism.held ← { object_id: target }
    organism.data ← {
        press_point:  { x: RAW.current.x, y: RAW.current.y },
        grab_offset:  { x: RAW.current.x - world.objects[target].x,
                        y: RAW.current.y - world.objects[target].y }
    }
    organism.state ← "ARMED"

    emit_effect("persistent", "set-selection", { object_ids: [target] })


function handle_drag_armed(organism):
    if DERIVED.current.button_1_released:
        -- click, not drag
        clear(organism)
        return

    if not DERIVED.current.drag_threshold_crossed:
        return

    if not get_permission("COMMIT", [organism.held.object_id, "pointer"]):
        clear(organism)
        return

    organism.state ← "DRAGGING"


function handle_dragging(organism):
    target ← organism.held.object_id
    grab   ← organism.data.grab_offset

    emit_effect("persistent", "move-object", {
        object_id: target,
        x: RAW.current.x - grab.x,
        y: RAW.current.y - grab.y
    })

    emit_effect("volatile", "drag-preview", {
        object_id: target,
        pointer_x: RAW.current.x,
        pointer_y: RAW.current.y
    })

    if DERIVED.current.button_1_released:
        clear(organism)
```

---

## Example 3: Marquee Selection

Recognizes drag from empty space and builds a selection rectangle.

```
STATES: IDLE, ARMED, SELECTING

function organism_marquee_select(organism):
    if organism.state == "IDLE":
        handle_marquee_idle(organism)
    elif organism.state == "ARMED":
        handle_marquee_armed(organism)
    elif organism.state == "SELECTING":
        handle_marquee_selecting(organism)
    else:
        clear(organism)


function handle_marquee_idle(organism):
    if not DERIVED.current.button_1_pressed:
        return
    if DERIVED.current.pointer_target is not None:
        return    -- pointer is on an object, not empty space

    if not get_permission("CHECK", ["pointer"]):
        clear(organism)
        return

    organism.data ← { press_point: { x: RAW.current.x, y: RAW.current.y } }
    organism.state ← "ARMED"


function handle_marquee_armed(organism):
    if DERIVED.current.button_1_released:
        emit_effect("persistent", "set-selection", { object_ids: [] })
        clear(organism)
        return

    if not DERIVED.current.drag_threshold_crossed:
        return

    organism.state ← "SELECTING"


function handle_marquee_selecting(organism):
    rect ← normalize_rect(organism.data.press_point, RAW.current)
    hits ← objects_in_rect(rect)

    emit_effect("volatile", "show-marquee", { rect: rect, candidate_ids: hits })

    if DERIVED.current.button_1_released:
        emit_effect("persistent", "set-selection", { object_ids: hits })
        clear(organism)
```

---

## Example 4: Group Drag

Recognizes drag beginning on a selected object and moves the entire selection as a unit.

```
STATES: IDLE, ARMED, DRAGGING

function organism_group_drag(organism):
    if organism.state == "IDLE":
        handle_group_idle(organism)
    elif organism.state == "ARMED":
        handle_group_armed(organism)
    elif organism.state == "DRAGGING":
        handle_group_dragging(organism)
    else:
        clear(organism)


function handle_group_idle(organism):
    if not DERIVED.current.button_1_pressed:
        return
    target ← DERIVED.current.pointer_target
    if target is None or target not in world.selection:
        return

    selected ← list(world.selection)
    if not get_permission("CHECK", selected):
        clear(organism)
        return

    organism.held ← { object_ids: selected, lead_id: target }
    organism.data ← {
        press_point:     { x: RAW.current.x, y: RAW.current.y },
        start_positions: snapshot_positions(selected)
    }
    organism.state ← "ARMED"


function handle_group_armed(organism):
    if DERIVED.current.button_1_released:
        clear(organism)
        return

    if not DERIVED.current.drag_threshold_crossed:
        return

    if not get_permission("COMMIT", organism.held.object_ids):
        clear(organism)
        return

    organism.state ← "DRAGGING"


function handle_group_dragging(organism):
    press ← organism.data.press_point
    dx    ← RAW.current.x - press.x
    dy    ← RAW.current.y - press.y

    emit_effect("persistent", "move-group", {
        object_ids:      organism.held.object_ids,
        start_positions: organism.data.start_positions,
        dx:              dx,
        dy:              dy
    })

    emit_effect("volatile", "drag-preview", {
        object_id: organism.held.lead_id,
        pointer_x: RAW.current.x,
        pointer_y: RAW.current.y
    })

    if DERIVED.current.button_1_released:
        clear(organism)
```

---

## Organism Ordering

Organisms run in registration order each cycle. Order determines implicit priority: multiple organisms may pass CHECK and enter ARMED simultaneously. When the threshold is crossed, they race to COMMIT in registration order. The first to reach COMMIT wins; later organisms find the resource locked and clear.

Design the registration order to reflect intended priority. Document the reasoning when order is load-bearing.

---

## Organisms Must Not Encode Coordination Logic

Organisms must not encode coordination logic about other organisms.

In particular, organisms must not:

- Check for conditions that imply another organism should take precedence (e.g., `if target in world.selection: return`).
- Replicate coordination decisions using world state, pointer location, or any other proxy for "what another organism would do."
- Attempt to avoid conflicts by conditionally disabling themselves based on assumed behavior of siblings.

All coordination between organisms must occur exclusively through:

- `get_permission()` — the organism asks; the judge answers.
- Resource contention — if a resource is held, the request is denied.
- Organism ordering — registration order determines who gets first access.

If an organism's behavior depends on whether another organism should act, that dependency must be expressed through resource requests, not conditional logic. The organism does not need to know why it was denied — only that it was.

Violations of this rule introduce hidden coupling between organisms and break the modularity that the Judge exists to provide.

---

## What Organisms Must Not Do

- Perform hit-testing or spatial computation (belongs to tokenizers).
- Write directly to the world model.
- Call canvas drawing functions.
- Read `coordination` directly (use `get_permission()`).
- Hold references to Tk objects or canvas items.

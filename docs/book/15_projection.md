# 15 — Projection

## Purpose

Projection is the reconciliation system between the application's logical state and the Tkinter Canvas. It reads the world model and the current frame's volatile effects, computes the complete desired visual state, and applies the minimal set of canvas operations to reach that state.

---

## Retained-Mode Canvas

Tkinter Canvas is a **retained-mode** drawing surface. Canvas items (rectangles, ovals, lines, text) are persistent objects with integer item IDs. They are not redrawn each frame automatically; they persist until explicitly deleted or modified.

This means the projection system must:
1. Know what is currently on the canvas.
2. Know what should be on the canvas.
3. Apply only the differences.

This is more efficient than deleting everything and redrawing from scratch each cycle. It also enables smooth animation and avoids flicker.

---

## Projection State

The projection system maintains its own private state: a record of every canvas item currently on screen.

```
canvas_state : { logical_key → canvas_item }

canvas_item:
    item_id     : int           -- Tk canvas item handle
    type        : string        -- "rectangle", "oval", "line", "text"
    coords      : list          -- positional arguments (e.g., [x1, y1, x2, y2])
    properties  : dict          -- visual properties (fill, outline, width, dash, ...)
```

`logical_key` is an application-defined string that uniquely identifies a visual element, independent of its canvas item ID. Examples:

```
"object:alpha:body"
"object:alpha:label"
"object:alpha:resize-handle:nw"
"overlay:marquee"
"overlay:hover:alpha"
"overlay:drag-preview:alpha"
```

---

## Reconciliation Algorithm

```
function render_projection(world, volatile_effects):
    desired ← compute_desired_state(world, volatile_effects)
    reconcile(desired)


function reconcile(desired):
    current_keys ← set(canvas_state.keys())
    desired_keys  ← set(desired.keys())

    -- Delete items no longer needed
    for key in (current_keys - desired_keys):
        canvas.delete(canvas_state[key].item_id)
        canvas_state.pop(key)

    -- Create new items
    for key in (desired_keys - current_keys):
        item_id ← canvas_create(desired[key])
        canvas_state[key] ← { item_id: item_id, **desired[key] }

    -- Update changed items
    for key in (desired_keys & current_keys):
        if differs(canvas_state[key], desired[key]):
            canvas_update(canvas_state[key].item_id, desired[key])
            canvas_state[key] ← { item_id: canvas_state[key].item_id, **desired[key] }


function canvas_create(spec):
    if spec.type == "rectangle":
        return canvas.create_rectangle(*spec.coords, **spec.properties)
    if spec.type == "oval":
        return canvas.create_oval(*spec.coords, **spec.properties)
    if spec.type == "line":
        return canvas.create_line(*spec.coords, **spec.properties)
    if spec.type == "text":
        return canvas.create_text(*spec.coords, **spec.properties)
    ...


function canvas_update(item_id, spec):
    canvas.coords(item_id, *spec.coords)
    canvas.itemconfig(item_id, **spec.properties)


function differs(current, desired):
    return current.coords != desired.coords or current.properties != desired.properties
```

---

## Computing Desired State

`compute_desired_state` maps the world model and volatile effects to a flat dict of logical-key → canvas item spec. It is a pure function: given the same inputs it produces the same output.

```
function compute_desired_state(world, volatile_effects):
    desired ← {}

    -- World objects
    for id, obj in world.objects:
        is_selected ← id in world.selection

        desired["object:{id}:body"] ← {
            type:       "rectangle",
            coords:     [obj.x, obj.y, obj.x + obj.w, obj.y + obj.h],
            properties: {
                fill:    obj.fill,
                outline: selection_color(is_selected),
                width:   selection_width(is_selected)
            }
        }

        desired["object:{id}:label"] ← {
            type:       "text",
            coords:     [obj.x + 8, obj.y + 8],
            properties: { text: obj.label, anchor: "nw", fill: "#ffffff" }
        }

    -- Resize handles (when exactly one object is selected)
    if len(world.selection) == 1:
        id  ← world.selection[0]
        obj ← world.objects[id]
        for handle in ("nw", "ne", "sw", "se"):
            cx, cy ← handle_center(obj, handle)
            desired["object:{id}:handle:{handle}"] ← {
                type:       "rectangle",
                coords:     [cx - 5, cy - 5, cx + 5, cy + 5],
                properties: { fill: "#ffffff", outline: "#1f4f7a", width: 2 }
            }

    -- Volatile effects
    for effect in volatile_effects:
        if effect.name == "hover-highlight":
            obj ← world.objects[effect.payload.object_id]
            desired["overlay:hover:{effect.payload.object_id}"] ← {
                type:       "rectangle",
                coords:     [obj.x - 4, obj.y - 4,
                             obj.x + obj.w + 4, obj.y + obj.h + 4],
                properties: { outline: "#f2c14e", width: 3 }
            }

        elif effect.name == "show-marquee":
            rect ← effect.payload.rect
            desired["overlay:marquee"] ← {
                type:       "rectangle",
                coords:     [rect.x1, rect.y1, rect.x2, rect.y2],
                properties: { outline: "#1f4f7a", width: 2, dash: (4, 3) }
            }

        elif effect.name == "drag-preview":
            obj ← world.objects[effect.payload.object_id]
            cx  ← obj.x + obj.w / 2
            cy  ← obj.y + obj.h / 2
            desired["overlay:drag-preview:{effect.payload.object_id}"] ← {
                type:       "line",
                coords:     [effect.payload.pointer_x, effect.payload.pointer_y, cx, cy],
                properties: { fill: "#2f4858", dash: (6, 4), width: 2 }
            }

    return desired
```

---

## Z-Order

Tkinter Canvas draws items in creation order; later items appear on top. When reconciling, z-order must be managed explicitly if it matters.

Two strategies:

**Strategy 1 — Key prefix ordering.** Name logical keys so that stable sort order produces the desired z-order. Example prefix scheme:

```
"bg:..."        -- background elements
"object:..."    -- world objects
"overlay:..."   -- volatile overlays (always on top)
```

Create items in this order. Since `reconcile` only creates items that don't exist, the z-order of existing items is preserved.

**Strategy 2 — Explicit lift/lower.** After reconciliation, call `canvas.tag_raise` or `canvas.tag_lower` on specific items if their z-order must change dynamically.

---

## Projection Must Not

- Modify the world model (no writing to `world`).
- Call `emit_effect()`.
- Make decisions based on input state (RAW or DERIVED).
- Hold organism state or coordination state.
- Issue canvas commands outside of `reconcile()`.

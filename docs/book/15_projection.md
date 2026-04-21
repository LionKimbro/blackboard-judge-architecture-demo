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

The projection system maintains two private structures:

```
canvas_map       : { logical_key → item_id }     -- maps logical keys to Tk canvas handles
previous_desired : { logical_key → spec }         -- the desired state from the prior cycle
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

Separating `canvas_map` from `previous_desired` avoids duplicating spec data inside the canvas state record. The spec lives in exactly one place — `previous_desired` — and `canvas_map` holds only the handle needed to issue canvas commands. There is no risk of the two drifting apart.

---

## Reconciliation Algorithm

```
function render_projection(world, volatile_effects):
    desired ← compute_desired_state(world, volatile_effects)
    reconcile(desired)
    previous_desired ← desired


function reconcile(desired):
    current_keys ← set(canvas_map.keys())
    desired_keys  ← set(desired.keys())

    -- Delete items no longer needed
    for key in (current_keys - desired_keys):
        canvas.delete(canvas_map[key])
        canvas_map.pop(key)

    -- Create new items (iterate in desired order to respect z-order)
    for key in desired_keys - current_keys:
        item_id ← canvas_create(desired[key])
        canvas_map[key] ← item_id

    -- Update changed items
    for key in (desired_keys & current_keys):
        if differs(previous_desired.get(key), desired[key]):
            canvas_update(canvas_map[key], desired[key])


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


function differs(prev_spec, desired_spec):
    if prev_spec is None:
        return True
    return prev_spec.coords != desired_spec.coords or prev_spec.properties != desired_spec.properties
```

> **Implementation note:** The equality check in `differs` is intentionally simplified. Real implementations may need to account for:
> - Floating-point vs. integer coordinate representation (Tkinter normalizes canvas coordinates to integers; store coords in the form Tkinter will accept to avoid false positives every cycle).
> - Dictionary key ordering (use normalized, canonical representations when comparing property dicts).
> - Color string normalization (e.g., `"#fff"` vs. `"#ffffff"` vs. `"white"`).
>
> The safest approach: normalize all coords and properties to their canonical form before writing them into `desired`, so comparisons are always between values in the same form.

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

**Desired state is ordered.** `compute_desired_state` returns an ordered structure (e.g., an ordered dict or list of `(key, spec)` pairs), not an unordered mapping. The order of entries defines the intended z-order. `reconcile` iterates desired state in this order so that newly created items are inserted into the canvas in the correct position, not simply appended to the top of the stack.

Two strategies for maintaining order:

**Strategy 1 — Key prefix ordering.** Name logical keys so that stable sort order produces the desired z-order. Example prefix scheme:

```
"bg:..."        -- background elements
"object:..."    -- world objects
"overlay:..."   -- volatile overlays (always on top)
```

`compute_desired_state` emits keys in sorted order. `reconcile` iterates in that order, creating items that don't yet exist. Since Tkinter appends new items above existing ones, items created later in the iteration naturally land higher in the z-stack.

**Strategy 2 — Explicit lift/lower.** After reconciliation, call `canvas.tag_raise` or `canvas.tag_lower` on specific items if their z-order must change dynamically. Necessary when existing items need to be reordered relative to each other, not just new items placed correctly.

---

## Coexistence With External Canvas Writers

Other code may write to the canvas outside of the projection system — debug overlays, decorative elements, UI chrome. This is permitted, subject to one rule:

**External writers must not modify or delete items placed by the projection system, and the projection system must not modify or delete items placed by external writers.**

Enforce this boundary using Tkinter canvas tags:

**Option A — Projection tags its own items.** The projection system applies a tag (e.g., `"__projection__"`) to every item it creates. External writers must not touch items carrying this tag.

```
function canvas_create(spec):
    if spec.type == "rectangle":
        item_id ← canvas.create_rectangle(*spec.coords, **spec.properties)
    ...
    canvas.addtag_withtag("__projection__", item_id)
    return item_id
```

**Option B — External writers tag their own items.** External code applies a tag (e.g., `"__external__"`) to everything it creates. The projection system ignores items carrying this tag.

Either convention works. Choose one and apply it consistently. The important thing is that both sides can identify what they own so that neither inadvertently interferes with the other.

---

## Projection Must Not

- Modify the world model (no writing to `world`).
- Call `emit_effect()`.
- Make decisions based on input state (RAW or DERIVED).
- Hold organism state or coordination state.
- Issue canvas commands outside of `reconcile()`.

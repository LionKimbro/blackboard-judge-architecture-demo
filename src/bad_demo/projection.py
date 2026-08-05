"""Retained-mode Canvas reconciliation for the BAD-rendered demo."""

from . import canvas_host_window, geometry, grid


g = {"items": {}, "specs": {}}


def render_projection(world, previews, config, raw):
    """Reconcile durable visuals and replace one-frame immediate visuals."""
    canvas = canvas_host_window.widgets["canvas"]
    if canvas is None:
        return
    try:
        if not canvas.winfo_exists():
            canvas_host_window.widgets["canvas"] = None
            return
    except AttributeError:
        pass
    except Exception:
        canvas_host_window.widgets["canvas"] = None
        return
    canvas.delete("immediate")
    desired = build_desired_state(world, previews, config, raw)
    reconcile(canvas, desired)
    grid.ensure_grid(canvas, make_grid_configuration(config), raw["show-grid"])
    draw_immediates(canvas, world, previews, config)


def build_desired_state(world, previews, config, raw):
    presentation = build_preview_presentation(world, previews, config)
    desired = {"background": ("rectangle", (0, 0, config["canvas-width"], config["canvas-height"]), {"fill": "#f6f2e8", "outline": "", "tags": "canvas-background"})}
    for object_id, obj in presentation.items():
        selected = object_id in world["selected-objects"]
        desired[f"object:{object_id}:body"] = ("rectangle", (obj["x"], obj["y"], obj["x"] + obj["w"], obj["y"] + obj["h"]), {"fill": obj["fill"], "outline": "#1f4f7a" if selected else "#24323a", "width": 4 if selected else 2, "tags": "model-object"})
        desired[f"object:{object_id}:label"] = ("text", (obj["x"] + 8, obj["y"] + 8), {"text": obj["label"], "anchor": "nw", "fill": "white", "tags": "model-object"})
    selected_id = geometry.single_selected_object_id(world)
    dragged_object_ids = preview_dragged_object_ids(previews)
    if selected_id and selected_id not in dragged_object_ids:
        for handle, (x, y) in geometry.resize_handle_centers(presentation[selected_id]).items():
            desired[f"handle:{selected_id}:{handle}"] = ("rectangle", (x - config["handle-half"], y - config["handle-half"], x + config["handle-half"], y + config["handle-half"]), {"fill": "white", "outline": "#1f4f7a"})
    return desired


def make_grid_configuration(config):
    return {"left": 0, "right": config["playfield-right"], "top": 0,
            "bottom": config["canvas-height"], "step": config["quantization-step"]}


def preview_dragged_object_ids(previews):
    return {
        object_id
        for effect in previews
        if effect["name"] == "drag-preview"
        for object_id in effect["payload"]["object-ids"]
    }


def build_preview_presentation(world, previews, config):
    """Return world visuals with this frame's object-preview geometry applied."""
    presentation = {object_id: dict(obj) for object_id, obj in world["objects"].items()}
    for effect in previews:
        payload, name = effect["payload"], effect["name"]
        if name == "drag-preview":
            for object_id, position in payload["positions"].items():
                if object_id in presentation:
                    presentation[object_id].update(position)
        elif name == "resize-preview" and payload["object-id"] in presentation:
            presentation[payload["object-id"]].update(payload["rect"])
    return presentation


def reconcile(canvas, desired):
    for key in list(g["items"]):
        if key not in desired:
            canvas.delete(g["items"].pop(key)); g["specs"].pop(key, None)
    for key, spec in desired.items():
        if key not in g["items"]:
            g["items"][key] = create_item(canvas, spec)
        elif g["specs"].get(key) != spec:
            canvas.coords(g["items"][key], *spec[1]); canvas.itemconfig(g["items"][key], **spec[2])
        g["specs"][key] = spec


def create_item(canvas, spec):
    kind, coords, options = spec
    return getattr(canvas, f"create_{kind}")(*coords, **options)


def draw_immediates(canvas, world, previews, config):
    for effect in previews:
        payload, name = effect["payload"], effect["name"]
        if name == "hover-highlight":
            obj = world["objects"].get(payload["object-id"])
            if obj:
                draw_highlight_halo(canvas, obj)
        elif name == "marquee-preview":
            rect = payload["rect"]
            canvas.create_rectangle(rect["x1"], rect["y1"], rect["x2"], rect["y2"], outline="#1f4f7a", dash=(4, 3), tags="immediate")
            for object_id in payload["object-ids"]:
                obj = world["objects"].get(object_id)
                if obj:
                    draw_highlight_halo(canvas, obj)


def draw_highlight_halo(canvas, obj):
    canvas.create_rectangle(obj["x"] - 4, obj["y"] - 4, obj["x"] + obj["w"] + 4, obj["y"] + obj["h"] + 4, outline="#f2c14e", width=3, tags="immediate")

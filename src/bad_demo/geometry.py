"""Geometry and world-query helpers for the BAD-rendered canvas demo."""


def clamp(value, lower, upper):
    return max(lower, min(upper, value))


def snap_value(value, step):
    return round(value / step) * step


def point_inside_object(x, y, obj):
    return obj["x"] <= x <= obj["x"] + obj["w"] and obj["y"] <= y <= obj["y"] + obj["h"]


def find_object_at(objects, x, y):
    for object_id in reversed(list(objects)):
        if point_inside_object(x, y, objects[object_id]):
            return object_id
    return None


def single_selected_object_id(world):
    selected = world["selected-objects"]
    return selected[0] if len(selected) == 1 else None


def find_resize_handle_at(world, x, y, half_size):
    object_id = single_selected_object_id(world)
    if object_id is None:
        return None
    obj = world["objects"][object_id]
    for handle, (cx, cy) in resize_handle_centers(obj).items():
        if abs(x - cx) <= half_size and abs(y - cy) <= half_size:
            return {"object-id": object_id, "handle": handle}
    return None


def resize_handle_centers(obj):
    return {
        "nw": (obj["x"], obj["y"]),
        "ne": (obj["x"] + obj["w"], obj["y"]),
        "sw": (obj["x"], obj["y"] + obj["h"]),
        "se": (obj["x"] + obj["w"], obj["y"] + obj["h"]),
    }


def rect_from_points(p1, p2):
    return {"x1": min(p1["x"], p2["x"]), "y1": min(p1["y"], p2["y"]),
            "x2": max(p1["x"], p2["x"]), "y2": max(p1["y"], p2["y"])}


def rect_intersects_object(rect, obj):
    return not (rect["x2"] < obj["x"] or rect["x1"] > obj["x"] + obj["w"]
                or rect["y2"] < obj["y"] or rect["y1"] > obj["y"] + obj["h"])


def list_objects_in_rect(objects, rect):
    return [object_id for object_id, obj in objects.items() if rect_intersects_object(rect, obj)]


def snapshot_object_positions(objects, object_ids):
    return {object_id: {"x": objects[object_id]["x"], "y": objects[object_id]["y"]}
            for object_id in object_ids}


def compute_group_delta_bound(objects, start_positions, delta, axis, right, bottom, margin):
    lower = None
    upper = None
    for object_id, start in start_positions.items():
        obj = objects[object_id]
        if axis == "x":
            low, high = margin - start["x"], right - obj["w"] - margin - start["x"]
        else:
            low, high = margin - start["y"], bottom - obj["h"] - margin - start["y"]
        lower = low if lower is None else max(lower, low)
        upper = high if upper is None else min(upper, high)
    return clamp(delta, lower, upper)


def make_drag_positions(objects, start_positions, requested_dx, requested_dy, config, quantization_enabled):
    """Return lawful positions from one shared, optionally snapped drag delta."""
    if quantization_enabled:
        requested_dx = snap_value(requested_dx, config["quantization-step"])
        requested_dy = snap_value(requested_dy, config["quantization-step"])
    dx = compute_group_delta_bound(objects, start_positions, requested_dx, "x", config["playfield-right"], config["canvas-height"], config["margin"])
    dy = compute_group_delta_bound(objects, start_positions, requested_dy, "y", config["playfield-right"], config["canvas-height"], config["margin"])
    return {object_id: {"x": start["x"] + dx, "y": start["y"] + dy} for object_id, start in start_positions.items()}


def compute_resized_rect(start_rect, handle, pointer_x, pointer_y, right, bottom, minimum, margin):
    left, top = start_rect["x"], start_rect["y"]
    end_x, end_y = left + start_rect["w"], top + start_rect["h"]
    if "w" in handle: left = clamp(pointer_x, margin, end_x - minimum)
    if "e" in handle: end_x = clamp(pointer_x, left + minimum, right - margin)
    if "n" in handle: top = clamp(pointer_y, margin, end_y - minimum)
    if "s" in handle: end_y = clamp(pointer_y, top + minimum, bottom - margin)
    return {"x": left, "y": top, "w": end_x - left, "h": end_y - top}


def make_resize_rectangle(start_rect, handle, pointer_x, pointer_y, config, quantization_enabled):
    """Return the optionally snapped, lawful rectangle for one resize gesture."""
    if quantization_enabled:
        pointer_x = snap_value(pointer_x, config["quantization-step"])
        pointer_y = snap_value(pointer_y, config["quantization-step"])
    return compute_resized_rect(start_rect, handle, pointer_x, pointer_y, config["playfield-right"], config["canvas-height"], config["min-size"], config["margin"])


def positions_are_lawful(objects, positions, config):
    for object_id, position in positions.items():
        obj = objects.get(object_id)
        if obj is None:
            return False
        if not config["margin"] <= position["x"] <= config["playfield-right"] - obj["w"] - config["margin"]:
            return False
        if not config["margin"] <= position["y"] <= config["canvas-height"] - obj["h"] - config["margin"]:
            return False
    return True


def rectangle_is_lawful(rect, config):
    return (rect["w"] >= config["min-size"] and rect["h"] >= config["min-size"]
            and rect["x"] >= config["margin"] and rect["y"] >= config["margin"]
            and rect["x"] + rect["w"] <= config["playfield-right"] - config["margin"]
            and rect["y"] + rect["h"] <= config["canvas-height"] - config["margin"])

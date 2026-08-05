"""Shared perception tokenizers for the BAD-rendered interaction runtime."""

from . import geometry, interaction_runtime

tokenizers = []


def initialize_tokenizers():
    tokenizers.clear()
    tokenizers.extend([
        make_tokenizer_record("pointer-motion", tokenizer_pointer_motion),
        make_tokenizer_record("button-1", tokenizer_button_1),
        make_tokenizer_record("pointer-target", tokenizer_pointer_target),
        make_tokenizer_record("resize-handles", tokenizer_resize_handles),
        make_tokenizer_record("pointer-draggable-target", tokenizer_pointer_draggable_target),
        make_tokenizer_record("button-1-click", tokenizer_button_1_click),
        make_tokenizer_record("drag-threshold", tokenizer_drag_threshold),
    ])


def make_tokenizer_record(name, fn):
    return {"NAME": name, "ACTIVE": True, "DATA": {}, "FN": fn}


def make_initial_derived():
    return {"moving": False, "dx": 0, "dy": 0, "motionless-duration": 0,
            "button-1-pressed": False, "button-1-released": False,
            "button-1-clicked": False, "single-click-draggable-target": None,
            "pointer-target": None, "pointer-draggable-target": None,
            "entered-target": None, "left-target": None,
            "pointer-handle-target": None, "drag-threshold-crossed": False}


def run_tokenizers():
    interaction_runtime.derived.clear()
    for tokenizer in tokenizers:
        if tokenizer["ACTIVE"]:
            tokenizer["FN"](tokenizer)


def tokenizer_pointer_motion(tokenizer):
    dx, dy = interaction_runtime.raw["x"] - interaction_runtime.raw_prev["x"], interaction_runtime.raw["y"] - interaction_runtime.raw_prev["y"]
    moved = dx != 0 or dy != 0
    interaction_runtime.derived.update({"dx": dx, "dy": dy, "moving": moved})
    if moved:
        tokenizer["DATA"]["last-motion-ms"] = interaction_runtime.raw["ms"]
    last_motion = tokenizer["DATA"].get("last-motion-ms", interaction_runtime.raw["ms"])
    interaction_runtime.derived["motionless-duration"] = max(0, interaction_runtime.raw["ms"] - last_motion)


def tokenizer_button_1(tokenizer):
    del tokenizer
    interaction_runtime.derived.update({"button-1-pressed": interaction_runtime.raw["button-1-down"] and not interaction_runtime.raw_prev["button-1-down"], "button-1-released": interaction_runtime.raw_prev["button-1-down"] and not interaction_runtime.raw["button-1-down"]})


def tokenizer_pointer_target(tokenizer):
    del tokenizer
    target = geometry.find_object_at(interaction_runtime.world["objects"], interaction_runtime.raw["x"], interaction_runtime.raw["y"]) if interaction_runtime.raw["inside-canvas"] else None
    interaction_runtime.derived.update({"pointer-target": target, "entered-target": None, "left-target": None})
    if target != interaction_runtime.raw_prev["mouse-over"]:
        interaction_runtime.derived["entered-target"] = target
        interaction_runtime.derived["left-target"] = interaction_runtime.raw_prev["mouse-over"]


def tokenizer_resize_handles(tokenizer):
    del tokenizer
    target = geometry.find_resize_handle_at(interaction_runtime.world, interaction_runtime.raw["x"], interaction_runtime.raw["y"], interaction_runtime.config["handle-half"]) if interaction_runtime.raw["inside-canvas"] else None
    interaction_runtime.derived["pointer-handle-target"] = target


def tokenizer_pointer_draggable_target(tokenizer):
    del tokenizer
    target = interaction_runtime.derived["pointer-target"]
    interaction_runtime.derived["pointer-draggable-target"] = target if target is not None and interaction_runtime.derived["pointer-handle-target"] is None else None


def tokenizer_button_1_click(tokenizer):
    interaction_runtime.derived.update({"button-1-clicked": False, "single-click-draggable-target": None})
    if interaction_runtime.derived["button-1-pressed"]:
        tokenizer["DATA"]["press"] = {"x": interaction_runtime.raw["x"], "y": interaction_runtime.raw["y"], "ms": interaction_runtime.raw["ms"], "moved": False}
        return
    press = tokenizer["DATA"].get("press")
    if press is None:
        return
    if interaction_runtime.raw["button-1-down"] and interaction_runtime.derived["moving"]:
        press["moved"] = True
    if not interaction_runtime.derived["button-1-released"]:
        return
    same_place = press["x"] == interaction_runtime.raw["x"] and press["y"] == interaction_runtime.raw["y"]
    timely = interaction_runtime.raw["ms"] - press["ms"] <= interaction_runtime.config["click-duration-ms"]
    if same_place and not press["moved"] and timely:
        interaction_runtime.derived["button-1-clicked"] = True
        interaction_runtime.derived["single-click-draggable-target"] = interaction_runtime.derived["pointer-draggable-target"]
    tokenizer["DATA"]["press"] = None


def tokenizer_drag_threshold(tokenizer):
    if interaction_runtime.derived["button-1-pressed"]:
        tokenizer["DATA"]["press-point"] = {"x": interaction_runtime.raw["x"], "y": interaction_runtime.raw["y"]}
    if interaction_runtime.derived["button-1-released"] or not interaction_runtime.raw["button-1-down"]:
        tokenizer["DATA"]["press-point"] = None
        interaction_runtime.derived["drag-threshold-crossed"] = False
        return
    point = tokenizer["DATA"].get("press-point")
    if point is None:
        interaction_runtime.derived["drag-threshold-crossed"] = False
        return
    dx, dy = interaction_runtime.raw["x"] - point["x"], interaction_runtime.raw["y"] - point["y"]
    interaction_runtime.derived["drag-threshold-crossed"] = dx * dx + dy * dy >= interaction_runtime.config["drag-threshold"] ** 2

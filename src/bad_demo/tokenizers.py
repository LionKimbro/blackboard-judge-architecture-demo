"""Shared perception tokenizers for the BAD-rendered interaction runtime."""

from . import geometry


def make_initial_derived():
    """Return only the prior-frame baseline used before the first cycle."""
    return {"moving": False, "dx": 0, "dy": 0, "motionless-duration": 0,
            "button-1-pressed": False, "button-1-released": False,
            "pointer-target": None, "entered-target": None, "left-target": None,
            "pointer-handle-target": None, "drag-threshold-crossed": False}


def run_tokenizers(system, world, config):
    """Start DERIVED empty, then let each ordered tokenizer write its facts."""
    system["DERIVED"] = {}
    for tokenizer in system["TOKENIZERS"]:
        if tokenizer["ACTIVE"]:
            tokenizer["FN"](system, world, config, tokenizer)


def tokenizer_pointer_motion(system, world, config, tokenizer):
    del world, config
    raw, previous = system["RAW"], system["RAW-PREV"]
    dx, dy = raw["x"] - previous["x"], raw["y"] - previous["y"]
    moved = dx != 0 or dy != 0
    system["DERIVED"].update({"dx": dx, "dy": dy, "moving": moved})
    if moved:
        tokenizer["DATA"]["last-motion-ms"] = raw["ms"]
    last_motion = tokenizer["DATA"].get("last-motion-ms", raw["ms"])
    system["DERIVED"]["motionless-duration"] = max(0, raw["ms"] - last_motion)


def tokenizer_button_1(system, world, config, tokenizer):
    del world, config, tokenizer
    raw, previous = system["RAW"], system["RAW-PREV"]
    system["DERIVED"].update({
        "button-1-pressed": raw["button-1-down"] and not previous["button-1-down"],
        "button-1-released": previous["button-1-down"] and not raw["button-1-down"],
    })


def tokenizer_pointer_target(system, world, config, tokenizer):
    del config, tokenizer
    raw, previous = system["RAW"], system["RAW-PREV"]
    target = geometry.find_object_at(world["objects"], raw["x"], raw["y"]) if raw["inside-canvas"] else None
    system["DERIVED"].update({"pointer-target": target, "entered-target": None, "left-target": None})
    if target != previous["mouse-over"]:
        system["DERIVED"]["entered-target"] = target
        system["DERIVED"]["left-target"] = previous["mouse-over"]


def tokenizer_resize_handles(system, world, config, tokenizer):
    del tokenizer
    target = None
    if system["RAW"]["inside-canvas"]:
        target = geometry.find_resize_handle_at(world, system["RAW"]["x"], system["RAW"]["y"], config["handle-half"])
    system["DERIVED"]["pointer-handle-target"] = target


def tokenizer_drag_threshold(system, world, config, tokenizer):
    del world
    derived, raw = system["DERIVED"], system["RAW"]
    if derived["button-1-pressed"]:
        tokenizer["DATA"]["press-point"] = {"x": raw["x"], "y": raw["y"]}
    if derived["button-1-released"] or not raw["button-1-down"]:
        tokenizer["DATA"]["press-point"] = None
        derived["drag-threshold-crossed"] = False
        return
    point = tokenizer["DATA"].get("press-point")
    if point is None:
        derived["drag-threshold-crossed"] = False
        return
    dx, dy = raw["x"] - point["x"], raw["y"] - point["y"]
    derived["drag-threshold-crossed"] = dx * dx + dy * dy >= config["drag-threshold"] ** 2

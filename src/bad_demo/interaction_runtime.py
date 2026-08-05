"""Blackboard-Judge update machine for the BAD-rendered demo."""

import copy

from . import effects_world, event_queue, geometry, judge as judge_module
from . import organisms as organisms_module
from . import projection, tk_runtime, tokenizers as tokenizers_module

g = {}
world = {}
config = {"canvas-width": 980, "canvas-height": 640, "playfield-right": 660,
          "drag-threshold": 8, "click-duration-ms": 350, "handle-half": 6,
          "min-size": 40, "margin": 20, "quantization-step": 20}
raw = {}
raw_prev = {}
derived = {}
derived_prev = {}


def initialize_demo_state():
    """Build the demo world and all interaction-machine registers."""
    world.clear(); world.update({"objects": {
        "alpha": {"id": "alpha", "x": 70, "y": 90, "w": 140, "h": 100, "fill": "#d96c4f", "label": "ALPHA"},
        "bravo": {"id": "bravo", "x": 270, "y": 220, "w": 170, "h": 120, "fill": "#5a7d4d", "label": "BRAVO"},
        "charlie": {"id": "charlie", "x": 180, "y": 410, "w": 210, "h": 90, "fill": "#4e6e81", "label": "CHARLIE"},
    }, "selected-objects": []})
    raw.clear(); raw.update(make_initial_raw())
    raw_prev.clear(); raw_prev.update(copy.deepcopy(raw))
    derived.clear(); derived.update(tokenizers_module.make_initial_derived())
    derived_prev.clear(); derived_prev.update(tokenizers_module.make_initial_derived())
    judge_module.initialize_judge()
    tokenizers_module.initialize_tokenizers()
    organisms_module.initialize_organisms()


def make_initial_raw():
    return {"x": 0, "y": 0, "ms": 0, "inside-canvas": True, "button-1-down": False,
            "mouse-over": None, "keys-down": {}, "widget-values": {}, "show-grid": False,
            "quantization-enabled": False, "quantization-step": config["quantization-step"]}


def run_update_cycle():
    if not event_queue.events:
        event_queue.post_event({"type": "TIME_PASSES", "ms": tk_runtime.now_ms()})
    for event in event_queue.drain_events():
        apply_event_to_runtime(event)


def apply_event_to_runtime(event):
    if event["type"] == "POINTER_MOTION":
        for sample in event["samples"]:
            run_cycle({**sample, "inside-canvas": True})
        return
    update = {"ms": event.get("ms", raw["ms"])}
    if event["type"] == "BUTTON_1_PRESSED": update.update({"x": event["x"], "y": event["y"], "button-1-down": True, "inside-canvas": True})
    elif event["type"] == "BUTTON_1_RELEASED": update.update({"x": event["x"], "y": event["y"], "button-1-down": False, "inside-canvas": True})
    elif event["type"] == "POINTER_LEFT_CANVAS": update.update({"x": event["x"], "y": event["y"], "inside-canvas": False})
    elif event["type"] in ("KEY_PRESSED", "KEY_RELEASED"):
        keys = dict(raw["keys-down"]); keys[event["keysym"]] = event["type"] == "KEY_PRESSED"; update["keys-down"] = keys
    elif event["type"] == "WIDGET_ACTIVATED":
        values = dict(raw["widget-values"]); values[event["widget"]] = event["value"]; update["widget-values"] = values
        if event["widget"] == "show-grid-checkbox": update["show-grid"] = bool(event["value"])
        if event["widget"] == "quantization-checkbox": update["quantization-enabled"] = bool(event["value"])
    elif event["type"] == "TIME_PASSES": pass
    else: raise ValueError(f"Unknown input event: {event['type']}")
    run_cycle(update)


def run_cycle(raw_update):
    raw_prev.clear(); raw_prev.update(copy.deepcopy(raw))
    derived_prev.clear(); derived_prev.update(copy.deepcopy(derived))
    current_raw = dict(raw); current_raw.update(raw_update)
    current_raw["mouse-over"] = geometry.find_object_at(world["objects"], current_raw["x"], current_raw["y"]) if current_raw["inside-canvas"] else None
    raw.clear(); raw.update(current_raw)
    tokenizers_module.run_tokenizers()
    judge_module.maintain_judge()
    organisms_module.evaluate_organisms()
    judge_module.maintain_judge()
    effects_world.route_effects()
    projection.render_projection(world, effects_world.get_current_previews(), config, raw)

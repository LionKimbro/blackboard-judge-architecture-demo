"""Blackboard-Judge update machine for the BAD-rendered demo."""

import copy

from . import effects_world, event_queue, geometry, judge, organisms, projection, tk_runtime, tokenizers


g = {}
world = {}
system = {}

config = {"canvas-width": 980, "canvas-height": 640, "playfield-right": 660,
          "drag-threshold": 8, "handle-half": 6, "min-size": 40, "margin": 20,
          "quantization-step": 20}


def initialize_demo_state():
    """Build the demo world and all interaction-machine registers."""
    world.clear(); world.update({"objects": {
        "alpha": {"id": "alpha", "x": 70, "y": 90, "w": 140, "h": 100, "fill": "#d96c4f", "label": "ALPHA"},
        "bravo": {"id": "bravo", "x": 270, "y": 220, "w": 170, "h": 120, "fill": "#5a7d4d", "label": "BRAVO"},
        "charlie": {"id": "charlie", "x": 180, "y": 410, "w": 210, "h": 90, "fill": "#4e6e81", "label": "CHARLIE"},
    }, "selected-objects": []})
    raw = make_initial_raw()
    system.clear(); system.update({"RAW": raw, "RAW-PREV": copy.deepcopy(raw),
        "DERIVED": tokenizers.make_initial_derived(), "DERIVED-PREV": tokenizers.make_initial_derived(),
        "COORDINATION": {"pointer-owner": None, "active-gesture": None, "resource-holds": {}, "leases": {}, "judge-notes": []},
        "EFFECTS": [], "PREVIEWS": [],
        "TOKENIZERS": [record("pointer-motion", tokenizers.tokenizer_pointer_motion), record("button-1", tokenizers.tokenizer_button_1), record("pointer-target", tokenizers.tokenizer_pointer_target), record("resize-handles", tokenizers.tokenizer_resize_handles), record("drag-threshold", tokenizers.tokenizer_drag_threshold)],
        "ORGANISMS": [record("hover-highlight", organisms.organism_hover_highlight), record("resize-object", organisms.organism_resize_object), record("drag-selection-group", organisms.organism_drag_selection_group), record("drag-object", organisms.organism_drag_object), record("marquee-select", organisms.organism_marquee_select)]})


def record(name, fn):
    return {"NAME": name, "ACTIVE": True, "STATE": organisms.IDLE, "HELD": {}, "DATA": {}, "FN": fn}


def make_initial_raw():
    return {"x": 0, "y": 0, "ms": 0, "inside-canvas": True, "button-1-down": False,
            "mouse-over": None, "keys-down": {}, "widget-values": {}, "quantization-step": config["quantization-step"]}


def run_update_cycle():
    events = event_queue.drain_events()
    if not events:
        run_cycle({"ms": tk_runtime.now_ms()})
        return
    for event in events:
        apply_event_to_runtime(event)


def apply_event_to_runtime(event):
    if event["type"] == "POINTER_MOTION":
        for sample in event["samples"]: run_cycle({**sample, "inside-canvas": True})
        return
    update = {"ms": event.get("ms", system["RAW"]["ms"])}
    if event["type"] == "BUTTON_1_PRESSED": update.update({"x": event["x"], "y": event["y"], "button-1-down": True, "inside-canvas": True})
    elif event["type"] == "BUTTON_1_RELEASED": update.update({"x": event["x"], "y": event["y"], "button-1-down": False, "inside-canvas": True})
    elif event["type"] == "POINTER_LEFT_CANVAS": update.update({"x": event["x"], "y": event["y"], "inside-canvas": False})
    elif event["type"] in ("KEY_PRESSED", "KEY_RELEASED"):
        keys = dict(system["RAW"]["keys-down"]); keys[event["keysym"]] = event["type"] == "KEY_PRESSED"; update["keys-down"] = keys
    elif event["type"] == "WIDGET_ACTIVATED":
        values = dict(system["RAW"]["widget-values"]); values[event["widget"]] = event["value"]; update["widget-values"] = values
    else: raise ValueError(f"Unknown input event: {event['type']}")
    run_cycle(update)


def run_cycle(raw_update):
    system["RAW-PREV"] = copy.deepcopy(system["RAW"]); system["DERIVED-PREV"] = copy.deepcopy(system["DERIVED"])
    raw = dict(system["RAW"]); raw.update(raw_update)
    if raw["inside-canvas"]: raw["mouse-over"] = geometry.find_object_at(world["objects"], raw["x"], raw["y"])
    else: raw["mouse-over"] = None
    system["RAW"] = raw
    tokenizers.run_tokenizers(system, world, config); judge.maintain_judge(system["COORDINATION"], system["ORGANISMS"])
    organisms.evaluate_organisms(system, world, config); judge.maintain_judge(system["COORDINATION"], system["ORGANISMS"])
    system["PREVIEWS"] = effects_world.route_effects(world, system["EFFECTS"], config)
    projection.render_projection(world, system["PREVIEWS"], config, system["RAW"])

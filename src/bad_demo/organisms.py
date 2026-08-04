"""Interaction organisms that turn perceived input into explicit effects."""

from . import effects_world, geometry, judge

IDLE = "IDLE"
ARMED = "ARMED"
DRAGGING = "DRAGGING"
SELECTING = "SELECTING"


def clear_organism(organism):
    organism.update({"STATE": IDLE, "HELD": {}, "DATA": {}})


def evaluate_organisms(system, world, config):
    system["EFFECTS"] = []
    for organism in system["ORGANISMS"]:
        if organism["ACTIVE"]:
            organism["FN"](system, world, config, organism)


def organism_hover_highlight(system, world, config, organism):
    del config
    target = system["DERIVED"]["pointer-target"]
    if target and system["COORDINATION"]["pointer-owner"] is None:
        effects_world.emit_projection_effect(system["EFFECTS"], organism["NAME"], "hover-highlight", {"object-id": target})


def organism_resize_object(system, world, config, organism):
    d, raw = system["DERIVED"], system["RAW"]
    if organism["STATE"] == IDLE and d["button-1-pressed"] and d["pointer-handle-target"]:
        target = d["pointer-handle-target"]
        organism.update({"STATE": ARMED, "HELD": dict(target), "DATA": {"start-rect": dict(world["objects"][target["object-id"]])}})
    elif organism["STATE"] == ARMED and d["button-1-released"]:
        clear_organism(organism)
    elif organism["STATE"] == ARMED and d["drag-threshold-crossed"]:
        if judge.get_permission(system["COORDINATION"], organism["NAME"], judge.COMMIT, ["pointer", organism["HELD"]["object-id"]]):
            organism["STATE"] = DRAGGING
    elif organism["STATE"] == DRAGGING:
        payload = {**organism["HELD"], "start-rect": organism["DATA"]["start-rect"], "x": raw["x"], "y": raw["y"]}
        effects_world.emit_projection_effect(system["EFFECTS"], organism["NAME"], "resize-preview", payload)
        if d["button-1-released"]:
            effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "resize-object", payload)
            clear_organism(organism)


def organism_drag_selection_group(system, world, config, organism):
    d, raw = system["DERIVED"], system["RAW"]
    target = d["pointer-target"]
    selected = world["selected-objects"]
    if organism["STATE"] == IDLE and d["button-1-pressed"] and target in selected and len(selected) > 1 and not d["pointer-handle-target"]:
        organism.update({"STATE": ARMED, "HELD": {"object-ids": list(selected)},
                         "DATA": {"anchor": {"x": raw["x"], "y": raw["y"]}, "start-positions": geometry.snapshot_object_positions(world["objects"], selected)}})
    elif organism["STATE"] == ARMED and d["button-1-released"]:
        clear_organism(organism)
    elif organism["STATE"] == ARMED and d["drag-threshold-crossed"]:
        if judge.get_permission(system["COORDINATION"], organism["NAME"], judge.COMMIT, ["pointer", *organism["HELD"]["object-ids"]]): organism["STATE"] = DRAGGING
    elif organism["STATE"] == DRAGGING:
        dx = geometry.compute_group_delta_bound(world["objects"], organism["DATA"]["start-positions"], raw["x"] - organism["DATA"]["anchor"]["x"], "x", config["playfield-right"], config["canvas-height"], config["margin"])
        dy = geometry.compute_group_delta_bound(world["objects"], organism["DATA"]["start-positions"], raw["y"] - organism["DATA"]["anchor"]["y"], "y", config["playfield-right"], config["canvas-height"], config["margin"])
        payload = {"object-ids": organism["HELD"]["object-ids"], "start-positions": organism["DATA"]["start-positions"], "dx": dx, "dy": dy}
        effects_world.emit_projection_effect(system["EFFECTS"], organism["NAME"], "group-drag-preview", payload)
        if d["button-1-released"]:
            effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "move-group", payload); clear_organism(organism)


def organism_drag_object(system, world, config, organism):
    d, raw = system["DERIVED"], system["RAW"]
    target = d["pointer-target"]
    if organism["STATE"] == IDLE and d["button-1-pressed"] and target and not d["pointer-handle-target"] and len(world["selected-objects"]) <= 1:
        organism.update({"STATE": ARMED, "HELD": {"object-id": target}, "DATA": {"anchor": {"x": raw["x"], "y": raw["y"]}, "start": dict(world["objects"][target])}})
    elif organism["STATE"] == ARMED and d["button-1-released"]:
        effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "set-selection", {"object-ids": [organism["HELD"]["object-id"]]}); clear_organism(organism)
    elif organism["STATE"] == ARMED and d["drag-threshold-crossed"]:
        if judge.get_permission(system["COORDINATION"], organism["NAME"], judge.COMMIT, ["pointer", organism["HELD"]["object-id"]]): organism["STATE"] = DRAGGING
    elif organism["STATE"] == DRAGGING:
        start, anchor = organism["DATA"]["start"], organism["DATA"]["anchor"]
        x = geometry.clamp(start["x"] + raw["x"] - anchor["x"], config["margin"], config["playfield-right"] - start["w"] - config["margin"])
        y = geometry.clamp(start["y"] + raw["y"] - anchor["y"], config["margin"], config["canvas-height"] - start["h"] - config["margin"])
        payload = {"object-id": organism["HELD"]["object-id"], "x": x, "y": y}
        effects_world.emit_projection_effect(system["EFFECTS"], organism["NAME"], "drag-preview", payload)
        if d["button-1-released"]:
            effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "move-object", payload); clear_organism(organism)


def organism_marquee_select(system, world, config, organism):
    d, raw = system["DERIVED"], system["RAW"]
    if organism["STATE"] == IDLE and d["button-1-pressed"] and d["pointer-target"] is None:
        organism.update({"STATE": ARMED, "HELD": {}, "DATA": {"anchor": {"x": raw["x"], "y": raw["y"]}}})
    elif organism["STATE"] == ARMED and d["button-1-released"]:
        effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "set-selection", {"object-ids": []}); clear_organism(organism)
    elif organism["STATE"] == ARMED and d["drag-threshold-crossed"]:
        if judge.get_permission(system["COORDINATION"], organism["NAME"], judge.COMMIT, ["pointer"]): organism["STATE"] = SELECTING
    elif organism["STATE"] == SELECTING:
        rect = geometry.rect_from_points(organism["DATA"]["anchor"], raw)
        payload = {"rect": rect, "object-ids": geometry.list_objects_in_rect(world["objects"], rect)}
        effects_world.emit_projection_effect(system["EFFECTS"], organism["NAME"], "marquee-preview", payload)
        if d["button-1-released"]:
            effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "set-selection", {"object-ids": payload["object-ids"]}); clear_organism(organism)

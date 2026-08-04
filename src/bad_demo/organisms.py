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
    target = system["DERIVED"].get("pointer-draggable-target")
    if target is None:
        return
    if not judge.get_permission(system["COORDINATION"], organism["NAME"], judge.CHECK, ["pointer"]):
        return
    effects_world.emit_projection_effect(system["EFFECTS"], organism["NAME"], "hover-highlight", {"object-id": target})


def organism_select_object_on_click(system, world, config, organism):
    del world, config
    target = system["DERIVED"].get("single-click-draggable-target")
    if target is None:
        return
    if not judge.get_permission(system["COORDINATION"], organism["NAME"], judge.CHECK, ["pointer"]):
        return
    effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "set-selection", {"object-ids": [target]})


def organism_resize_object(system, world, config, organism):
    d, raw = system["DERIVED"], system["RAW"]
    if organism["STATE"] == IDLE:
        target = d.get("pointer-handle-target")
        if not d["button-1-pressed"] or target is None:
            return
        if not judge.get_permission(system["COORDINATION"], organism["NAME"], judge.CHECK, ["pointer"]):
            return
        organism.update({"STATE": ARMED, "HELD": dict(target), "DATA": {"start-rect": dict(world["objects"][target["object-id"]])}})
        return
    if organism["STATE"] == ARMED:
        if d["button-1-released"]:
            clear_organism(organism)
            return
        if not d["drag-threshold-crossed"]:
            return
        if not judge.get_permission(system["COORDINATION"], organism["NAME"], judge.COMMIT, ["pointer", organism["HELD"]["object-id"]]):
            clear_organism(organism)
            return
        organism["STATE"] = DRAGGING
    if organism["STATE"] == DRAGGING:
        payload = {**organism["HELD"], "start-rect": organism["DATA"]["start-rect"], "x": raw["x"], "y": raw["y"]}
        effects_world.emit_projection_effect(system["EFFECTS"], organism["NAME"], "resize-preview", payload)
        if d["button-1-released"]:
            effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "resize-object", payload)
            clear_organism(organism)


def organism_drag_objects(system, world, config, organism):
    d, raw = system["DERIVED"], system["RAW"]
    if organism["STATE"] == IDLE:
        target = d.get("pointer-draggable-target")
        if not d["button-1-pressed"] or target is None:
            return
        if not judge.get_permission(system["COORDINATION"], organism["NAME"], judge.CHECK, ["pointer"]):
            return
        object_ids = list(world["selected-objects"]) if target in world["selected-objects"] else [target]
        organism.update({
            "STATE": ARMED,
            "HELD": {"object-ids": object_ids},
            "DATA": {
                "anchor": {"x": raw["x"], "y": raw["y"]},
                "start-positions": geometry.snapshot_object_positions(world["objects"], object_ids),
                "start-geometry": {object_id: dict(world["objects"][object_id]) for object_id in object_ids},
            },
        })
        return
    if organism["STATE"] == ARMED:
        if d["button-1-released"]:
            clear_organism(organism)
            return
        if not d["drag-threshold-crossed"]:
            return
        object_ids = organism["HELD"]["object-ids"]
        if not judge.get_permission(system["COORDINATION"], organism["NAME"], judge.COMMIT, ["pointer", *object_ids]):
            clear_organism(organism)
            return
        effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "set-selection", {"object-ids": object_ids})
        organism["STATE"] = DRAGGING
    if organism["STATE"] == DRAGGING:
        start_positions, anchor = organism["DATA"]["start-positions"], organism["DATA"]["anchor"]
        dx = geometry.compute_group_delta_bound(world["objects"], start_positions, raw["x"] - anchor["x"], "x", config["playfield-right"], config["canvas-height"], config["margin"])
        dy = geometry.compute_group_delta_bound(world["objects"], start_positions, raw["y"] - anchor["y"], "y", config["playfield-right"], config["canvas-height"], config["margin"])
        positions = {object_id: {"x": start["x"] + dx, "y": start["y"] + dy} for object_id, start in start_positions.items()}
        payload = {"object-ids": organism["HELD"]["object-ids"], "start-positions": start_positions, "positions": positions, "dx": dx, "dy": dy}
        effects_world.emit_projection_effect(system["EFFECTS"], organism["NAME"], "drag-preview", payload)
        if d["button-1-released"]:
            effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "move-objects", payload)
            clear_organism(organism)


def organism_marquee_select(system, world, config, organism):
    d, raw = system["DERIVED"], system["RAW"]
    if organism["STATE"] == IDLE:
        if not d["button-1-pressed"] or d["pointer-target"] is not None:
            return
        if not judge.get_permission(system["COORDINATION"], organism["NAME"], judge.CHECK, ["pointer"]):
            return
        organism.update({"STATE": ARMED, "HELD": {}, "DATA": {"anchor": {"x": raw["x"], "y": raw["y"]}}})
        return
    if organism["STATE"] == ARMED:
        if d["button-1-released"]:
            effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "set-selection", {"object-ids": []})
            clear_organism(organism)
            return
        if not d["drag-threshold-crossed"]:
            return
        if not judge.get_permission(system["COORDINATION"], organism["NAME"], judge.COMMIT, ["pointer"]):
            clear_organism(organism)
            return
        organism["STATE"] = SELECTING
    if organism["STATE"] == SELECTING:
        rect = geometry.rect_from_points(organism["DATA"]["anchor"], raw)
        payload = {"rect": rect, "object-ids": geometry.list_objects_in_rect(world["objects"], rect)}
        effects_world.emit_projection_effect(system["EFFECTS"], organism["NAME"], "marquee-preview", payload)
        if d["button-1-released"]:
            effects_world.emit_world_effect(system["EFFECTS"], organism["NAME"], "set-selection", {"object-ids": payload["object-ids"]})
            clear_organism(organism)

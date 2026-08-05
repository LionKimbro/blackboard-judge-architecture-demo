"""Interaction organisms that turn perceived input into explicit effects."""

from . import effects_world, geometry, interaction_runtime, judge

IDLE = "IDLE"
ARMED = "ARMED"
DRAGGING = "DRAGGING"
SELECTING = "SELECTING"

organisms = []


def initialize_organisms():
    organisms.clear()
    organisms.extend([
        make_organism_record("hover-highlight", organism_hover_highlight),
        make_organism_record("select-object-on-click", organism_select_object_on_click),
        make_organism_record("resize-object", organism_resize_object),
        make_organism_record("drag-objects", organism_drag_objects),
        make_organism_record("marquee-select", organism_marquee_select),
    ])


def make_organism_record(name, fn):
    return {"NAME": name, "ACTIVE": True, "STATE": IDLE, "HELD": {}, "DATA": {}, "FN": fn}


def clear_organism(organism):
    organism.update({"STATE": IDLE, "HELD": {}, "DATA": {}})


def evaluate_organisms():
    effects_world.clear_effects()
    for organism in organisms:
        if organism["ACTIVE"]:
            organism["FN"](organism)


def get_active_organism_names():
    return {organism["NAME"] for organism in organisms if organism["STATE"] != IDLE}


def organism_hover_highlight(organism):
    target = interaction_runtime.derived.get("pointer-draggable-target")
    if target is None:
        return
    if not judge.get_permission(organism["NAME"], judge.CHECK, ["pointer"]):
        return
    effects_world.emit_projection_effect({"source": organism["NAME"], "name": "hover-highlight", "payload": {"object-id": target}})


def organism_select_object_on_click(organism):
    target = interaction_runtime.derived.get("single-click-draggable-target")
    if target is None:
        return
    if not judge.get_permission(organism["NAME"], judge.CHECK, ["pointer"]):
        return
    effects_world.emit_world_effect({"source": organism["NAME"], "name": "set-selection", "payload": {"object-ids": [target]}})


def organism_resize_object(organism):
    if organism["STATE"] == IDLE:
        target = interaction_runtime.derived.get("pointer-handle-target")
        if not interaction_runtime.derived["button-1-pressed"] or target is None:
            return
        if not judge.get_permission(organism["NAME"], judge.CHECK, ["pointer"]):
            return
        organism.update({"STATE": ARMED, "HELD": dict(target), "DATA": {"start-rect": dict(interaction_runtime.world["objects"][target["object-id"]])}})
        return
    if organism["STATE"] == ARMED:
        if interaction_runtime.derived["button-1-released"]:
            clear_organism(organism)
            return
        if not interaction_runtime.derived["drag-threshold-crossed"]:
            return
        if not judge.get_permission(organism["NAME"], judge.COMMIT, ["pointer", organism["HELD"]["object-id"]]):
            clear_organism(organism)
            return
        organism["STATE"] = DRAGGING
    if organism["STATE"] == DRAGGING:
        rect = geometry.make_resize_rectangle(organism["DATA"]["start-rect"], organism["HELD"]["handle"], interaction_runtime.raw["x"], interaction_runtime.raw["y"], interaction_runtime.config, interaction_runtime.raw["quantization-enabled"])
        payload = {"object-id": organism["HELD"]["object-id"], "rect": rect}
        effects_world.emit_projection_effect({"source": organism["NAME"], "name": "resize-preview", "payload": payload})
        if interaction_runtime.derived["button-1-released"]:
            effects_world.emit_world_effect({"source": organism["NAME"], "name": "resize-object", "payload": payload})
            clear_organism(organism)


def organism_drag_objects(organism):
    if organism["STATE"] == IDLE:
        target = interaction_runtime.derived.get("pointer-draggable-target")
        if not interaction_runtime.derived["button-1-pressed"] or target is None:
            return
        if not judge.get_permission(organism["NAME"], judge.CHECK, ["pointer"]):
            return
        object_ids = list(interaction_runtime.world["selected-objects"]) if target in interaction_runtime.world["selected-objects"] else [target]
        organism.update({"STATE": ARMED, "HELD": {"object-ids": object_ids}, "DATA": {"anchor": {"x": interaction_runtime.raw["x"], "y": interaction_runtime.raw["y"]}, "start-positions": geometry.snapshot_object_positions(interaction_runtime.world["objects"], object_ids), "start-geometry": {object_id: dict(interaction_runtime.world["objects"][object_id]) for object_id in object_ids}}})
        return
    if organism["STATE"] == ARMED:
        if interaction_runtime.derived["button-1-released"]:
            clear_organism(organism)
            return
        if not interaction_runtime.derived["drag-threshold-crossed"]:
            return
        object_ids = organism["HELD"]["object-ids"]
        if not judge.get_permission(organism["NAME"], judge.COMMIT, ["pointer", *object_ids]):
            clear_organism(organism)
            return
        effects_world.emit_world_effect({"source": organism["NAME"], "name": "set-selection", "payload": {"object-ids": object_ids}})
        organism["STATE"] = DRAGGING
    if organism["STATE"] == DRAGGING:
        start_positions, anchor = organism["DATA"]["start-positions"], organism["DATA"]["anchor"]
        positions = geometry.make_drag_positions(interaction_runtime.world["objects"], start_positions, interaction_runtime.raw["x"] - anchor["x"], interaction_runtime.raw["y"] - anchor["y"], interaction_runtime.config, interaction_runtime.raw["quantization-enabled"])
        payload = {"object-ids": organism["HELD"]["object-ids"], "positions": positions}
        effects_world.emit_projection_effect({"source": organism["NAME"], "name": "drag-preview", "payload": payload})
        if interaction_runtime.derived["button-1-released"]:
            effects_world.emit_world_effect({"source": organism["NAME"], "name": "move-objects", "payload": payload})
            clear_organism(organism)


def organism_marquee_select(organism):
    if organism["STATE"] == IDLE:
        if not interaction_runtime.derived["button-1-pressed"] or interaction_runtime.derived["pointer-target"] is not None:
            return
        if not judge.get_permission(organism["NAME"], judge.CHECK, ["pointer"]):
            return
        organism.update({"STATE": ARMED, "HELD": {}, "DATA": {"anchor": {"x": interaction_runtime.raw["x"], "y": interaction_runtime.raw["y"]}}})
        return
    if organism["STATE"] == ARMED:
        if interaction_runtime.derived["button-1-released"]:
            effects_world.emit_world_effect({"source": organism["NAME"], "name": "set-selection", "payload": {"object-ids": []}})
            clear_organism(organism)
            return
        if not interaction_runtime.derived["drag-threshold-crossed"]:
            return
        if not judge.get_permission(organism["NAME"], judge.COMMIT, ["pointer"]):
            clear_organism(organism)
            return
        organism["STATE"] = SELECTING
    if organism["STATE"] == SELECTING:
        rect = geometry.rect_from_points(organism["DATA"]["anchor"], interaction_runtime.raw)
        payload = {"rect": rect, "object-ids": geometry.list_objects_in_rect(interaction_runtime.world["objects"], rect)}
        effects_world.emit_projection_effect({"source": organism["NAME"], "name": "marquee-preview", "payload": payload})
        if interaction_runtime.derived["button-1-released"]:
            effects_world.emit_world_effect({"source": organism["NAME"], "name": "set-selection", "payload": {"object-ids": payload["object-ids"]}})
            clear_organism(organism)

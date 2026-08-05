"""Effect construction, routing, and the only writes to durable world state."""

from . import interaction_runtime

WORLD_MUTATION = "WORLD_MUTATION"
PROJECTION_PREVIEW = "PROJECTION_PREVIEW"

effects = []
previews = []


def clear_effects():
    effects.clear()


def emit_world_effect(effect):
    effects.append({"kind": WORLD_MUTATION, **effect})


def emit_projection_effect(effect):
    effects.append({"kind": PROJECTION_PREVIEW, **effect})


def route_effects():
    previews.clear()
    for effect in effects:
        if effect["kind"] == PROJECTION_PREVIEW:
            previews.append(effect)
        elif effect["kind"] == WORLD_MUTATION:
            apply_world_effect(effect)
        else:
            raise ValueError(f"Unknown effect kind: {effect['kind']}")


def get_current_previews():
    return previews


def apply_world_effect(effect):
    payload = effect["payload"]
    if effect["name"] == "set-selection":
        interaction_runtime.world["selected-objects"] = list(payload["object-ids"])
    elif effect["name"] == "move-objects":
        if not is_positions_lawful(payload["positions"]):
            raise ValueError("Move proposal is outside lawful playfield bounds")
        for object_id, position in payload["positions"].items():
            interaction_runtime.world["objects"][object_id].update(position)
    elif effect["name"] == "resize-object":
        if not is_rectangle_lawful(payload["rect"]):
            raise ValueError("Resize proposal is outside lawful bounds")
        interaction_runtime.world["objects"][payload["object-id"]].update(payload["rect"])
    else:
        raise ValueError(f"Unknown world effect: {effect['name']}")


def is_positions_lawful(positions):
    for object_id, position in positions.items():
        obj = interaction_runtime.world["objects"].get(object_id)
        if obj is None:
            return False
        if not interaction_runtime.config["margin"] <= position["x"] <= interaction_runtime.config["playfield-right"] - obj["w"] - interaction_runtime.config["margin"]:
            return False
        if not interaction_runtime.config["margin"] <= position["y"] <= interaction_runtime.config["canvas-height"] - obj["h"] - interaction_runtime.config["margin"]:
            return False
    return True


def is_rectangle_lawful(rect):
    return (rect["w"] >= interaction_runtime.config["min-size"] and rect["h"] >= interaction_runtime.config["min-size"]
            and rect["x"] >= interaction_runtime.config["margin"] and rect["y"] >= interaction_runtime.config["margin"]
            and rect["x"] + rect["w"] <= interaction_runtime.config["playfield-right"] - interaction_runtime.config["margin"]
            and rect["y"] + rect["h"] <= interaction_runtime.config["canvas-height"] - interaction_runtime.config["margin"])

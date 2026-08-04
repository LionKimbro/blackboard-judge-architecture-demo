"""Effect construction, routing, and the only writes to durable world state."""

from . import geometry

WORLD_MUTATION = "WORLD_MUTATION"
PROJECTION_PREVIEW = "PROJECTION_PREVIEW"


def emit_world_effect(effects, source, name, payload):
    effects.append({"kind": WORLD_MUTATION, "source": source, "name": name, "payload": payload})


def emit_projection_effect(effects, source, name, payload):
    effects.append({"kind": PROJECTION_PREVIEW, "source": source, "name": name, "payload": payload})


def route_effects(world, effects, config):
    """Apply world effects in emission order and return current-frame previews."""
    previews = []
    for effect in effects:
        if effect["kind"] == PROJECTION_PREVIEW:
            previews.append(effect)
        elif effect["kind"] == WORLD_MUTATION:
            apply_world_effect(world, effect, config)
        else:
            raise ValueError(f"Unknown effect kind: {effect['kind']}")
    return previews


def apply_world_effect(world, effect, config):
    payload = effect["payload"]
    if effect["name"] == "set-selection":
        world["selected-objects"] = list(payload["object-ids"])
    elif effect["name"] == "move-objects":
        for object_id, start in payload["start-positions"].items():
            world["objects"][object_id]["x"] = start["x"] + payload["dx"]
            world["objects"][object_id]["y"] = start["y"] + payload["dy"]
    elif effect["name"] == "resize-object":
        obj = world["objects"][payload["object-id"]]
        rect = geometry.compute_resized_rect(payload["start-rect"], payload["handle"], payload["x"], payload["y"],
                                             config["playfield-right"], config["canvas-height"], config["min-size"], config["margin"])
        obj.update(rect)
    else:
        raise ValueError(f"Unknown world effect: {effect['name']}")

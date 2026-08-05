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
        if not geometry.positions_are_lawful(world["objects"], payload["positions"], config):
            raise ValueError("Move proposal is outside lawful playfield bounds")
        for object_id, position in payload["positions"].items():
            world["objects"][object_id].update(position)
    elif effect["name"] == "resize-object":
        if not geometry.rectangle_is_lawful(payload["rect"], config):
            raise ValueError("Resize proposal is outside lawful bounds")
        world["objects"][payload["object-id"]].update(payload["rect"])
    else:
        raise ValueError(f"Unknown world effect: {effect['name']}")

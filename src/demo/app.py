"""Tkinter canvas demo of the blackboard-judge interaction architecture.

This program demonstrates a tiny interactive ecology:
- tokenizers derive shared perceptual facts from raw pointer/button input
- organisms recognize local interaction episodes over time
- a judge authoritatively manages coordination and resource ownership
- effects are routed separately into world mutation and projection preview
"""

from __future__ import annotations

import copy
import time
import tkinter as tk


IDLE = "IDLE"
ARMED = "ARMED"
DRAGGING = "DRAGGING"
SELECTING = "SELECTING"

START = "START"
HOLD_RESOURCE = "HOLD-RESOURCE"

WORLD_MUTATION = "WORLD-MUTATION"
PROJECTION_PREVIEW = "PROJECTION-PREVIEW"

CANVAS_W = 980
CANVAS_H = 640
PANEL_X = 660
DRAG_THRESHOLD = 8
HANDLE_HALF = 6
MIN_SIZE = 40
TICK_MS = 100

g = {}
world = {}
system = {}


def main():
    """Build the UI, initialize the interaction system, and enter Tk."""
    build_app()
    reset_demo_state()
    render_projection()
    schedule_periodic_tick()
    g["root"].mainloop()


def build_app():
    """Create the root window and canvas, and bind raw-input callbacks."""
    g["root"] = tk.Tk()
    g["root"].title("Interaction Architecture Blackboard-Judge Demo")
    g["quantization-var"] = tk.BooleanVar(value=False)
    g["canvas"] = tk.Canvas(
        g["root"],
        width=CANVAS_W,
        height=CANVAS_H,
        bg="#f6f2e8",
        highlightthickness=0,
    )
    g["canvas"].grid(row=0, column=0, sticky="nsew")
    g["quantization-checkbox"] = tk.Checkbutton(
        g["root"],
        text="Quantize To Grid",
        variable=g["quantization-var"],
        command=handle_quantization_toggle,
        anchor="w",
    )
    g["quantization-checkbox"].grid(row=1, column=0, sticky="w", padx=12, pady=(6, 10))

    g["root"].grid_columnconfigure(0, weight=1)
    g["root"].grid_rowconfigure(0, weight=1)

    g["canvas"].bind("<Motion>", handle_pointer_motion)
    g["canvas"].bind("<ButtonPress-1>", handle_button_1_press)
    g["canvas"].bind("<ButtonRelease-1>", handle_button_1_release)
    g["canvas"].bind("<Leave>", handle_pointer_leave_canvas)
    g["root"].bind("<Escape>", handle_escape_reset)
    g["root"].bind("r", handle_escape_reset)


def reset_demo_state(event=None):
    """Initialize a tiny world and the blackboard-judge system state."""
    del event

    world.clear()
    world.update(
        {
            "objects": {
                "alpha": {
                    "id": "alpha",
                    "x": 70,
                    "y": 90,
                    "w": 140,
                    "h": 100,
                    "fill": "#d96c4f",
                    "label": "ALPHA",
                },
                "bravo": {
                    "id": "bravo",
                    "x": 270,
                    "y": 220,
                    "w": 170,
                    "h": 120,
                    "fill": "#5a7d4d",
                    "label": "BRAVO",
                },
                "charlie": {
                    "id": "charlie",
                    "x": 180,
                    "y": 410,
                    "w": 210,
                    "h": 90,
                    "fill": "#4e6e81",
                    "label": "CHARLIE",
                },
            },
            "selected-objects": [],
        }
    )

    system.clear()
    system.update(
        {
            "RAW": make_initial_raw(),
            "RAW-PREV": make_initial_raw(),
            "DERIVED": make_initial_derived(),
            "DERIVED-PREV": make_initial_derived(),
            "COORDINATION": {
                "pointer-owner": None,
                "active-gesture": None,
                "resource-holds": {},
                "leases": {},
                "hover-target": None,
                "judge-notes": [],
            },
            "EFFECTS": [],
            "CURRENT-ORGANISM": None,
            "TOKENIZERS": [
                {"NAME": "pointer-motion", "ACTIVE": True, "DATA": {}, "FN": tokenizer_pointer_motion},
                {"NAME": "button-1-transitions", "ACTIVE": True, "DATA": {}, "FN": tokenizer_button_1},
                {"NAME": "pointer-target", "ACTIVE": True, "DATA": {}, "FN": tokenizer_pointer_target},
                {"NAME": "resize-handles", "ACTIVE": True, "DATA": {}, "FN": tokenizer_resize_handles},
                {"NAME": "drag-threshold", "ACTIVE": True, "DATA": {}, "FN": tokenizer_drag_threshold},
            ],
            "ORGANISMS": [
                {
                    "NAME": "hover-highlight",
                    "ACTIVE": True,
                    "STATE": IDLE,
                    "HELD": {},
                    "DATA": {},
                    "FN": organism_hover_highlight,
                },
                {
                    "NAME": "resize-object",
                    "ACTIVE": True,
                    "STATE": IDLE,
                    "HELD": {},
                    "DATA": {},
                    "FN": organism_resize_object,
                },
                {
                    "NAME": "drag-object",
                    "ACTIVE": True,
                    "STATE": IDLE,
                    "HELD": {},
                    "DATA": {},
                    "FN": organism_drag_object,
                },
                {
                    "NAME": "marquee-select",
                    "ACTIVE": True,
                    "STATE": IDLE,
                    "HELD": {},
                    "DATA": {},
                    "FN": organism_marquee_select,
                },
                {
                    "NAME": "drag-selection-group",
                    "ACTIVE": True,
                    "STATE": IDLE,
                    "HELD": {},
                    "DATA": {},
                    "FN": organism_drag_selection_group,
                },
            ],
        }
    )


def make_initial_raw():
    """Return the canonical internal raw-input snapshot."""
    return {
        "x": 0,
        "y": 0,
        "ms": now_ms(),
        "inside-canvas": True,
        "button-1-down": False,
        "mouse-over": None,
        "quantization-enabled": False,
        "quantization-step": 20,
    }


def make_initial_derived():
    """Return the canonical internal derived perceptual field."""
    return {
        "moving": False,
        "dx": 0,
        "dy": 0,
        "motionless-duration": 0,
        "button-1-pressed": False,
        "button-1-released": False,
        "entered-target": None,
        "left-target": None,
        "drag-threshold-crossed": False,
        "pointer-target": None,
        "pointer-handle-target": None,
    }


def handle_pointer_motion(event):
    """Normalize pointer motion into RAW and run one interaction cycle."""
    run_cycle(
        {
            "x": event.x,
            "y": event.y,
            "inside-canvas": True,
            "button-1-down": system["RAW"]["button-1-down"],
            "mouse-over": find_object_at(event.x, event.y),
        }
    )


def handle_button_1_press(event):
    """Normalize button press into RAW and run one interaction cycle."""
    run_cycle(
        {
            "x": event.x,
            "y": event.y,
            "inside-canvas": True,
            "button-1-down": True,
            "mouse-over": find_object_at(event.x, event.y),
        }
    )


def handle_button_1_release(event):
    """Normalize button release into RAW and run one interaction cycle."""
    run_cycle(
        {
            "x": event.x,
            "y": event.y,
            "inside-canvas": True,
            "button-1-down": False,
            "mouse-over": find_object_at(event.x, event.y),
        }
    )


def handle_pointer_leave_canvas(event):
    """Mark the pointer as outside the canvas and process the change."""
    run_cycle(
        {
            "x": event.x,
            "y": event.y,
            "inside-canvas": False,
            "button-1-down": system["RAW"]["button-1-down"],
            "mouse-over": None,
        }
    )


def handle_escape_reset(event):
    """Reset the world and redraw the demo."""
    del event
    reset_demo_state()
    render_projection()


def handle_quantization_toggle():
    """Project checkbox state into RAW and redraw immediately."""
    run_cycle({}, render=True)


def run_cycle(raw_update, render=True):
    """Advance the architecture one cycle from raw input to projection."""
    preserve_previous_snapshots()
    populate_raw(raw_update)
    run_tokenizers()
    maintain_judge()
    evaluate_organisms()
    maintain_judge()
    route_effects()
    if render:
        render_projection()


def preserve_previous_snapshots():
    """Freeze prior RAW and DERIVED so tokenizers can work temporally."""
    system["RAW-PREV"] = copy.deepcopy(system["RAW"])
    system["DERIVED-PREV"] = copy.deepcopy(system["DERIVED"])


def populate_raw(raw_update):
    """Install a normalized raw-input snapshot for the current cycle."""
    snapshot = dict(system["RAW"])
    snapshot.update(raw_update)
    snapshot["ms"] = now_ms()
    if "quantization-enabled" not in raw_update:
        snapshot["quantization-enabled"] = current_quantization_enabled()
    if snapshot["inside-canvas"]:
        snapshot["mouse-over"] = find_object_at(snapshot["x"], snapshot["y"])
    else:
        snapshot["mouse-over"] = None
    system["RAW"] = snapshot


def schedule_periodic_tick():
    """Keep the architecture advancing even when no Tk input arrives."""
    g["root"].after(TICK_MS, handle_periodic_tick)


def handle_periodic_tick():
    """Run one idle cycle so time-based organisms can progress."""
    run_cycle({})
    schedule_periodic_tick()


def now_ms():
    """Return a monotonic millisecond clock for temporal interaction logic."""
    return int(time.monotonic() * 1000)


def current_quantization_enabled():
    """Read quantization state from the UI when present, else from RAW."""
    if "quantization-var" in g:
        return bool(g["quantization-var"].get())
    if system:
        return bool(system["RAW"]["quantization-enabled"])
    return False


def run_tokenizers():
    """Refresh DERIVED and let each tokenizer write shared perceptual facts."""
    system["DERIVED"] = make_initial_derived()
    system["DERIVED"]["pointer-target"] = system["RAW"]["mouse-over"]
    for tokenizer in system["TOKENIZERS"]:
        if tokenizer["ACTIVE"]:
            tokenizer["FN"](tokenizer)


def tokenizer_pointer_motion(tokenizer):
    """Compute pointer delta, movement, and motionless duration."""
    raw = system["RAW"]
    prev = system["RAW-PREV"]
    derived = system["DERIVED"]

    dx = raw["x"] - prev["x"]
    dy = raw["y"] - prev["y"]
    moved = (dx != 0) or (dy != 0)

    derived["dx"] = dx
    derived["dy"] = dy
    derived["moving"] = moved

    if moved:
        tokenizer["DATA"]["last-motion-ms"] = raw["ms"]
        derived["motionless-duration"] = 0
        return

    last_motion_ms = tokenizer["DATA"].get("last-motion-ms", raw["ms"])
    derived["motionless-duration"] = max(0, raw["ms"] - last_motion_ms)


def tokenizer_button_1(tokenizer):
    """Derive just-pressed and just-released from button state changes."""
    del tokenizer
    raw = system["RAW"]
    prev = system["RAW-PREV"]
    derived = system["DERIVED"]

    derived["button-1-pressed"] = raw["button-1-down"] and not prev["button-1-down"]
    derived["button-1-released"] = prev["button-1-down"] and not raw["button-1-down"]


def tokenizer_pointer_target(tokenizer):
    """Derive entered-target and left-target from hit-testing changes."""
    del tokenizer
    raw = system["RAW"]
    prev = system["RAW-PREV"]
    derived = system["DERIVED"]

    derived["pointer-target"] = raw["mouse-over"]
    if raw["mouse-over"] != prev["mouse-over"]:
        derived["entered-target"] = raw["mouse-over"]
        derived["left-target"] = prev["mouse-over"]


def tokenizer_resize_handles(tokenizer):
    """Derive whether the pointer is over a visible resize handle."""
    del tokenizer
    if not system["RAW"]["inside-canvas"]:
        system["DERIVED"]["pointer-handle-target"] = None
        return

    system["DERIVED"]["pointer-handle-target"] = find_resize_handle_at(
        system["RAW"]["x"],
        system["RAW"]["y"],
    )


def tokenizer_drag_threshold(tokenizer):
    """Derive when the pointer has moved far enough for dragging to count."""
    derived = system["DERIVED"]
    if derived["button-1-pressed"]:
        tokenizer["DATA"]["press-point"] = {"x": system["RAW"]["x"], "y": system["RAW"]["y"]}
        tokenizer["DATA"]["crossed"] = False

    if derived["button-1-released"]:
        tokenizer["DATA"]["press-point"] = None
        tokenizer["DATA"]["crossed"] = False
        derived["drag-threshold-crossed"] = False
        return

    anchor = tokenizer["DATA"].get("press-point")
    if not anchor or not system["RAW"]["button-1-down"]:
        tokenizer["DATA"]["crossed"] = False
        derived["drag-threshold-crossed"] = False
        return

    dx = system["RAW"]["x"] - anchor["x"]
    dy = system["RAW"]["y"] - anchor["y"]
    crossed = (dx * dx + dy * dy) >= (DRAG_THRESHOLD * DRAG_THRESHOLD)
    tokenizer["DATA"]["crossed"] = crossed
    derived["drag-threshold-crossed"] = crossed


def maintain_judge():
    """Reconcile coordination state against world and organism public state."""
    coordination = system["COORDINATION"]
    coordination["judge-notes"] = []

    resize = find_organism("resize-object")
    drag = find_organism("drag-object")
    marquee = find_organism("marquee-select")
    drag_group = find_organism("drag-selection-group")
    hover = find_organism("hover-highlight")
    resize_object = resize["HELD"].get("object-id")
    held_object = drag["HELD"].get("object-id")
    held_group = drag_group["HELD"].get("object-ids", [])
    resize_lease = coordination["leases"].get("resize-object")
    lease = coordination["leases"].get("drag-object")
    marquee_lease = coordination["leases"].get("marquee-select")
    group_lease = coordination["leases"].get("drag-selection-group")
    coordination["hover-target"] = hover["HELD"].get("object-id")

    if resize["STATE"] == DRAGGING and resize_object and resize_object in world["objects"]:
        set_exclusive_coordination("resize-object", resize_object)
        return

    if drag_group["STATE"] == DRAGGING and held_group:
        set_exclusive_coordination("drag-selection-group", list(held_group))
        return

    if drag["STATE"] == DRAGGING and held_object and held_object in world["objects"]:
        set_exclusive_coordination("drag-object", held_object)
        return

    if marquee["STATE"] == SELECTING:
        set_pointer_coordination("marquee-select", "pointer")
        return

    if lease:
        coordination["judge-notes"].append("released stale drag lease")
    if resize_lease:
        coordination["judge-notes"].append("released stale resize lease")
    if group_lease:
        coordination["judge-notes"].append("released stale group-drag lease")
    if marquee_lease:
        coordination["judge-notes"].append("released stale marquee lease")

    clear_coordination_claims()


def may_claim_pointer(organism_name, denial_note="denied START: pointer already owned"):
    """Check whether an organism may claim pointer ownership right now."""
    coordination = system["COORDINATION"]
    if coordination["pointer-owner"] in (None, organism_name):
        return True
    coordination["judge-notes"].append(denial_note)
    return False


def are_any_resources_held(resource_ids):
    """Return true when any resource in the list is already authoritatively held."""
    coordination = system["COORDINATION"]
    for resource_id in resource_ids:
        if resource_id in coordination["resource-holds"]:
            return True
    return False


def set_pointer_coordination(owner, resource):
    """Write an exclusive pointer claim with no object resource holds."""
    coordination = system["COORDINATION"]
    coordination["pointer-owner"] = owner
    coordination["active-gesture"] = owner
    coordination["resource-holds"] = {}
    coordination["leases"] = {
        owner: {
            "resource": resource,
            "kind": "exclusive",
            "valid": True,
        }
    }


def set_exclusive_coordination(owner, resource):
    """Write exclusive coordination for one object or a bundle of objects."""
    coordination = system["COORDINATION"]
    coordination["pointer-owner"] = owner
    coordination["active-gesture"] = owner
    if isinstance(resource, list):
        coordination["resource-holds"] = {resource_id: owner for resource_id in resource}
    else:
        coordination["resource-holds"] = {resource: owner}
    coordination["leases"] = {
        owner: {
            "resource": resource,
            "kind": "exclusive",
            "valid": True,
        }
    }


def clear_coordination_claims():
    """Clear active pointer ownership, gesture, and resource leases."""
    coordination = system["COORDINATION"]
    coordination["pointer-owner"] = None
    coordination["active-gesture"] = None
    coordination["resource-holds"] = {}
    coordination["leases"] = {}


def evaluate_organisms():
    """Let each organism read shared state, petition law, and emit effects."""
    system["EFFECTS"] = []
    for organism in system["ORGANISMS"]:
        if not organism["ACTIVE"]:
            continue
        system["CURRENT-ORGANISM"] = organism["NAME"]
        organism["FN"](organism)
    system["CURRENT-ORGANISM"] = None


def organism_hover_highlight(organism):
    """Emit preview highlight when hover is lawful and pointer is free."""
    target = system["DERIVED"]["pointer-target"]
    coordination = system["COORDINATION"]

    if coordination["pointer-owner"] not in (None, "hover-highlight"):
        organism["STATE"] = IDLE
        organism["HELD"] = {}
        return

    if target and system["RAW"]["inside-canvas"]:
        organism["STATE"] = IDLE
        organism["HELD"] = {"object-id": target}
        emit_projection_effect("hover-highlight", "hover-outline", {"object-id": target})
        return

    organism["STATE"] = IDLE
    organism["HELD"] = {}


def organism_drag_object(organism):
    """Recognize press-drag-release over an object and move it lawfully."""
    if organism["STATE"] == IDLE:
        handle_drag_idle_state(organism)
        return

    if organism["STATE"] == ARMED:
        handle_drag_armed_state(organism)
        return

    if organism["STATE"] == DRAGGING:
        handle_dragging_state(organism)
        return

    organism["STATE"] = IDLE
    organism["HELD"] = {}
    organism["DATA"] = {}


def organism_resize_object(organism):
    """Recognize press-drag-release on a visible resize handle."""
    if organism["STATE"] == IDLE:
        handle_resize_idle_state(organism)
        return

    if organism["STATE"] == ARMED:
        handle_resize_armed_state(organism)
        return

    if organism["STATE"] == DRAGGING:
        handle_resize_dragging_state(organism)
        return

    clear_organism(organism)


def organism_marquee_select(organism):
    """Recognize drag-selection beginning from empty space."""
    if organism["STATE"] == IDLE:
        handle_marquee_idle_state(organism)
        return

    if organism["STATE"] == ARMED:
        handle_marquee_armed_state(organism)
        return

    if organism["STATE"] == SELECTING:
        handle_marquee_selecting_state(organism)
        return

    clear_organism(organism)


def organism_drag_selection_group(organism):
    """Recognize dragging of the current selected object group."""
    if organism["STATE"] == IDLE:
        handle_group_drag_idle_state(organism)
        return

    if organism["STATE"] == ARMED:
        handle_group_drag_armed_state(organism)
        return

    if organism["STATE"] == DRAGGING:
        handle_group_dragging_state(organism)
        return

    clear_organism(organism)


def handle_drag_idle_state(organism):
    """Begin an armed drag candidate when press occurs over an object."""
    derived = system["DERIVED"]
    target = derived["pointer-target"]
    if not derived["button-1-pressed"] or not target:
        return
    if derived["pointer-handle-target"] is not None:
        return
    if target in world["selected-objects"]:
        return

    organism["HELD"] = {"object-id": target}
    if not get_permission(START):
        clear_organism(organism)
        return

    emit_world_effect("drag-object", "set-selection", {"object-ids": [target]})

    obj = world["objects"][target]
    organism["STATE"] = ARMED
    organism["DATA"] = {
        "press-point": {"x": system["RAW"]["x"], "y": system["RAW"]["y"]},
        "grab-offset": {
            "x": system["RAW"]["x"] - obj["x"],
            "y": system["RAW"]["y"] - obj["y"],
        },
    }


def handle_drag_armed_state(organism):
    """Convert an armed press into a real drag or abandon it on release."""
    derived = system["DERIVED"]

    if derived["button-1-released"]:
        emit_world_effect(
            "drag-object",
            "set-selection",
            {"object-ids": [organism["HELD"]["object-id"]]},
        )
        clear_organism(organism)
        return

    if not derived["drag-threshold-crossed"]:
        return

    if not get_permission(HOLD_RESOURCE):
        clear_organism(organism)
        return

    organism["STATE"] = DRAGGING


def handle_dragging_state(organism):
    """During drag, emit world movement and preview effects until release."""
    held_object = organism["HELD"]["object-id"]
    grab = organism["DATA"]["grab-offset"]

    emit_world_effect(
        "drag-object",
        "move-object",
        {
            "object-id": held_object,
            "x": system["RAW"]["x"] - grab["x"],
            "y": system["RAW"]["y"] - grab["y"],
        },
    )
    emit_projection_effect(
        "drag-object",
        "drag-anchor",
        {
            "object-id": held_object,
            "pointer-x": system["RAW"]["x"],
            "pointer-y": system["RAW"]["y"],
        },
    )

    if system["DERIVED"]["button-1-released"]:
        clear_organism(organism)


def handle_resize_idle_state(organism):
    """Arm a resize episode when button 1 is pressed on a resize handle."""
    derived = system["DERIVED"]
    target = derived["pointer-handle-target"]
    if not derived["button-1-pressed"] or not target:
        return

    organism["HELD"] = {"object-id": target["object-id"], "handle": target["handle"]}
    if not get_permission(START):
        clear_organism(organism)
        return

    obj = world["objects"][target["object-id"]]
    organism["STATE"] = ARMED
    organism["DATA"] = {
        "press-point": {"x": system["RAW"]["x"], "y": system["RAW"]["y"]},
        "start-rect": {"x": obj["x"], "y": obj["y"], "w": obj["w"], "h": obj["h"]},
    }


def handle_resize_armed_state(organism):
    """Wait until drag intent is clear before claiming resize ownership."""
    derived = system["DERIVED"]
    if derived["button-1-released"]:
        clear_organism(organism)
        return

    if not derived["drag-threshold-crossed"]:
        return

    if not get_permission(HOLD_RESOURCE):
        clear_organism(organism)
        return

    organism["STATE"] = DRAGGING


def handle_resize_dragging_state(organism):
    """Emit resize effects while the handle drag is active."""
    emit_world_effect(
        "resize-object",
        "resize-object",
        {
            "object-id": organism["HELD"]["object-id"],
            "handle": organism["HELD"]["handle"],
            "start-rect": organism["DATA"]["start-rect"],
            "pointer-x": system["RAW"]["x"],
            "pointer-y": system["RAW"]["y"],
        },
    )

    if system["DERIVED"]["button-1-released"]:
        clear_organism(organism)


def handle_marquee_idle_state(organism):
    """Arm marquee selection when button 1 is pressed on empty space."""
    derived = system["DERIVED"]
    if not derived["button-1-pressed"]:
        return
    if derived["pointer-handle-target"] is not None:
        return
    if derived["pointer-target"] is not None:
        return

    organism["HELD"] = {"gesture": "marquee-select"}
    if not get_permission(START):
        clear_organism(organism)
        return

    organism["STATE"] = ARMED
    organism["DATA"] = {"press-point": {"x": system["RAW"]["x"], "y": system["RAW"]["y"]}}


def handle_marquee_armed_state(organism):
    """Wait until drag intent is clear before beginning rectangle selection."""
    derived = system["DERIVED"]
    if derived["button-1-released"]:
        emit_world_effect("marquee-select", "set-selection", {"object-ids": []})
        clear_organism(organism)
        return

    if not derived["drag-threshold-crossed"]:
        return

    organism["STATE"] = SELECTING


def handle_marquee_selecting_state(organism):
    """Emit marquee preview and commit selection on release."""
    rect = rect_from_points(organism["DATA"]["press-point"], system["RAW"])
    hits = list_objects_in_rect(rect)

    organism["HELD"] = {"gesture": "marquee-select", "object-ids": hits}
    emit_projection_effect("marquee-select", "selection-rectangle", {"rect": rect, "object-ids": hits})

    if not system["DERIVED"]["button-1-released"]:
        return

    emit_world_effect("marquee-select", "set-selection", {"object-ids": hits})
    clear_organism(organism)


def handle_group_drag_idle_state(organism):
    """Arm group dragging when press begins on a selected object."""
    derived = system["DERIVED"]
    target = derived["pointer-target"]
    selected = world["selected-objects"]
    if not derived["button-1-pressed"] or not target:
        return
    if derived["pointer-handle-target"] is not None:
        return
    if target not in selected:
        return

    organism["HELD"] = {"object-ids": list(selected), "lead-object-id": target}
    if not get_permission(START):
        clear_organism(organism)
        return

    organism["STATE"] = ARMED
    organism["DATA"] = {
        "press-point": {"x": system["RAW"]["x"], "y": system["RAW"]["y"]},
        "start-positions": snapshot_object_positions(selected),
    }


def handle_group_drag_armed_state(organism):
    """Wait for threshold crossing before claiming the whole group."""
    derived = system["DERIVED"]
    if derived["button-1-released"]:
        emit_world_effect(
            "drag-selection-group",
            "set-selection",
            {"object-ids": [organism["HELD"]["lead-object-id"]]},
        )
        clear_organism(organism)
        return

    if not derived["drag-threshold-crossed"]:
        return

    if not get_permission(HOLD_RESOURCE):
        clear_organism(organism)
        return

    organism["STATE"] = DRAGGING


def handle_group_dragging_state(organism):
    """Move the selected group as one coordinated bundle."""
    press = organism["DATA"]["press-point"]
    dx = system["RAW"]["x"] - press["x"]
    dy = system["RAW"]["y"] - press["y"]

    emit_world_effect(
        "drag-selection-group",
        "move-selection-group",
        {
            "object-ids": list(organism["HELD"]["object-ids"]),
            "start-positions": organism["DATA"]["start-positions"],
            "dx": dx,
            "dy": dy,
        },
    )
    emit_projection_effect(
        "drag-selection-group",
        "drag-anchor",
        {
            "object-id": organism["HELD"]["lead-object-id"],
            "pointer-x": system["RAW"]["x"],
            "pointer-y": system["RAW"]["y"],
        },
    )

    if system["DERIVED"]["button-1-released"]:
        clear_organism(organism)


def get_permission(request):
    """Judge whether the current organism may start or hold a resource."""
    current = system["CURRENT-ORGANISM"]
    coordination = system["COORDINATION"]
    organism = find_organism(current)

    if request == START:
        if not may_claim_pointer(current):
            return False
        if current == "resize-object":
            target = organism["HELD"].get("object-id")
            if are_any_resources_held([target]):
                coordination["judge-notes"].append("denied START: resize target already held")
                return False
            return True
        if current == "drag-object":
            target = organism["HELD"].get("object-id")
            if are_any_resources_held([target]):
                coordination["judge-notes"].append("denied START: resource already held")
                return False
            return True
        if current == "drag-selection-group":
            if are_any_resources_held(organism["HELD"].get("object-ids", [])):
                coordination["judge-notes"].append("denied START: selected resource already held")
                return False
            return True
        if current == "marquee-select":
            return True
        return False

    if request == HOLD_RESOURCE:
        if current == "resize-object":
            target = organism["HELD"].get("object-id")
            if target not in world["objects"]:
                coordination["judge-notes"].append("denied HOLD-RESOURCE: missing resize target")
                return False
            if not may_claim_pointer(current, "denied HOLD-RESOURCE: pointer contested"):
                return False
            set_exclusive_coordination(current, target)
            return True

        if current == "drag-object":
            target = organism["HELD"].get("object-id")
            if target not in world["objects"]:
                coordination["judge-notes"].append("denied HOLD-RESOURCE: missing object")
                return False
            if not may_claim_pointer(current, "denied HOLD-RESOURCE: pointer contested"):
                return False
            set_exclusive_coordination(current, target)
            return True

        if current == "drag-selection-group":
            object_ids = organism["HELD"].get("object-ids", [])
            if not object_ids:
                coordination["judge-notes"].append("denied HOLD-RESOURCE: empty selection")
                return False
            for object_id in object_ids:
                if object_id not in world["objects"]:
                    coordination["judge-notes"].append("denied HOLD-RESOURCE: selected object missing")
                    return False
            if not may_claim_pointer(current, "denied HOLD-RESOURCE: pointer contested"):
                return False
            set_exclusive_coordination(current, list(object_ids))
            return True

        if current == "marquee-select":
            return True

        return False

    return False


def route_effects():
    """Apply world mutations now and keep preview effects for rendering."""
    for effect in system["EFFECTS"]:
        if effect["kind"] == WORLD_MUTATION:
            apply_world_effect(effect)


def apply_world_effect(effect):
    """Mutate durable world state from a world-mutation effect."""
    payload = effect["payload"]
    if effect["name"] == "move-object":
        obj = world["objects"][payload["object-id"]]
        x = payload["x"]
        y = payload["y"]
        if system["RAW"]["quantization-enabled"]:
            step = system["RAW"]["quantization-step"]
            x = snap_value(x, step)
            y = snap_value(y, step)
        obj["x"] = clamp(x, 20, PANEL_X - obj["w"] - 20)
        obj["y"] = clamp(y, 20, CANVAS_H - obj["h"] - 20)
        return

    if effect["name"] == "set-selection":
        world["selected-objects"] = list(payload["object-ids"])
        return

    if effect["name"] == "move-selection-group":
        apply_group_move_effect(payload)
        return

    if effect["name"] == "resize-object":
        apply_resize_object_effect(payload)


def emit_world_effect(source, name, payload):
    """Append a durable world-mutation effect to the effect list."""
    system["EFFECTS"].append(
        {"kind": WORLD_MUTATION, "source": source, "name": name, "payload": payload}
    )


def emit_projection_effect(source, name, payload):
    """Append a transient projection preview effect to the effect list."""
    system["EFFECTS"].append(
        {"kind": PROJECTION_PREVIEW, "source": source, "name": name, "payload": payload}
    )


def render_projection():
    """Render the world, coordination, and preview effects downstream."""
    canvas = g["canvas"]
    canvas.delete("all")
    draw_background()
    draw_world_objects()
    draw_preview_effects()
    draw_divider()
    draw_architecture_panel()


def draw_background():
    """Paint the canvas background and demo title."""
    canvas = g["canvas"]
    canvas.create_rectangle(0, 0, CANVAS_W, CANVAS_H, fill="#f6f2e8", outline="")
    if system["RAW"]["quantization-enabled"]:
        draw_quantization_grid()
    canvas.create_text(
        28,
        20,
        anchor="nw",
        text="Interaction Architecture Demo",
        fill="#1e2a33",
        font=("TkDefaultFont", 18, "bold"),
    )
    canvas.create_text(
        28,
        48,
        anchor="nw",
        text="Tokenizers perceive. Organisms petition. The judge legitimizes.",
        fill="#42525d",
        font=("TkDefaultFont", 10),
    )


def draw_quantization_grid():
    """Draw a light snap grid when quantization is enabled."""
    step = system["RAW"]["quantization-step"]
    canvas = g["canvas"]
    for x in range(20, PANEL_X, step):
        canvas.create_line(x, 0, x, CANVAS_H, fill="#e1dac8")
    for y in range(20, CANVAS_H, step):
        canvas.create_line(0, y, PANEL_X, y, fill="#e1dac8")


def draw_world_objects():
    """Draw the durable world objects on the playfield."""
    canvas = g["canvas"]
    for obj in world["objects"].values():
        x1 = obj["x"]
        y1 = obj["y"]
        x2 = x1 + obj["w"]
        y2 = y1 + obj["h"]
        canvas.create_rectangle(
            x1,
            y1,
            x2,
            y2,
            fill=obj["fill"],
            outline=selection_outline_for_object(obj["id"]),
            width=selection_width_for_object(obj["id"]),
        )
        canvas.create_text(
            x1 + 14,
            y1 + 16,
            anchor="nw",
            text=obj["label"],
            fill="#fdfaf2",
            font=("TkDefaultFont", 12, "bold"),
        )

    draw_resize_handles()


def draw_preview_effects():
    """Draw transient projection artifacts without mutating the world."""
    canvas = g["canvas"]
    for effect in system["EFFECTS"]:
        if effect["kind"] != PROJECTION_PREVIEW:
            continue
        if effect["name"] == "hover-outline":
            draw_hover_outline(effect["payload"]["object-id"])
            continue
        if effect["name"] == "drag-anchor":
            draw_drag_anchor(effect["payload"])
            continue
        if effect["name"] == "selection-rectangle":
            draw_selection_rectangle(effect["payload"])


def draw_hover_outline(object_id):
    """Draw a transient highlight around the hovered object."""
    obj = world["objects"][object_id]
    g["canvas"].create_rectangle(
        obj["x"] - 4,
        obj["y"] - 4,
        obj["x"] + obj["w"] + 4,
        obj["y"] + obj["h"] + 4,
        outline="#f2c14e",
        width=3,
    )


def draw_drag_anchor(payload):
    """Draw a guide from the pointer to the dragged object's center."""
    obj = world["objects"][payload["object-id"]]
    cx = obj["x"] + obj["w"] / 2
    cy = obj["y"] + obj["h"] / 2
    g["canvas"].create_line(
        payload["pointer-x"],
        payload["pointer-y"],
        cx,
        cy,
        fill="#2f4858",
        dash=(6, 4),
        width=2,
    )


def draw_selection_rectangle(payload):
    """Draw the marquee selection rectangle and its current hit objects."""
    rect = payload["rect"]
    g["canvas"].create_rectangle(
        rect["x1"],
        rect["y1"],
        rect["x2"],
        rect["y2"],
        outline="#1f4f7a",
        width=2,
        dash=(4, 3),
    )

    for object_id in payload["object-ids"]:
        obj = world["objects"][object_id]
        g["canvas"].create_rectangle(
            obj["x"] - 6,
            obj["y"] - 6,
            obj["x"] + obj["w"] + 6,
            obj["y"] + obj["h"] + 6,
            outline="#1f4f7a",
            width=2,
            dash=(3, 2),
        )


def draw_resize_handles():
    """Draw corner resize handles when exactly one object is selected."""
    object_id = single_selected_object_id()
    if object_id is None:
        return

    obj = world["objects"][object_id]
    for handle in ("nw", "ne", "sw", "se"):
        cx, cy = resize_handle_center(obj, handle)
        g["canvas"].create_rectangle(
            cx - HANDLE_HALF,
            cy - HANDLE_HALF,
            cx + HANDLE_HALF,
            cy + HANDLE_HALF,
            fill="#fdfaf2",
            outline="#1f4f7a",
            width=2,
        )


def draw_divider():
    """Separate playfield from the architecture inspector panel."""
    g["canvas"].create_line(PANEL_X, 0, PANEL_X, CANVAS_H, fill="#c5bda9", width=2)


def draw_architecture_panel():
    """Display the internal blackboard state for inspection."""
    x = PANEL_X + 24
    y = 24
    lines = build_panel_lines()
    canvas = g["canvas"]

    canvas.create_text(
        x,
        y,
        anchor="nw",
        text="Inspector",
        fill="#1e2a33",
        font=("TkDefaultFont", 16, "bold"),
    )
    y += 30

    for line in lines:
        canvas.create_text(
            x,
            y,
            anchor="nw",
            text=line,
            fill="#2c3941",
            font=("Consolas", 10),
        )
        y += 18


def build_panel_lines():
    """Format a concise textual view of the architecture state."""
    raw = system["RAW"]
    derived = system["DERIVED"]
    coord = system["COORDINATION"]
    resize = find_organism("resize-object")
    drag = find_organism("drag-object")
    marquee = find_organism("marquee-select")
    drag_group = find_organism("drag-selection-group")
    hover = find_organism("hover-highlight")

    return [
        "RAW",
        f"  xy=({raw['x']}, {raw['y']})  inside={raw['inside-canvas']}",
        f"  b1-down={raw['button-1-down']}  target={raw['mouse-over']}",
        f"  quantized={raw['quantization-enabled']}  step={raw['quantization-step']}",
        "",
        "DERIVED",
        f"  moving={derived['moving']}  dxdy=({derived['dx']}, {derived['dy']})",
        f"  b1-pressed={derived['button-1-pressed']}",
        f"  b1-released={derived['button-1-released']}",
        f"  entered={derived['entered-target']}  left={derived['left-target']}",
        f"  drag-threshold-crossed={derived['drag-threshold-crossed']}",
        f"  pointer-handle-target={derived['pointer-handle-target']}",
        "",
        "WORLD",
        f"  selected={world['selected-objects']}",
        "",
        "COORDINATION",
        f"  pointer-owner={coord['pointer-owner']}",
        f"  active-gesture={coord['active-gesture']}",
        f"  resource-holds={coord['resource-holds']}",
        f"  hover-target={coord['hover-target']}",
        "",
        "ORGANISMS",
        f"  hover-highlight STATE={hover['STATE']} HELD={hover['HELD']}",
        f"  resize-object   STATE={resize['STATE']} HELD={resize['HELD']}",
        f"  marquee-select  STATE={marquee['STATE']} HELD={marquee['HELD']}",
        f"  drag-selection  STATE={drag_group['STATE']} HELD={drag_group['HELD']}",
        f"  drag-object     STATE={drag['STATE']} HELD={drag['HELD']}",
        "",
        "NOTES",
        "  ESC or r resets the demo",
        "  Single selection shows resize handles",
        "  Empty-space drag creates a marquee selection",
        "  Drag a selected object to move the full group",
        f"  judge-notes={coord['judge-notes']}",
    ]


def find_object_at(x, y):
    """Return the topmost world object whose bounds contain the point."""
    for object_id in reversed(list(world["objects"].keys())):
        obj = world["objects"][object_id]
        if point_inside_object(x, y, obj):
            return object_id
    return None


def point_inside_object(x, y, obj):
    """Check whether a point lies inside an object's rectangle."""
    return obj["x"] <= x <= obj["x"] + obj["w"] and obj["y"] <= y <= obj["y"] + obj["h"]


def find_resize_handle_at(x, y):
    """Return the selected object's resize handle under the pointer, if any."""
    object_id = single_selected_object_id()
    if object_id is None:
        return None

    obj = world["objects"][object_id]
    for handle in ("nw", "ne", "sw", "se"):
        cx, cy = resize_handle_center(obj, handle)
        if abs(x - cx) <= HANDLE_HALF and abs(y - cy) <= HANDLE_HALF:
            return {"object-id": object_id, "handle": handle}
    return None


def single_selected_object_id():
    """Return the single selected object id, or None otherwise."""
    if len(world["selected-objects"]) != 1:
        return None
    return world["selected-objects"][0]


def resize_handle_center(obj, handle):
    """Return the center point of a named corner resize handle."""
    if handle == "nw":
        return obj["x"], obj["y"]
    if handle == "ne":
        return obj["x"] + obj["w"], obj["y"]
    if handle == "sw":
        return obj["x"], obj["y"] + obj["h"]
    return obj["x"] + obj["w"], obj["y"] + obj["h"]


def find_organism(name):
    """Look up an organism by its canonical name."""
    for organism in system["ORGANISMS"]:
        if organism["NAME"] == name:
            return organism
    raise KeyError(name)


def clamp(value, lower, upper):
    """Clamp a numeric value into an inclusive range."""
    return max(lower, min(upper, value))


def snap_value(value, step):
    """Snap a numeric value to the nearest quantization step."""
    return int(round(value / step) * step)


def clear_organism(organism):
    """Return an organism to its empty resting condition."""
    organism["STATE"] = IDLE
    organism["HELD"] = {}
    organism["DATA"] = {}


def rect_from_points(p1, p2):
    """Normalize two points into a rectangle dictionary."""
    return {
        "x1": min(p1["x"], p2["x"]),
        "y1": min(p1["y"], p2["y"]),
        "x2": max(p1["x"], p2["x"]),
        "y2": max(p1["y"], p2["y"]),
    }


def list_objects_in_rect(rect):
    """Return object ids whose rectangles intersect the marquee rectangle."""
    hits = []
    for object_id, obj in world["objects"].items():
        if rect_intersects_object(rect, obj):
            hits.append(object_id)
    return hits


def rect_intersects_object(rect, obj):
    """Check whether a marquee rectangle intersects an object rectangle."""
    return not (
        rect["x2"] < obj["x"]
        or rect["x1"] > obj["x"] + obj["w"]
        or rect["y2"] < obj["y"]
        or rect["y1"] > obj["y"] + obj["h"]
    )


def snapshot_object_positions(object_ids):
    """Capture object positions for later relative group movement."""
    positions = {}
    for object_id in object_ids:
        obj = world["objects"][object_id]
        positions[object_id] = {"x": obj["x"], "y": obj["y"]}
    return positions


def apply_group_move_effect(payload):
    """Move a selected object bundle while preserving relative offsets."""
    start_positions = payload["start-positions"]
    dx = payload["dx"]
    dy = payload["dy"]
    if system["RAW"]["quantization-enabled"]:
        step = system["RAW"]["quantization-step"]
        dx = snap_value(dx, step)
        dy = snap_value(dy, step)

    bounded_dx = compute_group_delta_bound(start_positions, dx, "x")
    bounded_dy = compute_group_delta_bound(start_positions, dy, "y")

    for object_id in payload["object-ids"]:
        obj = world["objects"][object_id]
        start = start_positions[object_id]
        obj["x"] = start["x"] + bounded_dx
        obj["y"] = start["y"] + bounded_dy


def apply_resize_object_effect(payload):
    """Resize one object by applying lawful geometry constraints."""
    obj = world["objects"][payload["object-id"]]
    rect = compute_resized_rect(
        payload["start-rect"],
        payload["handle"],
        payload["pointer-x"],
        payload["pointer-y"],
    )
    obj["x"] = rect["x"]
    obj["y"] = rect["y"]
    obj["w"] = rect["w"]
    obj["h"] = rect["h"]


def compute_resized_rect(start_rect, handle, pointer_x, pointer_y):
    """Compute a clamped rectangle from a resize handle drag."""
    left = start_rect["x"]
    top = start_rect["y"]
    right = start_rect["x"] + start_rect["w"]
    bottom = start_rect["y"] + start_rect["h"]
    if system["RAW"]["quantization-enabled"]:
        step = system["RAW"]["quantization-step"]
        pointer_x = snap_value(pointer_x, step)
        pointer_y = snap_value(pointer_y, step)

    if "w" in handle:
        left = clamp(pointer_x, 20, right - MIN_SIZE)
    if "e" in handle:
        right = clamp(pointer_x, left + MIN_SIZE, PANEL_X - 20)
    if "n" in handle:
        top = clamp(pointer_y, 20, bottom - MIN_SIZE)
    if "s" in handle:
        bottom = clamp(pointer_y, top + MIN_SIZE, CANVAS_H - 20)

    return {
        "x": left,
        "y": top,
        "w": right - left,
        "h": bottom - top,
    }


def compute_group_delta_bound(start_positions, delta, axis):
    """Clamp group translation so the full selection stays in bounds."""
    lower_bound = None
    upper_bound = None

    for object_id, start in start_positions.items():
        obj = world["objects"][object_id]
        if axis == "x":
            low = 20 - start["x"]
            high = PANEL_X - obj["w"] - 20 - start["x"]
        else:
            low = 20 - start["y"]
            high = CANVAS_H - obj["h"] - 20 - start["y"]

        lower_bound = low if lower_bound is None else max(lower_bound, low)
        upper_bound = high if upper_bound is None else min(upper_bound, high)

    return clamp(delta, lower_bound, upper_bound)


def selection_outline_for_object(object_id):
    """Choose an outline color based on current selection state."""
    if object_id in world["selected-objects"]:
        return "#1f4f7a"
    return "#24323a"


def selection_width_for_object(object_id):
    """Choose an outline width based on current selection state."""
    if object_id in world["selected-objects"]:
        return 4
    return 2


if __name__ == "__main__":
    main()

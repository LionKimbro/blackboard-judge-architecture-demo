"""Tkinter canvas demo of the blackboard-judge interaction architecture.

This program demonstrates a tiny interactive ecology:
- tokenizers derive shared perceptual facts from raw pointer/button input
- organisms recognize local interaction episodes over time
- a judge authoritatively manages coordination and resource ownership
- effects are routed separately into world mutation and projection preview
"""

from __future__ import annotations

import copy
import tkinter as tk


IDLE = "IDLE"
ARMED = "ARMED"
DRAGGING = "DRAGGING"

START = "START"
HOLD_RESOURCE = "HOLD-RESOURCE"

WORLD_MUTATION = "WORLD-MUTATION"
PROJECTION_PREVIEW = "PROJECTION-PREVIEW"

CANVAS_W = 980
CANVAS_H = 640
PANEL_X = 660
DRAG_THRESHOLD = 8

g = {}
world = {}
system = {}


def main():
    """Build the UI, initialize the interaction system, and enter Tk."""
    build_app()
    reset_demo_state()
    render_projection()
    g["root"].mainloop()


def build_app():
    """Create the root window and canvas, and bind raw-input callbacks."""
    g["root"] = tk.Tk()
    g["root"].title("Interaction Architecture Blackboard-Judge Demo")
    g["canvas"] = tk.Canvas(
        g["root"],
        width=CANVAS_W,
        height=CANVAS_H,
        bg="#f6f2e8",
        highlightthickness=0,
    )
    g["canvas"].grid(row=0, column=0, sticky="nsew")

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
            }
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
                    "NAME": "drag-object",
                    "ACTIVE": True,
                    "STATE": IDLE,
                    "HELD": {},
                    "DATA": {},
                    "FN": organism_drag_object,
                },
            ],
        }
    )


def make_initial_raw():
    """Return the canonical internal raw-input snapshot."""
    return {
        "x": 0,
        "y": 0,
        "ms": 0,
        "inside-canvas": True,
        "button-1-down": False,
        "mouse-over": None,
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
    }


def handle_pointer_motion(event):
    """Normalize pointer motion into RAW and run one interaction cycle."""
    run_cycle(
        {
            "x": event.x,
            "y": event.y,
            "ms": event.time,
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
            "ms": event.time,
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
            "ms": event.time,
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
            "ms": event.time,
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


def run_cycle(raw_update):
    """Advance the architecture one cycle from raw input to projection."""
    preserve_previous_snapshots()
    populate_raw(raw_update)
    run_tokenizers()
    maintain_judge()
    evaluate_organisms()
    maintain_judge()
    route_effects()
    render_projection()


def preserve_previous_snapshots():
    """Freeze prior RAW and DERIVED so tokenizers can work temporally."""
    system["RAW-PREV"] = copy.deepcopy(system["RAW"])
    system["DERIVED-PREV"] = copy.deepcopy(system["DERIVED"])


def populate_raw(raw_update):
    """Install a normalized raw-input snapshot for the current cycle."""
    system["RAW"] = raw_update


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


def tokenizer_drag_threshold(tokenizer):
    """Derive when the pointer has moved far enough for dragging to count."""
    derived = system["DERIVED"]
    drag = find_organism("drag-object")

    if drag["STATE"] != ARMED:
        tokenizer["DATA"]["crossed"] = False
        derived["drag-threshold-crossed"] = False
        return

    anchor = drag["DATA"]["press-point"]
    dx = system["RAW"]["x"] - anchor["x"]
    dy = system["RAW"]["y"] - anchor["y"]
    crossed = (dx * dx + dy * dy) >= (DRAG_THRESHOLD * DRAG_THRESHOLD)
    tokenizer["DATA"]["crossed"] = crossed
    derived["drag-threshold-crossed"] = crossed


def maintain_judge():
    """Reconcile coordination state against world and organism public state."""
    coordination = system["COORDINATION"]
    coordination["judge-notes"] = []

    drag = find_organism("drag-object")
    hover = find_organism("hover-highlight")
    held_object = drag["HELD"].get("object-id")
    lease = coordination["leases"].get("drag-object")
    coordination["hover-target"] = hover["HELD"].get("object-id")

    if drag["STATE"] == DRAGGING and held_object and held_object in world["objects"]:
        coordination["pointer-owner"] = "drag-object"
        coordination["active-gesture"] = "drag-object"
        coordination["resource-holds"] = {held_object: "drag-object"}
        coordination["leases"]["drag-object"] = {
            "resource": held_object,
            "kind": "exclusive",
            "valid": True,
        }
        return

    if lease:
        coordination["judge-notes"].append("released stale drag lease")

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


def handle_drag_idle_state(organism):
    """Begin an armed drag candidate when press occurs over an object."""
    derived = system["DERIVED"]
    target = derived["pointer-target"]
    if not derived["button-1-pressed"] or not target:
        return

    organism["HELD"] = {"object-id": target}
    if not get_permission(START):
        organism["HELD"] = {}
        return

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
        organism["STATE"] = IDLE
        organism["HELD"] = {}
        organism["DATA"] = {}
        return

    if not derived["drag-threshold-crossed"]:
        return

    if not get_permission(HOLD_RESOURCE):
        organism["STATE"] = IDLE
        organism["HELD"] = {}
        organism["DATA"] = {}
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
        organism["STATE"] = IDLE
        organism["HELD"] = {}
        organism["DATA"] = {}


def get_permission(request):
    """Judge whether the current organism may start or hold a resource."""
    current = system["CURRENT-ORGANISM"]
    coordination = system["COORDINATION"]
    organism = find_organism(current)

    if request == START:
        target = organism["HELD"].get("object-id")
        if current != "drag-object":
            return False
        if coordination["pointer-owner"] not in (None, current):
            coordination["judge-notes"].append("denied START: pointer already owned")
            return False
        if target in coordination["resource-holds"]:
            coordination["judge-notes"].append("denied START: resource already held")
            return False
        return True

    if request == HOLD_RESOURCE:
        target = organism["HELD"].get("object-id")
        if current != "drag-object":
            return False
        if target not in world["objects"]:
            coordination["judge-notes"].append("denied HOLD-RESOURCE: missing object")
            return False
        if coordination["pointer-owner"] not in (None, current):
            coordination["judge-notes"].append("denied HOLD-RESOURCE: pointer contested")
            return False

        coordination["pointer-owner"] = current
        coordination["active-gesture"] = current
        coordination["resource-holds"] = {target: current}
        coordination["leases"][current] = {
            "resource": target,
            "kind": "exclusive",
            "valid": True,
        }
        return True

    return False


def route_effects():
    """Apply world mutations now and keep preview effects for rendering."""
    for effect in system["EFFECTS"]:
        if effect["kind"] == WORLD_MUTATION:
            apply_world_effect(effect)


def apply_world_effect(effect):
    """Mutate durable world state from a world-mutation effect."""
    payload = effect["payload"]
    if effect["name"] != "move-object":
        return

    obj = world["objects"][payload["object-id"]]
    obj["x"] = clamp(payload["x"], 20, PANEL_X - obj["w"] - 20)
    obj["y"] = clamp(payload["y"], 20, CANVAS_H - obj["h"] - 20)


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
            outline="#24323a",
            width=2,
        )
        canvas.create_text(
            x1 + 14,
            y1 + 16,
            anchor="nw",
            text=obj["label"],
            fill="#fdfaf2",
            font=("TkDefaultFont", 12, "bold"),
        )


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
    drag = find_organism("drag-object")
    hover = find_organism("hover-highlight")

    return [
        "RAW",
        f"  xy=({raw['x']}, {raw['y']})  inside={raw['inside-canvas']}",
        f"  b1-down={raw['button-1-down']}  target={raw['mouse-over']}",
        "",
        "DERIVED",
        f"  moving={derived['moving']}  dxdy=({derived['dx']}, {derived['dy']})",
        f"  b1-pressed={derived['button-1-pressed']}",
        f"  b1-released={derived['button-1-released']}",
        f"  entered={derived['entered-target']}  left={derived['left-target']}",
        f"  drag-threshold-crossed={derived['drag-threshold-crossed']}",
        "",
        "COORDINATION",
        f"  pointer-owner={coord['pointer-owner']}",
        f"  active-gesture={coord['active-gesture']}",
        f"  resource-holds={coord['resource-holds']}",
        f"  hover-target={coord['hover-target']}",
        "",
        "ORGANISMS",
        f"  hover-highlight STATE={hover['STATE']} HELD={hover['HELD']}",
        f"  drag-object     STATE={drag['STATE']} HELD={drag['HELD']}",
        "",
        "NOTES",
        "  ESC or r resets the demo",
        "  Hover outlines are preview effects",
        "  Drag motion is world mutation via routed effects",
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


def find_organism(name):
    """Look up an organism by its canonical name."""
    for organism in system["ORGANISMS"]:
        if organism["NAME"] == name:
            return organism
    raise KeyError(name)


def clamp(value, lower, upper):
    """Clamp a numeric value into an inclusive range."""
    return max(lower, min(upper, value))


if __name__ == "__main__":
    main()

import demo.app as app


class FakeClock:
    def __init__(self, start=1000, step=100):
        self.value = start
        self.step = step

    def __call__(self):
        current = self.value
        self.value += self.step
        return current


def setup_demo(monkeypatch):
    clock = FakeClock()
    monkeypatch.setattr(app, "now_ms", clock)
    app.reset_demo_state()
    return clock


def cycle(x=None, y=None, button_1_down=None, inside_canvas=None):
    raw_update = {}
    if x is not None:
        raw_update["x"] = x
    if y is not None:
        raw_update["y"] = y
    if button_1_down is not None:
        raw_update["button-1-down"] = button_1_down
    if inside_canvas is not None:
        raw_update["inside-canvas"] = inside_canvas
    app.run_cycle(raw_update, render=False)


def press(x, y):
    cycle(x=x, y=y, button_1_down=True, inside_canvas=True)


def move(x, y):
    cycle(x=x, y=y, inside_canvas=True)


def release(x, y):
    cycle(x=x, y=y, button_1_down=False, inside_canvas=True)


def marquee_select(x1, y1, x2, y2):
    press(x1, y1)
    move(x2, y2)
    release(x2, y2)


def drag_single(x1, y1, x2, y2):
    press(x1, y1)
    move(x2, y2)
    release(x2, y2)


def test_idle_tick_accumulates_motionless_duration(monkeypatch):
    setup_demo(monkeypatch)

    cycle(x=50, y=50, inside_canvas=True)
    first = app.system["DERIVED"]["motionless-duration"]
    cycle()
    second = app.system["DERIVED"]["motionless-duration"]
    cycle()
    third = app.system["DERIVED"]["motionless-duration"]

    assert first == 0
    assert second == 100
    assert third == 200


def test_marquee_selects_multiple_objects(monkeypatch):
    setup_demo(monkeypatch)

    marquee_select(40, 60, 450, 360)

    assert app.world["selected-objects"] == ["alpha", "bravo"]


def test_click_empty_space_clears_selection(monkeypatch):
    setup_demo(monkeypatch)
    marquee_select(40, 60, 450, 360)

    press(520, 120)
    release(520, 120)

    assert app.world["selected-objects"] == []


def test_click_selected_object_collapses_group_to_one(monkeypatch):
    setup_demo(monkeypatch)
    marquee_select(40, 60, 450, 360)

    press(120, 120)
    release(120, 120)

    assert app.world["selected-objects"] == ["alpha"]


def test_pressing_unselected_object_collapses_existing_group_selection(monkeypatch):
    setup_demo(monkeypatch)
    marquee_select(40, 60, 450, 360)

    press(240, 450)

    assert app.world["selected-objects"] == ["charlie"]
    assert app.find_organism("drag-object")["STATE"] == app.ARMED


def test_single_object_drag_moves_object(monkeypatch):
    setup_demo(monkeypatch)

    start_x = app.world["objects"]["alpha"]["x"]
    start_y = app.world["objects"]["alpha"]["y"]

    drag_single(100, 120, 180, 210)

    assert app.world["objects"]["alpha"]["x"] == start_x + 80
    assert app.world["objects"]["alpha"]["y"] == start_y + 90
    assert app.world["selected-objects"] == ["alpha"]


def test_group_drag_moves_selected_objects_together(monkeypatch):
    setup_demo(monkeypatch)
    marquee_select(40, 60, 450, 360)

    alpha_before = dict(app.world["objects"]["alpha"])
    bravo_before = dict(app.world["objects"]["bravo"])

    press(120, 120)
    move(170, 170)
    release(170, 170)

    alpha_after = app.world["objects"]["alpha"]
    bravo_after = app.world["objects"]["bravo"]

    assert alpha_after["x"] - alpha_before["x"] == 50
    assert alpha_after["y"] - alpha_before["y"] == 50
    assert bravo_after["x"] - bravo_before["x"] == 50
    assert bravo_after["y"] - bravo_before["y"] == 50


def test_group_drag_clamps_at_right_boundary(monkeypatch):
    setup_demo(monkeypatch)
    marquee_select(40, 60, 450, 360)

    press(120, 120)
    move(900, 120)
    release(900, 120)

    alpha = app.world["objects"]["alpha"]
    bravo = app.world["objects"]["bravo"]

    assert bravo["x"] + bravo["w"] == app.PANEL_X - 20
    assert alpha["x"] == 270
    assert bravo["x"] == 470

from bad_demo import canvas_host_window
from bad_demo import event_queue
from bad_demo import interaction_runtime as runtime
from bad_demo import projection


class FakeCanvas:
    def __init__(self):
        self.items = {}
        self.next_id = 0
        self.immediate_deletes = 0

    def create_rectangle(self, *args, **kwargs):
        return self.create_item("rectangle", args, kwargs)

    def create_text(self, *args, **kwargs):
        return self.create_item("text", args, kwargs)

    def create_line(self, *args, **kwargs):
        return self.create_item("line", args, kwargs)

    def create_item(self, kind, args, kwargs):
        self.next_id += 1
        self.items[self.next_id] = {"kind": kind, "args": args, "kwargs": kwargs}
        return self.next_id

    def delete(self, item):
        if item == "immediate":
            self.immediate_deletes += 1
            for item_id in [item_id for item_id, value in self.items.items() if value["kwargs"].get("tags") == "immediate"]:
                self.items.pop(item_id)
            return
        self.items.pop(item, None)

    def coords(self, item, *args):
        self.items[item]["args"] = args

    def itemconfig(self, item, **kwargs):
        self.items[item]["kwargs"].update(kwargs)


def setup_bad_demo():
    event_queue.events.clear()
    projection.g["items"].clear()
    projection.g["specs"].clear()
    canvas_host_window.widgets["canvas"] = FakeCanvas()
    runtime.initialize_demo_state()
    runtime.run_cycle({"ms": 1000})


def post_press(x, y, ms):
    event_queue.post_event({"type": "BUTTON_1_PRESSED", "x": x, "y": y, "ms": ms})


def post_release(x, y, ms):
    event_queue.post_event({"type": "BUTTON_1_RELEASED", "x": x, "y": y, "ms": ms})


def test_pointer_motion_coalesces_only_at_pending_tail():
    event_queue.events.clear()
    event_queue.post_pointer_motion(1, 2, 10)
    event_queue.post_pointer_motion(3, 4, 20)
    event_queue.post_event({"type": "KEY_PRESSED", "keysym": "r", "char": "r", "ms": 25})
    event_queue.post_pointer_motion(5, 6, 30)

    assert len(event_queue.events) == 3
    assert event_queue.events[0]["samples"] == [{"x": 1, "y": 2, "ms": 10}, {"x": 3, "y": 4, "ms": 20}]
    assert event_queue.events[2]["samples"] == [{"x": 5, "y": 6, "ms": 30}]


def test_click_selects_an_object_through_the_input_queue():
    setup_bad_demo()
    post_press(120, 120, 1100)
    post_release(120, 120, 1200)
    runtime.run_update_cycle()

    assert runtime.world["selected-objects"] == ["alpha"]


def test_marquee_selects_two_objects_through_the_input_queue():
    setup_bad_demo()
    post_press(40, 60, 1100)
    event_queue.post_pointer_motion(450, 360, 1200)
    post_release(450, 360, 1300)
    runtime.run_update_cycle()

    assert runtime.world["selected-objects"] == ["alpha", "bravo"]


def test_single_object_drag_updates_the_world_only_on_release():
    setup_bad_demo()
    post_press(100, 120, 1100)
    event_queue.post_pointer_motion(180, 210, 1200)
    runtime.run_update_cycle()

    assert runtime.world["objects"]["alpha"]["x"] == 70
    post_release(180, 210, 1300)
    runtime.run_update_cycle()

    assert runtime.world["objects"]["alpha"]["x"] == 150
    assert runtime.world["objects"]["alpha"]["y"] == 180
    assert runtime.world["selected-objects"] == ["alpha"]


def test_dragging_a_selected_object_moves_the_entire_selection():
    setup_bad_demo()
    runtime.world["selected-objects"] = ["alpha", "bravo"]
    post_press(100, 120, 1100)
    event_queue.post_pointer_motion(180, 210, 1200)
    post_release(180, 210, 1300)
    runtime.run_update_cycle()

    assert runtime.world["objects"]["alpha"]["x"] == 150
    assert runtime.world["objects"]["bravo"]["x"] == 350


def test_drag_preview_overrides_every_dragged_object_presentation():
    setup_bad_demo()
    runtime.world["selected-objects"] = ["alpha", "bravo"]
    post_press(100, 120, 1100)
    event_queue.post_pointer_motion(180, 210, 1200)
    runtime.run_update_cycle()

    canvas = canvas_host_window.widgets["canvas"]
    alpha = canvas.items[projection.g["items"]["object:alpha:body"]]
    bravo = canvas.items[projection.g["items"]["object:bravo:body"]]

    assert alpha["args"][:2] == (150, 180)
    assert bravo["args"][:2] == (350, 310)
    assert not [key for key in projection.g["items"] if key.startswith("handle:")]
    assert not [item for item in canvas.items.values() if item["kwargs"].get("tags") == "immediate" and item["kind"] == "rectangle"]


def test_marquee_preview_draws_halos_around_candidate_objects():
    setup_bad_demo()
    post_press(40, 60, 1100)
    event_queue.post_pointer_motion(450, 360, 1200)
    runtime.run_update_cycle()

    canvas = canvas_host_window.widgets["canvas"]
    halos = [item for item in canvas.items.values() if item["kwargs"].get("tags") == "immediate" and item["kwargs"].get("outline") == "#f2c14e"]
    assert len(halos) == 2


def test_projection_reuses_a_persistent_canvas_item():
    setup_bad_demo()
    first_item = projection.g["items"]["object:alpha:body"]
    runtime.run_cycle({"ms": 1100})

    assert projection.g["items"]["object:alpha:body"] == first_item


def test_projection_ignores_a_canvas_destroyed_before_timer_callback():
    setup_bad_demo()

    class DestroyedCanvas:
        def winfo_exists(self):
            return False

    canvas_host_window.widgets["canvas"] = DestroyedCanvas()
    runtime.run_cycle({"ms": 1100})

    assert canvas_host_window.widgets["canvas"] is None

# Module — Canvas Host Window

## Source Evidence

`src/demo/app.py` — the Canvas/widget construction and event binding portions
of `build_app()`, plus the `handle_*` Tk callback functions.

## Render Target

`src/bad_demo/canvas_host_window.py`

## OWNS

- Creating the first visible application `tkinter.Toplevel`.
- Creating, laying out, and retaining handles for the Canvas and
  any supporting widgets (such as the local quantization control
  checkbox.)
- Registering this window's Canvas input, keyboard, and supporting-widget
  callbacks.
- Translating Tk event objects into normalized input events and posting them to
  Input Event Queue.

## READS

- Tkinter event coordinates and widget-control values.
- Application configuration required for the window title and Canvas size.

## CALLS

- `interaction_runtime.initialize_demo_state()` during window startup.
- Input Event Queue posting functions from callback adapters.
- `tk_runtime.now_ms()` to timestamp posted input events.

## MAY SAFELY ASSUME

- App Shell has already created and withdrawn the Tk root.
- Every callback runs on the Tkinter main thread.
- Interaction Runtime owns interaction state and Projection owns Canvas drawing.

## ENSURES

- The first visible application window is a Toplevel, not the Tk root.
- Widget callbacks remain thin adapters with no gesture behavior.
- The Canvas and control values exist before the runtime's first projection.

## Callback Ownership

Canvas Host Window owns the registration and thin adapter functions for these
categories of callback:

- **Canvas pointer callbacks:** pointer motion, primary-button press,
  primary-button release, and pointer leave.  Each adapter extracts toolkit
  coordinates/state and posts a normalized input event.  Pointer motion posts
  a timestamped motion sample for queue-tail coalescing.
- **Host-window keyboard callbacks:** keyboard bindings on this Toplevel,
  initially Escape and `r`.  The adapters post raw key-pressed
  and key-released events; they do not decide that a key means reset or any
  other command.
- **Supporting-widget command callbacks:** local controls owned by
  this window, initially the Show Grid checkbox and the Quantize To
  Grid checkbox.  The adapter reports the widget name and current
  value by posting a raw widget-activated input event.

These callbacks do not include Timer callbacks.  Timer owns its own `after()`
callback and merely invokes the callback supplied when the timer is started.

## DOES NOT OWN

- Tk root lifecycle, `mainloop()`, `after()` scheduling, runtime cycle order,
  tokenization, organisms, coordination, world mutation, or Canvas rendering.

## Sketch

```python

widgets = {
    "host-window": None,
    "canvas": None,
    "show-grid-checkbox": None,
    "quantization-checkbox": None,
}

vars = {
    "show-grid-var": None,
    "quantization-var": None,
}

function create_canvas_host_window():
    create_visible_toplevel()
    create_canvas_and_controls()
    register_thin_input_handlers()
    initialize_demo_state()
    run_cycle({})                 # priming state and first projection

function handle_canvas_pointer_motion(event):
    post_pointer_motion(event.x, event.y, tk_runtime.now_ms())
```

### Window and Control Layout

Desired layout:

```text
[                                           ]
[                 Canvas                    ]
[                                           ]
---------------------------------------------
(widget row)
```

The widget row contains a **Show Grid** checkbox and a **Quantize To Grid**
checkbox, with Quantize To Grid placed to the right of Show Grid.

```python
def create_canvas_and_controls():
    create the Canvas at the configured size.
    place it in the first row, spanning the window's two layout columns.

    create the Show Grid checkbox and its Boolean variable.
    create the Quantize To Grid checkbox and its separate Boolean variable.

    place Show Grid beneath the Canvas in the left column.
    place Quantize To Grid beside it in the right column.

    let both layout columns share available extra width.

    retain every created widget in widgets and every control variable in vars.
```

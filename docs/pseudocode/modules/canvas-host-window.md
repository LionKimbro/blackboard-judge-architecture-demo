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
- Translating Tk event objects into normalized runtime input updates.

## READS

- Tkinter event coordinates and widget-control values.
- Application configuration required for the window title and Canvas size.

## CALLS

- `runtime.initialize_demo_state()` during window startup.
- `runtime.run_cycle(raw_update)` from callback adapters.

## MAY SAFELY ASSUME

- App Shell has already created and withdrawn the Tk root.
- Every callback runs on the Tkinter main thread.
- Runtime owns interaction state and Projection owns Canvas drawing.

## ENSURES

- The first visible application window is a Toplevel, not the Tk root.
- Widget callbacks remain thin adapters with no gesture behavior.
- The Canvas and control values exist before the runtime's first projection.

## Callback Ownership

Canvas Host Window owns the registration and thin adapter functions for these
categories of callback:

- **Canvas pointer callbacks:** pointer motion, primary-button press,
  primary-button release, and pointer leave.  Each adapter extracts toolkit
  coordinates/state and calls `runtime.run_cycle(raw_update)`.
- **Host-window keyboard callbacks:** application keyboard commands bound to
  this Toplevel, initially Escape and `r` for resetting the demo.  The adapter
  calls the appropriate runtime command; it does not perform reset behavior
  itself.
- **Supporting-widget command callbacks:** local controls owned by this
  window, initially the Quantize To Grid checkbox.  The adapter reports the
  control's current value to the runtime and requests the normal update path.

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
    "quantization-checkbox": None,
}

vars = {
    "quantization-var": None,
}

function create_canvas_host_window():
    create_visible_toplevel()
    create_canvas_and_controls()
    register_thin_input_handlers()
    initialize_demo_state()
    run_cycle({})                 # priming state and first projection

function handle_canvas_pointer_motion(event):
    run_cycle({ x: event.x, y: event.y, inside-canvas: True })
```

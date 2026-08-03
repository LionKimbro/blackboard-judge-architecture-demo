# Module — Application Shell

## Source Evidence

`src/demo/app.py` — `main()`, `build_app()`, and Tk callback handlers.

## Render Target

`src/bad_demo/app_shell.py`

## OWNS

- Tk root/window creation and visible widget construction.
- Canvas and quantization-checkbox bindings.
- Thin conversion of Tk events into normalized runtime input updates.
- Entering the Tk event loop after startup is complete.

## READS

- Tkinter event coordinates.
- Runtime-facing application objects created during startup.

## CALLS

- `runtime.initialize_demo_state()`.
- `runtime.run_cycle(raw_update)`.
- `runtime.schedule_periodic_tick()`.

## MAY SAFELY ASSUME

- Tkinter callbacks run on the Tkinter main thread.
- Runtime owns interaction state; projection owns Canvas drawing.

## ENSURES

- Every relevant input callback forwards normalized facts rather than gesture
  interpretation.
- The first state initialization and projection occur before `mainloop()`.

## DOES NOT OWN

- Raw/derived fact maintenance, gesture interpretation, coordination, world
  mutation, or projection drawing.

## Sketch

```text
function main():
    build_visible_application()
    initialize_demo_state()
    run_cycle({})                 # priming state and first projection
    schedule_periodic_tick()
    enter_tk_event_loop()

function handle_pointer_motion(event):
    run_cycle({ x: event.x, y: event.y, inside-canvas: True })

function handle_primary_button_press(event):
    run_cycle({ x: event.x, y: event.y, inside-canvas: True,
                button-1-down: True })
```


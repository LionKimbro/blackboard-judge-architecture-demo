# Module — Application Shell

## Source Evidence

`src/demo/app.py` — `main()` and the root-window portion of `build_app()`.

## Render Target

`src/bad_demo/app_shell.py`

## OWNS

- Program setup orchestration.
- Loading and applying program configuration (if any.)
- Orchestrating the start of the timer loop.
- Kicking off the first Canvas Host window's creation.
- Entering the Tk event loop after application composition is complete.

## READS

- nothing

## CALLS

- `canvas_host_window.create_canvas_host_window()`.
- `timer.start_periodic_timer()`
- `tk_runtime.create_and_withdraw_root()`.

## MAY SAFELY ASSUME

- Tkinter callbacks run on the Tkinter main thread.

## ENSURES

- Tk Runtime has created a hidden root that serves as the Tk runtime anchor.
- The application is setup before calling 'mainloop()'.

## DOES NOT OWN

- Visible application windows.
- Event-handler registration.
- Timer scheduling.
- Raw/Derived fact maintenance, gesture interpretation, coordination,
  world mutation, or projection drawing.

## Sketch

```text
function main():
    tk_runtime.create_and_withdraw_root()
    timer.initialize_timer()
    create_canvas_host_window()
    start_periodic_timer(TICK-MS, interaction_runtime.run_update_cycle)
    tk_runtime.g["root"].mainloop()
```

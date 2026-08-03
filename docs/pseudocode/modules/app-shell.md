# Module — Application Shell

## Source Evidence

`src/demo/app.py` — `main()` and the root-window portion of `build_app()`.

## Render Target

`src/bad_demo/app_shell.py`

## OWNS

- Program setup orchestration.
- Loading and applying program configuration (if any.)
- Setting up tkinter to baseline standards:
  - Creating and immediately withdrawing the Tk root runtime anchor.
  - Orchestrating the start of the timer loop.
- Kicking off the first Canvas Host window's creation.
- Entering the Tk event loop after application composition is complete.

## READS

- nothing

## CALLS

- `canvas_host_window.create_canvas_host_window()`.
- `timer.start_periodic_timer()`

## MAY SAFELY ASSUME

- Tkinter callbacks run on the Tkinter main thread.

## ENSURES

- The Tk root stays hidden and exists only as the Tk runtime anchor.
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
    create_and_withdraw_tk_root()
    initialize_timer(tk_root)
    create_canvas_host_window()
    start_periodic_timer(TICK-MS, run_idle_cycle)
    enter_tk_event_loop()
```

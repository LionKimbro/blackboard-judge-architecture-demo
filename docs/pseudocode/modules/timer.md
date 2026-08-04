# Module — Periodic Timer

## Source Evidence

`src/demo/app.py` — `schedule_periodic_tick()` and `handle_periodic_tick()`.

## Render Target

`src/bad_demo/timer.py`

## OWNS

- Registering recurring Tk `after()` callbacks.
- Scheduling the next occurrence after a timer callback has run.
- Cancelling or replacing a prior scheduled callback when the application later
  needs that capability.
- Checking whether at least one application Toplevel remains after each timer
  callback, and ending the Tk main loop when none remain.

## READS

- A caller-supplied interval and callback.
- Tk Runtime's root operations.

## CALLS

- The caller-supplied callback when each interval expires.
- `tk_runtime.g["root"]` for its `after()`, `after_cancel()`, and `quit()`
  operations.
- `tk_runtime.has_active_toplevels()` after each timer callback.

## MAY SAFELY ASSUME

- The supplied callback is safe to invoke on the Tkinter main thread.
- Application composition chooses what recurring work occurs.
- Tk Runtime has withdrawn the root and visible application windows are
  Toplevels belonging to that root.

## ENSURES

- Periodic scheduling is reusable and does not know whether it drives an
  interaction cycle, polling task, animation, or other work.
- It schedules the next occurrence without embedding application behavior.
- It does not keep an otherwise windowless application alive after the last
  application Toplevel closes.

## DOES NOT OWN

- Tk root creation, visible Toplevels, widget bindings, interaction-cycle
  behavior, the semantics of the scheduled callback, or closing a Toplevel.

## Sketch

```text
function initialize_timer():
    confirm tk_runtime.g["root"] exists

function start_periodic_timer(interval-ms, callback):
    remember_interval_and_callback()
    schedule_next_callback()

function handle_timer_expiry():
    callback()
    if tk_runtime.has_active_toplevels():
        schedule_next_callback()
    else:
        tk_runtime.g["root"].quit()
```

The scheduler is installed once during application composition; the interval and
callback are genuine caller choices for each periodic timer.

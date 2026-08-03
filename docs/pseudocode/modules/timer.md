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

## READS

- A caller-supplied interval and callback.

## CALLS

- The caller-supplied callback when each interval expires.
- Tkinter's `after()` scheduling interface.

## MAY SAFELY ASSUME

- The supplied callback is safe to invoke on the Tkinter main thread.
- Application composition chooses what recurring work occurs.

## ENSURES

- Periodic scheduling is reusable and does not know whether it drives an
  interaction cycle, polling task, animation, or other work.
- It schedules the next occurrence without embedding application behavior.

## DOES NOT OWN

- Tk root creation, visible Toplevels, widget bindings, interaction-cycle
  behavior, or the semantics of the scheduled callback.

## Sketch

```text
function initialize_timer(scheduler):
    remember_scheduler_for_this_timer_machine()

function start_periodic_timer(interval-ms, callback):
    remember_interval_and_callback()
    schedule_next_callback()

function handle_timer_expiry():
    callback()
    schedule_next_callback()
```

The scheduler is installed once during application composition; the interval and
callback are genuine caller choices for each periodic timer.

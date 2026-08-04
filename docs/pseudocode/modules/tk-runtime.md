# Module — Tk Runtime

## Source Evidence

`src/demo/app.py` — Tk root creation and root-level Tk operations currently
mixed into `build_app()` and timer scheduling.

## Render Target

`src/bad_demo/tk_runtime.py`

## OWNS

- The shared `g["root"]` register containing the hidden Tk root.
- Creating and immediately withdrawing that root.
- General root-level Tk operations needed by other modules.
- Determining whether any live application Toplevel belongs to the root.
- Returning monotonic millisecond timestamps for Tk callback adapters.

## READS

- The current Tk root's child-widget list.
- Python's monotonic clock.

## CALLS

- Tkinter root and Toplevel operations needed to create/withdraw the root and
  inspect its live Toplevel children.
- Python `time.monotonic()` for timestamp generation.

## MAY SAFELY ASSUME

- App Shell creates the application composition in the Tkinter main thread.
- Visible application windows are Toplevels whose owner is `g["root"]`.

## ENSURES

- Every module that needs the Tk root accesses it through `tk_runtime.g` or a
  Tk Runtime operation.
- The root is withdrawn before visible application windows are created.
- Active-Toplevel checks do not require a window module to inspect a sibling
  window's widget registry.

## DOES NOT OWN

- System orchestration, application configuration, or calling `mainloop()`.
- Calling `after()`, `after_cancel()`, or `quit()`.
- Timer interval/callback/after-id registers or the timer recurrence policy.
- Any Toplevel's widget handles, event bindings, interaction state, or Canvas
  drawing.

## Sketch

```python
g = {
    "root": None,
}


def create_and_withdraw_root():
    g["root"] = tk.Tk()
    g["root"].withdraw()


def has_active_toplevels():
    return any_live_toplevel_belongs_to(g["root"])


def now_ms():
    return int(time.monotonic() * 1000)
```

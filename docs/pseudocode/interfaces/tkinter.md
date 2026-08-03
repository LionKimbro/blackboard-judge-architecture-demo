# Interface — Tkinter Runtime

## Provided By

Python standard library: `tkinter`.

## Used For

- Creating the application window and widget hierarchy.
- Registering event callbacks and key bindings.
- Scheduling periodic work with `after()`.
- Owning the Tk event loop.

## Relied-Upon Facts

- Tkinter owns the GUI event loop and invokes callbacks on its main thread.
- A callback may receive a toolkit event whose coordinates are relative to the
  Canvas that received it.
- `after()` schedules a future callback; it does not create a worker thread.

## Project Rules

- Callbacks only adapt toolkit facts into the application interaction flow.
- No background worker or unrelated module reads or mutates widgets.
- `mainloop()` starts only after application state and bindings are initialized.

## Documentation

- Python Tkinter documentation.
- `C:\lion\github\lions-documents\raw\0010__lions-tkinter-development-conventions_v1.json`


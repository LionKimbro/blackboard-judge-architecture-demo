# Aspect — Input Event Contract

## Participating Modules

`canvas-host-window`, `event-queue`, and `interaction-runtime`.

## Purpose

This contract defines the normalized raw input facts that Canvas Host Window
posts to Input Event Queue and Interaction Runtime consumes.  Input Event Queue
owns their pending FIFO storage and motion coalescing; it does not define their
application meaning.

## Raw-Only Boundary

Input Event Queue contains only input facts: pointer position and button state,
key state, or a concrete widget activation/value.  It never contains a semantic
command, recognized gesture, selection decision, or requested world mutation.
Those meanings may be derived only after the input is consumed, by the
appropriate tokenizer/interaction layer.

## Common Rule

* Every input event has a string `type`.
* Time-bearing pointer/control events use a monotonic `ms` value returned by
  `tk_runtime.now_ms()` at callback time.
* Canvas coordinates are relative to the Canvas host window's Canvas.

## Event Types

### `POINTER_MOTION`

Produced by the Canvas `<Motion>` adapter.  This is the only coalesced event
type.

```python
{
    "type": "POINTER_MOTION",
    "samples": [
        {"x": 100, "y": 120, "ms": 123456},
    ],
}
```

The samples list is ordered.  Input Event Queue may append a new sample only
when the pending queue tail is another `POINTER_MOTION` event.

### `BUTTON_1_PRESSED`

Produced by the Canvas `<ButtonPress-1>` adapter.

```python
{"type": "BUTTON_1_PRESSED", "x": 100, "y": 120, "ms": 123456}
```

### `BUTTON_1_RELEASED`

Produced by the Canvas `<ButtonRelease-1>` adapter.

```python
{"type": "BUTTON_1_RELEASED", "x": 100, "y": 120, "ms": 123456}
```

### `POINTER_LEFT_CANVAS`

Produced by the Canvas `<Leave>` adapter.

```python
{"type": "POINTER_LEFT_CANVAS", "x": 100, "y": 120, "ms": 123456}
```

### `KEY_PRESSED`

Produced by a host-window key-press adapter.  It reports the key fact without
deciding what that key means to the application.

```python
{"type": "KEY_PRESSED", "keysym": "Escape", "char": "", "ms": 123456}
```

### `KEY_RELEASED`

Produced by a host-window key-release adapter.

```python
{"type": "KEY_RELEASED", "keysym": "Escape", "char": "", "ms": 123456}
```

### `WIDGET_ACTIVATED`

Produced by a supporting-widget callback.  It identifies the concrete widget
and reports its current raw/widget value without naming a semantic command.

```python
{
    "type": "WIDGET_ACTIVATED",
    "widget": "quantization-checkbox",
    "value": True,
    "ms": 123456,
}
```

## Consumer Rule

Interaction Runtime consumes events in FIFO order.  It expands a
`POINTER_MOTION` event into its samples in list order before processing the
next queued event.  It converts each input event into the appropriate RAW
update.  Tokenizers may derive a command fact or other higher-level perceptual
fact from those RAW values; the input queue does not do so.  Organisms and
projection do not consume queued events directly.

## Does Not Define

- Tkinter binding syntax or widget handles.
- Timer scheduling.
- DERIVED facts, command interpretation, or semantic events emitted by
  interaction organisms.
- Durable world mutations.

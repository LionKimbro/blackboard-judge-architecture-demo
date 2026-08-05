# Aspect — Quantization

## Participating Modules

`interaction-runtime`, `geometry`, `organisms`, `effects-world`, `projection`,
and `grid`.

## Purpose

Quantization makes an interaction's proposed geometry align to the configured
grid when enabled.  Grid is only the visual reference; it neither decides nor
performs interaction snapping.

## Authority and Data Flow

- Interaction Runtime owns the authoritative quantization step in shared
  configuration and places the current enabled value from the checkbox into
  RAW.
- Geometry owns the pure calculations that snap and constrain values.
- Organisms choose a quantized, lawful proposed geometry while an interaction
  is active.
- Effects World commits the exact proposal supplied by the organism; it does
  not independently snap it again.
- Projection displays the proposal.
- Grid displays the configured reference lines only.

## System Rules

- Quantization is a proposal rule, not a rendering rule.
- A preview and the final world effect use the exact same proposed geometry.
  Releasing the pointer therefore cannot cause a separate snapping jump.
- When quantization is disabled, the lawful unconstrained proposal is used.
- Constraints always win: every proposal must still respect playfield bounds
  and minimum dimensions.
- A group drag snaps its one shared delta, never the individual member objects;
  this preserves their relative offsets.
- Marquee selection and hover perception are not quantized.

## Narrative Pseudo-code

```python
def make_quantized_drag_proposal(starting_positions, raw_delta, constraints,
                                 quantization):
    proposed_delta <- raw_delta

    if quantization is enabled:
        proposed_delta <- snap the one shared X, Y delta to the configured step

    constrain proposed_delta so every affected object remains lawful.
    return the proposed position for every affected object.


def make_quantized_resize_proposal(starting_rectangle, handle, raw_pointer,
                                   constraints, quantization):
    proposed_pointer <- raw_pointer

    if quantization is enabled:
        proposed_pointer <- snap its X, Y values to the configured step

    return the lawful resized rectangle for that handle and pointer.


def use_proposal_for_interaction(proposed_geometry):
    emit the current-frame preview using proposed_geometry.

    when the interaction commits:
        emit the world effect containing that same proposed_geometry.


def apply_quantized_world_effect(proposed_geometry):
    validate that proposed_geometry remains lawful.
    write it to the world without choosing a new snap result.
```

## Does Not Define

- Grid Canvas item creation, visibility mechanics, or layer order.
- The checkbox widget or its Tkinter callback.
- A future choice to snap marquee anchors, rotation, or other interaction
  types.

# Module — Effects and World Mutation

## Source Evidence

`src/demo/app.py` — `route_effects()`, `apply_world_effect()`, emission
helpers, and persistent-effect application helpers.

## Render Target

`src/bad_demo/effects_world.py`

## OWNS

- Effect record construction.
- In-order routing of the current cycle's effects.
- The only legal writes to durable `world` state.

## READS

- Effect queue produced by organisms.
- World objects and selection needed to apply a named mutation.

## CALLS

- Geometry helpers for group movement and resize calculations.
- Lawfulness validation for proposed geometry.  See
  [Quantization](../aspects/quantization.md).

## MAY SAFELY ASSUME

- All organisms have finished emitting effects for the cycle.
- Effects have `kind`, `source`, `name`, and `payload` fields.

## ENSURES

- World mutation effects apply in emission order.
- Volatile effects survive only long enough for the following projection pass.
- Unknown effect names fail visibly rather than silently changing no state.
- A quantized interaction effect commits the exact proposal previously shown
  in its preview; Effects World does not calculate another snap result.

## DOES NOT OWN

- Gesture behavior, Judge decisions, RAW/DERIVED facts, or Canvas operations.

## Initial World Effects

- Set committed selection.
- Move one or more objects to supplied lawful proposed positions.
- Resize one object to a supplied lawful proposed rectangle.

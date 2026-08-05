# Module — Effects and World Mutation

## Source Evidence

`src/demo/app.py` — `route_effects()`, `apply_world_effect()`, emission
helpers, and persistent-effect application helpers.

## Render Target

`src/bad_demo/effects_world.py`

## OWNS

- Effect record construction.
- Its open `effects` and `previews` collections for the current cycle.
- In-order routing of the current cycle's effects.
- The only legal writes to durable `world` state.

## READS

- Effect records produced by organisms in its own `effects` collection.
- The one canonical `world` and `config` contexts in Interaction Runtime.

## CALLS

- Its local lawfulness checks for proposed geometry.  See
  [Quantization](../aspects/quantization.md).

## MAY SAFELY ASSUME

- Interaction Runtime has constructed the canonical world/configuration
  contexts before an effect is routed.
- Every supplied effect record has `source`, `name`, and `payload` fields.

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

## Narrative Pseudo-code

```python
effects = []    # open collection: records emitted in this interaction cycle
previews = []   # open collection: projection records for the current frame


def clear_effects():
    clear the current cycle's effects before organisms begin emitting.


def emit_world_effect(effect):
    append the supplied effect record, marked to say:
        this is a durable world mutation


def emit_projection_effect(effect):
    append the supplied effect record, marked to say:
        this is a one-frame projection preview


def route_effects():
    begin with an empty list of current-frame previews.

    for each emitted effect, in emission order:
        if it is a world mutation:
            apply its named mutation to the durable world.

        if it is a projection preview:
            retain it in the current-frame preview list.

        otherwise:
            fail visibly; an unknown effect kind is a programming error.

    retain the current-frame preview list for Projection.


def get_current_previews():
    return the current-frame preview collection.


def apply_world_effect(effect):
    if the effect is set-selection:
        replace the committed selection with its supplied object IDs.

    if the effect is move-objects:
        verify every supplied proposed position is lawful for its object.
        write those exact X, Y positions to the referenced world objects.

    if the effect is resize-object:
        verify the supplied proposed rectangle is lawful.
        write that exact rectangle to the referenced world object.

    otherwise:
            fail visibly; an unknown world-effect name is a programming error.
```

A projection preview is never applied to the durable world.  It survives only
until the immediately following Projection pass, while a world mutation is
already durable before Projection sees the result.

Effects World directly reads `interaction-runtime.config` and directly mutates
`interaction-runtime.world`; it is specifically authorized to make those
durable world writes.  It does not maintain a second context bundle or an
installed copy of either shared object.

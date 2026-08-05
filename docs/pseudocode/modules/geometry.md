# Module — Geometry and Query Helpers

## Source Evidence

`src/demo/app.py` — object lookup, rectangle, clamping, snapping, resizing,
selection-display, and group-bound helper functions.

## Render Target

`src/bad_demo/geometry.py`

## OWNS

- Pure or near-pure geometric calculations used by other modules.
- Object and handle query operations over the world geometry.
- Bounds, snapping, rectangle intersection, group movement limits, and resize
  rectangle calculations.

## READS

- Explicit geometry values, or the current world when an object lookup is the
  operation's subject.

## CALLS

- No architectural subsystem.

## MAY SAFELY ASSUME

- Object rectangles use x/y/w/h fields.
- The playfield bounds and minimum dimensions are provided by configuration or
  a shared constants region.

## ENSURES

- Shared geometric rules are implemented once and used consistently by
  tokenizers, organisms, effects-world, and projection.
- Helpers do not mutate world state or Canvas state.
- Snapping helpers calculate geometry only; they do not decide whether an
  interaction should be quantized.  See [Quantization](../aspects/quantization.md).

## DOES NOT OWN

- Tokenizer registration, effect emission, interaction state, or rendering.

## Narrative Pseudo-code

```python
def clamp(value, minimum, maximum):
    return value, limited to the inclusive minimum-to-maximum range.


def snap_value(value, step):
    return the grid multiple nearest to value.


def find_object_at(objects, x, y):
    inspect model objects from front to back.
    return the first object whose rectangle contains X, Y;
      otherwise return no object.


def find_resize_handle_at(world, x, y, handle_half_size):
    if there is not exactly one selected object, return no handle.

    calculate that object's four handle centers.
    return the handle whose small square contains X, Y;
      otherwise return no handle.


def rectangle_from(first_point, second_point):
    return the normalized rectangle whose left/top and right/bottom enclose
      both points, regardless of drag direction.


def objects_intersecting(rectangle, objects):
    return every object whose rectangle overlaps the supplied rectangle.


def constrain_group_delta(objects, starting_positions, requested_delta,
                          playfield_bounds, margin):
    calculate the smallest and largest shared X delta that keeps every object
      inside the lawful horizontal bounds.
    do the same for Y.
    return requested_delta clamped to those shared limits.


def make_drag_positions(starting_positions, requested_delta, constraints,
                        quantization):
    if quantization is enabled:
        snap the one shared X, Y requested_delta to quantization.step.

    lawful_delta <- constrain_group_delta(...)
    return every object's starting position plus lawful_delta.


def make_resize_rectangle(starting_rectangle, handle, requested_pointer,
                          constraints, quantization):
    if quantization is enabled:
        snap requested_pointer X and Y to quantization.step.

    move only the edges named by handle.
    constrain the moving edges to preserve minimum size and playfield bounds.
    return the resulting lawful rectangle.
```

Geometry's results are candidates.  Organisms decide when to ask for a
quantized candidate, and Effects World decides when a candidate becomes
durable world state.

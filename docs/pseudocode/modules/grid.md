# Module — Grid

## Source Evidence

`src/demo/app.py` — the quantization grid drawing portion of projection.

## Render Target

`src/bad_demo/grid.py`

## OWNS

- The static Canvas grid-line items for a particular Canvas and grid
  configuration.
- Their shared `gridline` tag and the mechanical application of a requested
  visible/hidden state.
- The grid's background-layer placement.

## READS

- A grid configuration—playfield bounds, Canvas dimensions, and quantization
  step—supplied by Projection from Interaction Runtime's authoritative display
  configuration.
- An explicit requested-visibility value supplied by Projection.

## CALLS

- Tkinter Canvas item creation, configuration, tagging, and stacking
  operations.

## MAY SAFELY ASSUME

- It is called on the Tkinter main thread.
- The Canvas is usable.
- Projection owns the Canvas background and model-object visuals, and gives
  them stable layer tags as needed for grid placement.

## ENSURES

- A fixed grid configuration creates its vertical and horizontal lines only
  once per Canvas.
- Every grid line carries the shared `gridline` tag, so the complete grid can
  be shown or hidden with one Canvas configuration operation.
- The grid remains above the Canvas background and below all model-object
  visuals, including when it is hidden and later shown.
- Grid visibility never changes durable world state.
- Grid lines are visual reference only; Grid does not snap interaction geometry.

## DOES NOT OWN

- The Show Grid checkbox or the meaning of its value.
- The decision whether the grid should be visible.
- When the grid should be created.  Projection decides when to request that
  Grid ensure its items exist.
- The gridded-area bounds or grid spacing.
- Quantization or geometry proposal calculations.  See
  [Quantization](../aspects/quantization.md).
- World objects, selection, handles, interaction previews, or immediate
  overlays.
- Input processing or effect routing.

## Narrative Pseudo-code

```python
def ensure_grid(canvas, grid_configuration, should_be_visible):
    if this Canvas or grid configuration differs from the grid we already own:
        discard our remembered grid handles.
        create the grid for this Canvas and configuration.

    set_grid_visibility(should_be_visible)
    maintain_grid_layer()


def create_grid_for_current_configuration():
    starting at the left edge of the playfield, continuing to its right edge
      in quantization-step increments:
        create a vertical line covering the Canvas height.
        tag it with both "gridline" and a stable location tag, such as
          "grid:x:120".

    starting at the top edge of the Canvas, continuing to its bottom edge in
      quantization-step increments:
        create a horizontal line covering the playfield width.
        tag it with both "gridline" and a stable location tag, such as
          "grid:y:120".


def set_grid_visibility(should_be_visible):
    if should_be_visible:
        configure every item tagged "gridline" as visible.
    otherwise:
        configure every item tagged "gridline" as hidden.


def maintain_grid_layer():
    place every item tagged "gridline" above the Canvas background layer.
    place every item tagged "gridline" below the model-object layer.

    This must be maintained even after visibility toggles or reconciliation
      creates model-object items, so the grid is never brought in front of
      the objects it supports.
```

The intended stack from back to front is: Canvas background, grid, model
objects, selection handles, and immediate overlays.

"""Static, background-layer Canvas grid items."""


g = {"canvas": None, "configuration": None}


def ensure_grid(canvas, configuration, should_be_visible):
    """Mechanically ensure the requested static grid and its presentation."""
    signature = make_configuration_signature(configuration)
    if g["canvas"] is not canvas or g["configuration"] != signature:
        canvas.delete("gridline")
        create_grid_lines(canvas, configuration)
        g.update({"canvas": canvas, "configuration": signature})
    canvas.itemconfigure("gridline", state="normal" if should_be_visible else "hidden")
    maintain_grid_layer(canvas)


def make_configuration_signature(configuration):
    return tuple(sorted(configuration.items()))


def create_grid_lines(canvas, configuration):
    left, right = configuration["left"], configuration["right"]
    top, bottom, step = configuration["top"], configuration["bottom"], configuration["step"]
    for x in range(left, right + 1, step):
        canvas.create_line(x, top, x, bottom, fill="#ddd7ca", tags=("gridline", f"grid:x:{x}"))
    for y in range(top, bottom + 1, step):
        canvas.create_line(left, y, right, y, fill="#ddd7ca", tags=("gridline", f"grid:y:{y}"))


def maintain_grid_layer(canvas):
    canvas.tag_raise("gridline", "canvas-background")
    canvas.tag_lower("gridline", "model-object")

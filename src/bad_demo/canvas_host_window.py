"""Visible Canvas host window and its raw-input callback adapters."""

import tkinter as tk

from . import event_queue, interaction_runtime, tk_runtime


widgets = {"host-window": None, "canvas": None, "quantization-checkbox": None}
vars = {"quantization-var": None}


def create_canvas_host_window():
    """Create the first visible Toplevel, bind adapters, and prime the runtime."""
    window = tk.Toplevel(tk_runtime.g["root"]); window.title("Blackboard-Judge BAD Render Demo")
    canvas = tk.Canvas(window, width=interaction_runtime.config["canvas-width"], height=interaction_runtime.config["canvas-height"], bg="#f6f2e8", highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")
    variable = tk.BooleanVar(value=False)
    checkbox = tk.Checkbutton(window, text="Quantize To Grid", variable=variable, command=handle_quantization_checkbox)
    checkbox.grid(row=1, column=0, sticky="w", padx=12, pady=(6, 10))
    widgets.update({"host-window": window, "canvas": canvas, "quantization-checkbox": checkbox}); vars["quantization-var"] = variable
    canvas.bind("<Motion>", handle_pointer_motion); canvas.bind("<ButtonPress-1>", handle_button_1_press); canvas.bind("<ButtonRelease-1>", handle_button_1_release); canvas.bind("<Leave>", handle_pointer_leave)
    window.bind("<KeyPress>", handle_key_press); window.bind("<KeyRelease>", handle_key_release)
    interaction_runtime.initialize_demo_state(); interaction_runtime.run_cycle({})


def handle_pointer_motion(event): event_queue.post_pointer_motion(event.x, event.y, tk_runtime.now_ms())
def handle_button_1_press(event): event_queue.post_event({"type": "BUTTON_1_PRESSED", "x": event.x, "y": event.y, "ms": tk_runtime.now_ms()})
def handle_button_1_release(event): event_queue.post_event({"type": "BUTTON_1_RELEASED", "x": event.x, "y": event.y, "ms": tk_runtime.now_ms()})
def handle_pointer_leave(event): event_queue.post_event({"type": "POINTER_LEFT_CANVAS", "x": event.x, "y": event.y, "ms": tk_runtime.now_ms()})
def handle_key_press(event): event_queue.post_event({"type": "KEY_PRESSED", "keysym": event.keysym, "char": event.char, "ms": tk_runtime.now_ms()})
def handle_key_release(event): event_queue.post_event({"type": "KEY_RELEASED", "keysym": event.keysym, "char": event.char, "ms": tk_runtime.now_ms()})
def handle_quantization_checkbox(): event_queue.post_event({"type": "WIDGET_ACTIVATED", "widget": "quantization-checkbox", "value": bool(vars["quantization-var"].get()), "ms": tk_runtime.now_ms()})

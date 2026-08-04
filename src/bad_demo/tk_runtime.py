"""Shared Tk runtime facilities for the BAD-rendered demo."""

import tkinter as tk
import time


g = {
    "root": None,
}


def create_and_withdraw_root():
    """Create the hidden Tk root used by the application's Toplevel windows."""
    g["root"] = tk.Tk()
    g["root"].withdraw()


def has_active_toplevels():
    """Return whether the hidden root currently owns a live Toplevel."""
    for widget in g["root"].winfo_children():
        if isinstance(widget, tk.Toplevel) and widget.winfo_exists():
            return True
    return False


def now_ms():
    """Return a monotonic timestamp for a normalized Tk input fact."""
    return int(time.monotonic() * 1000)

"""Periodic Tk timer machine for the BAD-rendered demo."""

from . import tk_runtime


g = {
    "interval-ms": None,
    "callback": None,
    "after-id": None,
}


def initialize_timer():
    """Confirm that Tk Runtime has installed the root this timer will use."""
    if tk_runtime.g["root"] is None:
        raise RuntimeError("Tk Runtime must create the root before Timer starts.")


def start_periodic_timer(interval_ms, callback):
    """Start or replace the recurring timer using the supplied callback."""
    cancel_periodic_timer()
    g["interval-ms"] = interval_ms
    g["callback"] = callback
    schedule_next_callback()


def cancel_periodic_timer():
    """Cancel the pending timer callback when one has been scheduled."""
    if g["after-id"] is None:
        return

    tk_runtime.g["root"].after_cancel(g["after-id"])
    g["after-id"] = None


def schedule_next_callback():
    """Schedule the next timer expiry from the current timer registers."""
    g["after-id"] = tk_runtime.g["root"].after(
        g["interval-ms"],
        handle_timer_expiry,
    )


def handle_timer_expiry():
    """Run scheduled work, then continue only while a Toplevel remains."""
    g["after-id"] = None
    g["callback"]()

    if tk_runtime.has_active_toplevels():
        schedule_next_callback()
        return

    tk_runtime.g["root"].quit()

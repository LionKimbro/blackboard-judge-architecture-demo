"""Application-shell machine for the BAD-rendered Blackboard-Judge demo.

This module owns setup orchestration and entry into Tk's event loop.  Tk Runtime
owns the hidden root; visible windows, timer behavior, and interaction behavior
will be rendered in their own modules.
"""

from . import timer
from . import tk_runtime


TICK_MS = 100


def main():
    """Compose available application parts, then enter Tk's event loop."""
    tk_runtime.create_and_withdraw_root()
    timer.initialize_timer()

    # Pending rendered modules:
    # canvas_host_window.create_canvas_host_window()
    # timer.start_periodic_timer(TICK_MS, interaction_runtime.run_update_cycle)
    timer.start_periodic_timer(TICK_MS, handle_temporary_timer_callback)

    tk_runtime.g["root"].mainloop()


def handle_temporary_timer_callback():
    """Stand in for Interaction Runtime until that module is rendered."""
    return


if __name__ == "__main__":
    main()

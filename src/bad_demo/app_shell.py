"""Application-shell machine for the BAD-rendered Blackboard-Judge demo.

This module owns setup orchestration and entry into Tk's event loop.  Tk Runtime
owns the hidden root; visible windows, timer behavior, and interaction behavior
will be rendered in their own modules.
"""

from . import timer
from . import tk_runtime
from . import canvas_host_window
from . import interaction_runtime


TICK_MS = 100


def main():
    """Compose available application parts, then enter Tk's event loop."""
    tk_runtime.create_and_withdraw_root()
    timer.initialize_timer()

    canvas_host_window.create_canvas_host_window()
    timer.start_periodic_timer(TICK_MS, interaction_runtime.run_update_cycle)

    tk_runtime.g["root"].mainloop()


if __name__ == "__main__":
    main()

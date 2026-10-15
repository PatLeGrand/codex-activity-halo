"""Select the control-button display without assuming connector names."""
import os


def control_screen(screens, primary, env=None):
    env = os.environ if env is None else env
    requested = env.get("ACTIVITY_HALO_MONITOR") or env.get("COMPUTER_USE_MCP_MONITOR")
    return next((screen for screen in screens if requested and screen.name() == requested), primary)

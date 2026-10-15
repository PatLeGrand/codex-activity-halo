import unittest
from types import SimpleNamespace
from display_config import control_screen


class ScreenSelectionTests(unittest.TestCase):
    def test_primary_and_overrides(self):
        primary = SimpleNamespace(name=lambda: "eDP-1")
        other = SimpleNamespace(name=lambda: "DP-2")
        screens = [primary, other]
        self.assertIs(control_screen(screens, primary, {}), primary)
        self.assertIs(control_screen(screens, primary, {"ACTIVITY_HALO_MONITOR": "DP-2"}), other)
        self.assertIs(control_screen(screens, primary, {"COMPUTER_USE_MCP_MONITOR": "DP-2"}), other)
        self.assertIs(control_screen(screens, primary, {"ACTIVITY_HALO_MONITOR": "missing"}), primary)
        self.assertIs(control_screen(screens, primary, {"ACTIVITY_HALO_MONITOR": "eDP-1", "COMPUTER_USE_MCP_MONITOR": "DP-2"}), primary)
        self.assertIsNone(control_screen([], None, {}))

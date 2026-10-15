import unittest
from feedback import Session, control_caption
from theme import THEMES, theme_for


class ThemeTests(unittest.TestCase):
    def test_unknown_or_missing_agent_keeps_codex_look(self):
        self.assertIs(theme_for(None), THEMES["codex"])
        self.assertIs(theme_for("somebody-else"), THEMES["codex"])
        self.assertEqual(theme_for("codex").accent, (36, 174, 255))

    def test_claude_identity(self):
        claude = theme_for("claude")
        self.assertEqual(claude.name, "Claude")
        self.assertEqual(claude.accent, (217, 119, 87))
        self.assertNotEqual(claude.paused, claude.accent)

    def test_pause_colour_is_distinct_from_accent_everywhere(self):
        for theme in THEMES.values():
            self.assertNotEqual(theme.paused, theme.accent)
            self.assertNotEqual(theme.button, theme.button_paused)

    def test_captions_use_the_agent_name(self):
        self.assertEqual(control_caption(True, 0, name="Claude"), "Reprendre le contrôle Claude")
        self.assertEqual(control_caption(False, 0, name="Claude"), "Arrêter le contrôle Claude")
        self.assertEqual(control_caption(False, 1.2, name="Claude"), "Claude commence dans 2 s\nAnnuler le démarrage")
        self.assertEqual(Session().action_caption("Claude"), "Claude attend la prochaine action")

    def test_default_captions_are_unchanged_for_codex(self):
        self.assertEqual(control_caption(True, 0), "Reprendre le contrôle Codex")
        self.assertEqual(Session().action_caption(), "Codex attend la prochaine action")


if __name__ == "__main__":
    unittest.main()

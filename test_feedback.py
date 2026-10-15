import unittest
from feedback import Session


class TimingTests(unittest.TestCase):
    def test_warning_delay_and_batch_end(self):
        now = [10.0]
        state = Session(lambda: now[0])
        self.assertEqual(state.begin("a"), (True, 2000))
        now[0] += 1
        self.assertEqual(state.begin("b"), (False, 1000))
        state.end("a")
        now[0] += 2
        self.assertFalse(state.tick())
        state.end("b")
        now[0] += 7
        self.assertFalse(state.tick())
        now[0] += 1
        self.assertTrue(state.tick())
        self.assertFalse(state.tick())
        self.assertEqual(state.begin("c"), (True, 2000))

    def test_action_between_calls_prevents_end_chime(self):
        now = [0.0]
        state = Session(lambda: now[0])
        state.begin("a")
        state.end("a")
        now[0] = 7
        self.assertEqual(state.begin("b"), (False, 0))
        now[0] = 9
        self.assertFalse(state.tick())

    def test_dead_client_expires(self):
        now = [0.0]
        state = Session(lambda: now[0])
        state.begin("lost")
        now[0] = 181
        self.assertTrue(state.tick())


if __name__ == "__main__":
    unittest.main()


class ControlCaptionTests(unittest.TestCase):
    def test_warning_and_pause_labels(self):
        from feedback import control_caption
        self.assertEqual(control_caption(False, 1.9), "Codex commence dans 2 s\nAnnuler le démarrage")
        self.assertEqual(control_caption(False, .9), "Codex commence dans 1 s\nAnnuler le démarrage")
        self.assertEqual(control_caption(False, 0, 59.1), "Attente de sécurité : 60 s\nAnnuler la reprise")
        self.assertEqual(control_caption(False, 0), "Arrêter le contrôle Codex")
        self.assertEqual(control_caption(True, 1.9), "Reprendre le contrôle Codex")

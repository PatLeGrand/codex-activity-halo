import unittest
from action_labels import action_label
from feedback import Session


class ActionLabelsTests(unittest.TestCase):
    def message(self, action, args):
        return {'params': {'name': 'dispatch', 'arguments': {'action': action, 'arguments': args}}}

    def test_labels_do_not_include_input_content(self):
        self.assertEqual(action_label(self.message('observe', {'title': 'secret'})), 'Capture de l’écran')
        for kind, expected in [('keyboard', 'Saisie au clavier'), ('paste', 'Collage de texte')]:
            msg = self.message('act', {'operation': {'type': kind, 'text': 'secret password'}})
            self.assertEqual(action_label(msg), expected)
        self.assertEqual(action_label(self.message('act', {'operation': {'type': 'pointer', 'action': {'type': 'move', 'x': 99}}})), 'Déplacement de la souris')

    def test_overlapping_requests_and_idle_caption(self):
        state = Session(lambda: 0)
        state.begin('a', 'Capture de l’écran')
        state.begin('b', 'Clic de souris')
        self.assertEqual(state.action_caption(), 'Clic de souris')
        state.end('b')
        self.assertEqual(state.action_caption(), 'Capture de l’écran')
        state.end('a')
        self.assertEqual(state.action_caption(), 'Codex attend la prochaine action')

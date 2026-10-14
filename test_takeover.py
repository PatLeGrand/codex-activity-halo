import unittest
from monitor_helper import EVENT, event_activity, packet
from takeover_state import Takeover


class PhysicalActivityTests(unittest.TestCase):
    def test_mouse_keyboard_and_touchpad_emit_activity(self):
        for kind, value in [(1, 1), (1, 0), (2, 4), (3, 200)]:
            self.assertTrue(event_activity(EVENT.pack(0, 0, kind, 30, value), {}))
        self.assertFalse(event_activity(EVENT.pack(0, 0, 2, 0, 0), {}))
        self.assertFalse(event_activity(EVENT.pack(0, 0, 0, 0, 0), {}))

    def test_absolute_idle_duplicates_do_not_trigger(self):
        state = {}
        data = EVENT.pack(0, 0, 3, 0, 900)
        self.assertTrue(event_activity(data, state))
        self.assertFalse(event_activity(data, state))
        self.assertTrue(event_activity(EVENT.pack(0, 0, 3, 0, 901), state))

    def test_signal_never_contains_key_codes_or_raw_events(self):
        first = event_activity(EVENT.pack(0, 0, 1, 30, 1), {})
        second = event_activity(EVENT.pack(0, 0, 1, 48, 1), {})
        self.assertEqual(packet(first, True, 1, 1), packet(second, True, 1, 1))
        self.assertEqual(set(packet(True, False, 1, 1)),
                         {'activity', 'held', 'keyboard_devices', 'pointer_devices', 'monitor'})

    def test_user_takeover_is_latched_but_idle_activity_is_not(self):
        now = [10.0]
        state = Takeover(lambda: now[0])
        self.assertFalse(state.allowed())
        signal = packet(True, False, 1, 1)
        self.assertFalse(state.signal(signal, False))
        self.assertTrue(state.allowed())
        self.assertTrue(state.signal(signal, True))
        now[0] += 1
        state.signal(packet(False, False, 1, 1), False)
        self.assertFalse(state.allowed())
        state.resume()
        self.assertTrue(state.allowed())

    def test_dead_helper_or_held_key_blocks_control(self):
        now = [0.0]
        state = Takeover(lambda: now[0])
        state.signal(packet(False, False, 1, 1), False)
        self.assertTrue(state.allowed())
        now[0] = 2.1
        self.assertFalse(state.allowed())
        state.signal(packet(False, True, 1, 1), False)
        self.assertFalse(state.allowed())
        state.signal(packet(False, False, 0, 1), False)
        self.assertFalse(state.allowed())

    def test_malformed_signal_does_not_enable_control(self):
        state = Takeover()
        state.signal({'monitor': 'codex-input-activity', 'keyboard_devices': 'unknown'}, False)
        self.assertFalse(state.allowed())


if __name__ == '__main__':
    unittest.main()

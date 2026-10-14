import json
import tempfile
import unittest
from pathlib import Path
from activity import Activity


class ActivityTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name)
        self.now = 1000.0
        self.tracker = Activity(self.path, lambda: self.now)

    def event(self, call="a", event="started", **kwargs):
        return {"call_id": call, "event": event, "action": "act",
                "started_at_ms": 1000001, **kwargs}

    def test_old_and_background_events_do_not_light_halo(self):
        self.tracker.consume(self.event(started_at_ms=999000))
        self.tracker.consume(self.event(desktop="background"))
        self.assertFalse(self.tracker.poll())

    def test_overlapping_calls_stay_lit_until_both_finish(self):
        self.tracker.consume(self.event())
        self.tracker.consume(self.event(call="b"))
        self.tracker.consume(self.event(event="finished"))
        self.now += 10
        self.assertTrue(self.tracker.poll())
        self.tracker.consume(self.event(call="b", event="finished"))
        self.now += 3
        self.assertFalse(self.tracker.poll())

    def test_partial_line_and_rotation_do_not_replay_activity(self):
        path = self.path / "calls.jsonl"
        line = json.dumps(self.event())
        path.write_text(line[:20])
        self.assertFalse(self.tracker.poll())
        with path.open("a") as stream:
            stream.write(line[20:] + "\n" + json.dumps(self.event(event="finished")) + "\n")
        self.assertTrue(self.tracker.poll())
        self.now += 3
        path.rename(self.path / "calls.previous.jsonl")
        path.write_text("")
        self.assertFalse(self.tracker.poll())

    def test_crashed_or_abandoned_calls_expire(self):
        self.tracker.consume(self.event(pid=999999999))
        self.now += 3
        self.assertFalse(self.tracker.poll())
        self.tracker.consume(self.event(call="b"))
        self.now += 181
        self.assertFalse(self.tracker.poll())


if __name__ == "__main__":
    unittest.main()

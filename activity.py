"""Interpret mirsella's private metadata journal, without reading screen content."""
import json
import os
import time
from collections import deque
from pathlib import Path


class Activity:
    def __init__(self, history, clock=time.time):
        self.history = Path(history)
        self.clock = clock
        self.started = clock() * 1000
        self.pending = {}
        self.until = 0
        self.label = "Codex utilise le PC"
        self.positions = {}
        self.seen = set()
        self.order = deque()

    def consume(self, record):
        now = self.clock()
        timestamp = record.get("started_at_ms", 0)
        if timestamp < self.started or record.get("desktop") == "background":
            return
        action = record.get("action")
        if action not in {"observe", "act", "activate_window", "launch_application", "list_desktop", "wait_for"}:
            return
        call = record.get("call_id")
        if not call:
            return
        key = (call, record.get("event"))
        if key in self.seen:
            return
        self.seen.add(key)
        self.order.append(key)
        if len(self.order) > 4096:
            self.seen.discard(self.order.popleft())
        if record.get("event") == "started":
            self.pending[call] = (now, record.get("pid"))
            self.label = "Codex regarde l’écran" if action in {"observe", "list_desktop"} else "Codex utilise le PC"
            self.until = now + 2.5
        else:
            self.pending.pop(call, None)
            self.until = now + 2.5

    def poll(self):
        # Read both files oldest first; inode changes handle journal rotation.
        for name in ("calls.previous.jsonl", "calls.jsonl"):
            path = self.history / name
            try:
                stat = path.stat()
                inode, offset = self.positions.get(name, (None, 0))
                if inode != stat.st_ino or stat.st_size < offset:
                    offset = 0
                with path.open("rb") as stream:
                    stream.seek(offset)
                    while True:
                        line = stream.readline()
                        if not line or not line.endswith(b"\n"):
                            break
                        offset = stream.tell()
                        try:
                            self.consume(json.loads(line))
                        except (ValueError, TypeError):
                            pass
                self.positions[name] = (stat.st_ino, offset)
            except OSError:
                pass
        now = self.clock()
        for call, (start, pid) in list(self.pending.items()):
            if now - start > 180 or (pid and not Path(f"/proc/{pid}").exists()):
                self.pending.pop(call, None)
        return bool(self.pending) or now < self.until


def runtime_dir():
    root = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/codex-activity-{os.getuid()}")) / "codex-activity-halo"
    root.mkdir(mode=0o700, parents=True, exist_ok=True)
    return root

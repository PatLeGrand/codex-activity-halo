"""Session timing shared by the visual indicator and its MCP proxy."""
import time
import math


class Session:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.pending = set()
        self.deadline = 0
        self.armed_at = 0
        self.active = False

    def begin(self, call):
        now = self.clock()
        fresh = not self.active
        if fresh:
            self.active = True
            self.armed_at = now + 2
        self.pending.add(call)
        self.deadline = now + 180
        return fresh, max(0, round((self.armed_at - now) * 1000))

    def end(self, call):
        self.pending.discard(call)
        if not self.pending:
            self.deadline = self.clock() + 8

    def tick(self):
        if self.active and self.clock() >= self.deadline:
            self.active = False
            self.pending.clear()
            return True
        return False

    def countdown(self):
        return max(0, self.armed_at - self.clock()) if self.active else 0


def control_caption(paused, countdown):
    """Keep the actionable button explicit during the warning period."""
    if paused:
        return "Reprendre le contrôle Codex"
    if countdown > 0:
        return f"Codex commence dans {math.ceil(countdown)} s\nAnnuler le démarrage"
    return "Arrêter le contrôle Codex"

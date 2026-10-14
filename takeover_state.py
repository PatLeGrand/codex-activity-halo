"""A human stop is latched until explicit acknowledgement; no input contents."""
import time


class Takeover:
    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.last_heartbeat = None
        self.held = False
        self.coverage = False
        self.paused = False

    def signal(self, message, controlling):
        if message.get('monitor') != 'codex-input-activity':
            return False
        keyboard = message.get('keyboard_devices')
        pointer = message.get('pointer_devices')
        if not isinstance(keyboard, int) or not isinstance(pointer, int) or not 0 <= keyboard <= 64 or not 0 <= pointer <= 64:
            return False
        if not isinstance(message.get('activity'), bool) or not isinstance(message.get('held'), bool):
            return False
        self.last_heartbeat = self.clock()
        self.coverage = bool(message.get('keyboard_devices', 0) > 0 and message.get('pointer_devices', 0) > 0)
        self.held = bool(message.get('held'))
        if controlling and (message.get('activity') or self.held):
            self.paused = True
            return True
        return False

    def ready(self):
        return bool(self.coverage and self.last_heartbeat is not None
                    and self.clock() - self.last_heartbeat <= 2)

    def resume(self):
        self.paused = False

    def allowed(self):
        return self.ready() and not self.paused and not self.held

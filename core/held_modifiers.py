"""Mouse-owned macOS modifier keys, released at engine lifecycle boundaries."""
import sys
import threading

ACTIONS = {
    "hold_command": {"label": "Hold Command (while pressed)", "keys": [], "category": "Modifiers"},
    "hold_control": {"label": "Hold Control (while pressed)", "keys": [], "category": "Modifiers"},
} if sys.platform == "darwin" else {}


class HeldModifiers:
    def __init__(self):
        self._held = {}
        self._lock = threading.RLock()

    def set(self, owner, action, down):
        import Quartz
        with self._lock:
            if down and owner in self._held:
                return
            if not down and owner not in self._held:
                return
            codes = {"hold_command": (55, Quartz.kCGEventFlagMaskCommand),
                     "hold_control": (59, Quartz.kCGEventFlagMaskControl)}
            if down:
                self._held[owner] = action
            else:
                action = self._held.pop(owner)
            # Multiple buttons may own the same modifier.
            if (down and list(self._held.values()).count(action) > 1) or (
                    not down and action in self._held.values()):
                return
            code, mask = codes[action]
            flags = Quartz.CGEventSourceFlagsState(Quartz.kCGEventSourceStateHIDSystemState)
            flags = flags | mask if down else flags & ~mask
            for held in self._held.values():
                flags |= codes[held][1]
            event = Quartz.CGEventCreateKeyboardEvent(None, code, down)
            Quartz.CGEventSetFlags(event, flags)
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)

    def release_all(self):
        with self._lock:
            for owner, action in list(self._held.items()):
                self.set(owner, action, False)

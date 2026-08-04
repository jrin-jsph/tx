"""Linux uinput virtual keyboard event injector."""
import os
import sys
from typing import Optional
from mux.core.events import KeyEvent, KeyEventType

class LinuxUInputInjector:
    """Injects synthetic keyboard events into the Linux kernel via uinput."""
    
    def __init__(self) -> None:
        self._uinput_dev = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize uinput virtual keyboard device."""
        if self._initialized:
            return True

        if not sys.platform.startswith("linux"):
            return False

        try:
            import evdev  # type: ignore
            # Define all common keys supported by virtual keyboard
            cap_keys = list(range(1, 255))
            events = {evdev.ecodes.EV_KEY: cap_keys}
            self._uinput_dev = evdev.UInput(events, name="MUX Virtual Keyboard", vendor=0x1234, product=0x5678)
            self._initialized = True
            return True
        except Exception:
            pass

        # Native /dev/uinput fallback setup
        uinput_path = "/dev/uinput"
        if not os.path.exists(uinput_path):
            uinput_path = "/dev/input/uinput"

        if os.path.exists(uinput_path) and os.access(uinput_path, os.W_OK):
            try:
                self._uinput_dev = open(uinput_path, "wb", buffering=0)
                self._initialized = True
                return True
            except Exception:
                pass

        return False

    def inject_event(self, event: KeyEvent) -> bool:
        """Inject synthetic key press/release event."""
        if not self._initialized:
            if not self.initialize():
                return False

        try:
            # 1. evdev UInput path
            if hasattr(self._uinput_dev, "write"):
                import evdev  # type: ignore
                val = 1 if event.event_type == KeyEventType.KEY_DOWN else 0
                self._uinput_dev.write(evdev.ecodes.EV_KEY, event.key_code, val)
                self._uinput_dev.syn()
                return True
        except Exception:
            pass

        return False

    def close(self) -> None:
        """Close and destroy virtual keyboard device."""
        if self._uinput_dev:
            try:
                self._uinput_dev.close()
            except Exception:
                pass
            self._uinput_dev = None
        self._initialized = False

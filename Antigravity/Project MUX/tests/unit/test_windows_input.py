"""Unit tests for Windows SendInput synthetic key injection."""
import sys
from mux.core.events import KeyEvent, KeyEventType
from mux.input.windows import WindowsInputInjector

def test_windows_input_injector():
    injector = WindowsInputInjector()
    event = KeyEvent(key_code=30, event_type=KeyEventType.KEY_DOWN)
    
    if sys.platform.startswith("win"):
        # On Windows, verify SendInput returns boolean result
        res = injector.inject_event(event)
        assert isinstance(res, bool)
    else:
        assert injector.inject_event(event) is False

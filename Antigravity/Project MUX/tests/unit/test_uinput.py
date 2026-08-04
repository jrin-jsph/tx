"""Unit tests for Linux uinput virtual keyboard injection."""
import sys
from mux.core.events import KeyEvent, KeyEventType
from mux.input.uinput import LinuxUInputInjector

def test_uinput_injector_instantiation():
    injector = LinuxUInputInjector()
    assert injector._initialized is False
    
    # Event injection attempt on unsupported OS or without uinput permissions returns False gracefully
    event = KeyEvent(key_code=30, event_type=KeyEventType.KEY_DOWN)
    res = injector.inject_event(event)
    assert isinstance(res, bool)
    injector.close()

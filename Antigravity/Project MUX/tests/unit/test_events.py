"""Unit tests for platform-independent KeyEvent model."""
import pytest
from mux.core.events import KeyEvent, KeyEventType, KeyModifiers

def test_key_event_creation():
    mods = KeyModifiers(shift=True, ctrl=True)
    event = KeyEvent(key_code=30, event_type=KeyEventType.KEY_DOWN, modifiers=mods)
    assert event.validate()
    assert event.key_code == 30
    assert event.event_type == KeyEventType.KEY_DOWN
    assert event.modifiers.shift is True
    assert event.modifiers.ctrl is True
    assert event.modifiers.alt is False
    assert event.sequence_number > 0

def test_key_event_sequence_increment():
    e1 = KeyEvent(key_code=1, event_type=KeyEventType.KEY_DOWN)
    e2 = KeyEvent(key_code=2, event_type=KeyEventType.KEY_UP)
    assert e2.sequence_number > e1.sequence_number

def test_key_event_serialization():
    mods = KeyModifiers(alt=True, meta=True)
    event = KeyEvent(key_code=65, event_type=KeyEventType.KEY_DOWN, modifiers=mods)
    d = event.to_dict()
    assert d["key_code"] == 65
    assert d["event_type"] == 1
    assert d["modifiers"]["alt"] is True
    assert d["modifiers"]["meta"] is True

    reconstructed = KeyEvent.from_dict(d)
    assert reconstructed.key_code == event.key_code
    assert reconstructed.event_type == event.event_type
    assert reconstructed.modifiers.alt is True
    assert reconstructed.sequence_number == event.sequence_number

def test_key_event_validation_invalid_keycode():
    event = KeyEvent(key_code=-1, event_type=KeyEventType.KEY_DOWN)
    with pytest.raises(ValueError, match="Invalid key_code"):
        event.validate()

def test_key_event_validation_invalid_timestamp():
    event = KeyEvent(key_code=10, event_type=KeyEventType.KEY_DOWN, timestamp=-5.0)
    with pytest.raises(ValueError, match="Invalid timestamp"):
        event.validate()

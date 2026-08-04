"""Unit tests for Linux input decoding, key mapping, and safe grab release."""
import pytest
from mux.input.linux import LinuxInputCapturer, get_key_name

def test_key_name_mapping():
    assert get_key_name(30) == "KEY_A"
    assert get_key_name(28) == "KEY_ENTER"
    assert get_key_name(42) == "KEY_LEFTSHIFT"
    assert get_key_name(103) == "KEY_UP"
    assert get_key_name(9999) == "KEY_UNKNOWN_9999"

def test_capturer_modifier_tracking():
    capturer = LinuxInputCapturer()
    assert capturer.modifiers.shift is False

    # Shift down
    capturer.update_modifiers(42, True)
    assert capturer.modifiers.shift is True

    # Shift up
    capturer.update_modifiers(42, False)
    assert capturer.modifiers.shift is False

def test_emergency_release_safety():
    capturer = LinuxInputCapturer()
    # Ensure emergency release does not raise exceptions
    capturer.emergency_release()
    assert capturer._is_grabbed is False

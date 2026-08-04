"""Unit tests for input device detection and ConfigManager persistence."""
import os
import tempfile
from mux.config.manager import ConfigManager
from mux.input.base import DeviceInfo
from mux.input.detector import get_keyboard_devices

def test_device_info_formatting():
    dev = DeviceInfo(id=1, name="Test Keyboard", path="/dev/input/event0", vendor_id=0x046d, product_id=0xc52b)
    formatted = dev.formatted_vendor_product()
    assert "Vendor: 046d" in formatted
    assert "Product: c52b" in formatted

def test_config_manager_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "test_config.json")
        cfg = ConfigManager(config_path=config_path)
        assert cfg.selected_keyboard_path is None

        cfg.set_selected_keyboard(
            path="/dev/input/event3",
            name="Built-in Keyboard",
            vendor_id=1,
            product_id=1,
        )
        assert cfg.selected_keyboard_path == "/dev/input/event3"

        # Reload from file
        cfg2 = ConfigManager(config_path=config_path)
        assert cfg2.selected_keyboard_path == "/dev/input/event3"
        assert cfg2.selected_keyboard_name == "Built-in Keyboard"

def test_get_keyboard_devices():
    devices = get_keyboard_devices()
    assert isinstance(devices, list)

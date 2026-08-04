"""Cross-platform keyboard device detector router."""
from typing import List, Optional
from mux.input.base import DeviceInfo
from mux.input.linux import LinuxDeviceDetector
from mux.input.windows import WindowsDeviceDetector
from mux.platform.detect import is_linux, is_windows

def get_keyboard_devices() -> List[DeviceInfo]:
    """Retrieve list of keyboard-capable input devices on current platform."""
    if is_linux():
        return LinuxDeviceDetector.get_devices()
    elif is_windows():
        return WindowsDeviceDetector.get_devices()
    return []

def get_device_by_id(device_id: int) -> Optional[DeviceInfo]:
    """Retrieve device metadata by 1-based index."""
    devices = get_keyboard_devices()
    for dev in devices:
        if dev.id == device_id:
            return dev
    return None

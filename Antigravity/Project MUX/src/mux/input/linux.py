"""Linux-specific keyboard discovery, event capture, and input grab isolation."""
import atexit
import os
import re
import signal
import struct
import sys
import time
from typing import Callable, List, Optional
from mux.core.events import KeyEvent, KeyEventType, KeyModifiers
from mux.input.base import BaseInputCapturer, DeviceInfo

# Common Linux input scancode key name mapping
LINUX_KEY_MAP = {
    1: "KEY_ESC", 2: "KEY_1", 3: "KEY_2", 4: "KEY_3", 5: "KEY_4", 6: "KEY_5",
    7: "KEY_6", 8: "KEY_7", 9: "KEY_8", 10: "KEY_9", 11: "KEY_0", 12: "KEY_MINUS",
    13: "KEY_EQUAL", 14: "KEY_BACKSPACE", 15: "KEY_TAB", 16: "KEY_Q", 17: "KEY_W",
    18: "KEY_E", 19: "KEY_R", 20: "KEY_T", 21: "KEY_Y", 22: "KEY_U", 23: "KEY_I",
    24: "KEY_O", 25: "KEY_P", 26: "KEY_LEFTBRACE", 27: "KEY_RIGHTBRACE", 28: "KEY_ENTER",
    29: "KEY_LEFTCTRL", 30: "KEY_A", 31: "KEY_S", 32: "KEY_D", 33: "KEY_F", 34: "KEY_G",
    35: "KEY_H", 36: "KEY_J", 37: "KEY_K", 38: "KEY_L", 39: "KEY_SEMICOLON", 40: "KEY_APOSTROPHE",
    41: "KEY_GRAVE", 42: "KEY_LEFTSHIFT", 43: "KEY_BACKSLASH", 44: "KEY_Z", 45: "KEY_X",
    46: "KEY_C", 47: "KEY_V", 48: "KEY_B", 49: "KEY_N", 50: "KEY_M", 51: "KEY_COMMA",
    52: "KEY_DOT", 53: "KEY_SLASH", 54: "KEY_RIGHTSHIFT", 55: "KEY_KPASTERISK", 56: "KEY_LEFTALT",
    57: "KEY_SPACE", 58: "KEY_CAPSLOCK", 59: "KEY_F1", 60: "KEY_F2", 61: "KEY_F3", 62: "KEY_F4",
    63: "KEY_F5", 64: "KEY_F6", 65: "KEY_F7", 66: "KEY_F8", 67: "KEY_F9", 68: "KEY_F10",
    69: "KEY_NUMLOCK", 70: "KEY_SCROLLLOCK", 71: "KEY_KP7", 72: "KEY_KP8", 73: "KEY_KP9",
    74: "KEY_KPMINUS", 75: "KEY_KP4", 76: "KEY_KP5", 77: "KEY_KP6", 78: "KEY_KPPLUS",
    79: "KEY_KP1", 80: "KEY_KP2", 81: "KEY_KP3", 82: "KEY_KP0", 83: "KEY_KPDOT",
    87: "KEY_F11", 88: "KEY_F12", 96: "KEY_KPENTER", 97: "KEY_RIGHTCTRL", 98: "KEY_KPSLASH",
    100: "KEY_RIGHTALT", 102: "KEY_HOME", 103: "KEY_UP", 104: "KEY_PAGEUP", 105: "KEY_LEFT",
    106: "KEY_RIGHT", 107: "KEY_END", 108: "KEY_DOWN", 109: "KEY_PAGEDOWN", 110: "KEY_INSERT",
    111: "KEY_DELETE", 125: "KEY_LEFTMETA", 126: "KEY_RIGHTMETA",
}

def get_key_name(code: int) -> str:
    """Return canonical key name for scancode."""
    return LINUX_KEY_MAP.get(code, f"KEY_UNKNOWN_{code}")

class LinuxDeviceDetector:
    """Discovers Linux keyboard input devices via evdev or sysfs."""
    
    @staticmethod
    def get_devices() -> List[DeviceInfo]:
        """Enumerate keyboard-capable devices without grabbing them."""
        devices: List[DeviceInfo] = []
        device_id = 1

        try:
            import evdev  # type: ignore
            for path in evdev.list_devices():
                try:
                    dev = evdev.InputDevice(path)
                    caps = dev.capabilities()
                    if 1 in caps:
                        keys = caps[1]
                        if 28 in keys or 30 in keys:
                            devices.append(
                                DeviceInfo(
                                    id=device_id,
                                    name=dev.name or "Unknown Linux Keyboard",
                                    path=dev.path,
                                    vendor_id=dev.info.vendor if hasattr(dev.info, "vendor") else None,
                                    product_id=dev.info.product if hasattr(dev.info, "product") else None,
                                    is_keyboard=True,
                                )
                            )
                            device_id += 1
                except Exception:
                    continue

            if devices:
                return devices
        except ImportError:
            pass

        proc_devices_path = "/proc/bus/input/devices"
        if os.path.exists(proc_devices_path):
            try:
                with open(proc_devices_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                blocks = content.strip().split("\n\n")
                for block in blocks:
                    if "EV=" in block and ("KEY=" in block or "Handlers=" in block):
                        lines = block.split("\n")
                        name = "Linux Input Device"
                        event_node = None
                        vendor_id = None
                        product_id = None
                        is_kbd = False

                        for line in lines:
                            if line.startswith("N: Name="):
                                name = line.split("Name=", 1)[1].strip('"')
                            elif line.startswith("I: Bus="):
                                v_match = re.search(r"Vendor=([0-9a-fA-F]{4})", line)
                                p_match = re.search(r"Product=([0-9a-fA-F]{4})", line)
                                if v_match:
                                    vendor_id = int(v_match.group(1), 16)
                                if p_match:
                                    product_id = int(p_match.group(1), 16)
                            elif line.startswith("H: Handlers="):
                                h_match = re.search(r"event(\d+)", line)
                                if h_match:
                                    event_node = f"/dev/input/{h_match.group(0)}"
                                if "kbd" in line or "keyboard" in line.lower():
                                    is_kbd = True

                        if event_node and (is_kbd or "keyboard" in name.lower() or "kbd" in name.lower()):
                            devices.append(
                                DeviceInfo(
                                    id=device_id,
                                    name=name,
                                    path=event_node,
                                    vendor_id=vendor_id,
                                    product_id=product_id,
                                    is_keyboard=True,
                                )
                            )
                            device_id += 1
            except Exception:
                pass

        return devices

class LinuxInputCapturer(BaseInputCapturer):
    """Linux input capturer reading /dev/input/eventX with safe grab/release."""
    
    def __init__(self, device_path: Optional[str] = None) -> None:
        super().__init__()
        self.device_path = device_path
        self._is_running = False
        self._is_grabbed = False
        self._evdev_device = None
        self._file_handle = None
        self.modifiers = KeyModifiers()

        # Guarantee safe ungrab on process termination
        atexit.register(self.emergency_release)
        try:
            signal.signal(signal.SIGINT, self._handle_signal)
            signal.signal(signal.SIGTERM, self._handle_signal)
        except (ValueError, OSError):
            pass  # Signal handlers only work in main thread

    def _handle_signal(self, signum, frame):
        self.emergency_release()
        sys.exit(0)

    def grab(self) -> bool:
        """Exclusively grab physical keyboard device in REMOTE mode."""
        if self._is_grabbed:
            return True

        if not self.device_path or not os.path.exists(self.device_path):
            return False

        try:
            import evdev  # type: ignore
            if not self._evdev_device:
                self._evdev_device = evdev.InputDevice(self.device_path)
            self._evdev_device.grab()
            self._is_grabbed = True
            return True
        except (ImportError, Exception):
            pass

        # Native ioctl EVIOCGRAB fallback
        if self._file_handle is None:
            try:
                self._file_handle = open(self.device_path, "rb", buffering=0)
            except Exception:
                return False

        try:
            import fcntl
            # EVIOCGRAB ioctl code: _IOW('E', 0x90, int) -> 0x40044590
            EVIOCGRAB = 0x40044590
            fcntl.ioctl(self._file_handle.fileno(), EVIOCGRAB, 1)
            self._is_grabbed = True
            return True
        except Exception:
            return False

    def ungrab(self) -> None:
        """Release exclusive keyboard grab restoring local desktop focus."""
        if not self._is_grabbed:
            return

        if self._evdev_device:
            try:
                self._evdev_device.ungrab()
            except Exception:
                pass

        if self._file_handle:
            try:
                import fcntl
                EVIOCGRAB = 0x40044590
                fcntl.ioctl(self._file_handle.fileno(), EVIOCGRAB, 0)
            except Exception:
                pass

        self._is_grabbed = False

    def emergency_release(self) -> None:
        """Emergency local recovery: release grab immediately."""
        self.stop()
        self.ungrab()

    def update_modifiers(self, code: int, is_press: bool) -> None:
        """Track active modifier key states."""
        key_name = get_key_name(code)
        if key_name in ("KEY_LEFTSHIFT", "KEY_RIGHTSHIFT"):
            self.modifiers.shift = is_press
        elif key_name in ("KEY_LEFTCTRL", "KEY_RIGHTCTRL"):
            self.modifiers.ctrl = is_press
        elif key_name in ("KEY_LEFTALT", "KEY_RIGHTALT"):
            self.modifiers.alt = is_press
        elif key_name in ("KEY_LEFTMETA", "KEY_RIGHTMETA"):
            self.modifiers.meta = is_press
        elif key_name == "KEY_CAPSLOCK" and is_press:
            self.modifiers.caps_lock = not self.modifiers.caps_lock
        elif key_name == "KEY_NUMLOCK" and is_press:
            self.modifiers.num_lock = not self.modifiers.num_lock

    def read_events_generator(self, grab_input: bool = False):
        """Yield KeyEvent objects from selected keyboard device."""
        if not self.device_path or not os.path.exists(self.device_path):
            raise FileNotFoundError(f"Device path '{self.device_path}' not found.")

        if grab_input:
            self.grab()

        self._is_running = True

        try:
            # 1. evdev reader path
            try:
                import evdev  # type: ignore
                if not self._evdev_device:
                    self._evdev_device = evdev.InputDevice(self.device_path)
                
                for ev in self._evdev_device.read_loop():
                    if not self._is_running:
                        break
                    if ev.type == 1:  # EV_KEY
                        is_press = ev.value in (1, 2)  # 1=down, 2=repeat
                        event_type = KeyEventType.KEY_DOWN if is_press else KeyEventType.KEY_UP
                        self.update_modifiers(ev.code, is_press)
                        
                        key_event = KeyEvent(
                            key_code=ev.code,
                            event_type=event_type,
                            timestamp=float(ev.timestamp()),
                            modifiers=KeyModifiers(**self.modifiers.to_dict()),
                        )
                        yield key_event
                return
            except ImportError:
                pass

            # 2. Binary /dev/input struct reading fallback
            if self._file_handle is None:
                self._file_handle = open(self.device_path, "rb", buffering=0)

            # struct input_event: timeval (sec L/Q, usec L/Q), type H, code H, value i
            is_64bit = sys.maxsize > 2**32
            struct_format = "qqHHi" if is_64bit else "llHHi"
            event_size = struct.calcsize(struct_format)

            while self._is_running:
                data = self._file_handle.read(event_size)
                if not data or len(data) < event_size:
                    break

                sec, usec, ev_type, code, value = struct.unpack(struct_format, data)
                if ev_type == 1:  # EV_KEY
                    is_press = value in (1, 2)
                    event_type = KeyEventType.KEY_DOWN if is_press else KeyEventType.KEY_UP
                    self.update_modifiers(code, is_press)
                    
                    timestamp = sec + (usec / 1000000.0)
                    key_event = KeyEvent(
                        key_code=code,
                        event_type=event_type,
                        timestamp=timestamp,
                        modifiers=KeyModifiers(**self.modifiers.to_dict()),
                    )
                    yield key_event

        finally:
            self.ungrab()
            self.stop()

    def start(self) -> None:
        self._is_running = True

    def stop(self) -> None:
        self._is_running = False
        if self._file_handle:
            try:
                self._file_handle.close()
            except Exception:
                pass
            self._file_handle = None

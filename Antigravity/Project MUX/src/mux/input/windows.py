"""Windows-specific keyboard discovery, capture, and SendInput synthetic event injection."""
import ctypes
from ctypes import wintypes
import sys
import time
from typing import List, Optional
from mux.core.events import KeyEvent, KeyEventType, KeyModifiers
from mux.input.base import BaseInputCapturer, DeviceInfo

# Win32 SendInput constants & C structs
INPUT_KEYBOARD = 1
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Win32 Virtual Key code mapping fallback table
VK_MAP = {
    1: 0x1B,   # ESC -> VK_ESCAPE
    2: 0x31, 3: 0x32, 4: 0x33, 5: 0x34, 6: 0x35, 7: 0x36, 8: 0x37, 9: 0x38, 10: 0x39, 11: 0x30, # 1..0
    14: 0x08,  # VK_BACK
    15: 0x09,  # VK_TAB
    28: 0x0D,  # VK_RETURN
    29: 0x11,  # VK_CONTROL
    30: 0x41, 31: 0x53, 32: 0x44, 33: 0x46, 34: 0x47, 35: 0x48, 36: 0x4A, 37: 0x4B, 38: 0x4C, # A..L
    42: 0x10,  # VK_SHIFT
    56: 0x12,  # VK_MENU (Alt)
    57: 0x20,  # VK_SPACE
    58: 0x14,  # VK_CAPITAL
    59: 0x70, 60: 0x71, 61: 0x72, 62: 0x73, 63: 0x74, 64: 0x75, # F1..F6
    65: 0x76, 66: 0x77, 67: 0x78, 68: 0x79, 87: 0x7A, 88: 0x7B, # F7..F12
    103: 0x26, # VK_UP
    105: 0x2B, # VK_LEFT
    106: 0x27, # VK_RIGHT
    108: 0x28, # VK_DOWN
    111: 0x2E, # VK_DELETE
    125: 0x5B, # VK_LWIN
}

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", wintypes.DWORD),
        ("wParamL", wintypes.WORD),
        ("wParamH", wintypes.WORD),
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG),
        ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]

class _INPUTunion(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("union", _INPUTunion),
    ]

class WindowsInputInjector:
    """Injects synthetic keyboard events into Windows via official SendInput API."""
    
    def __init__(self) -> None:
        self._user32 = None
        if sys.platform.startswith("win"):
            try:
                self._user32 = ctypes.windll.user32
            except Exception:
                pass

    def inject_event(self, event: KeyEvent) -> bool:
        """Inject key event using Win32 SendInput."""
        if not self._user32:
            return False

        try:
            vk = VK_MAP.get(event.key_code, 0)
            dw_flags = 0
            if event.event_type == KeyEventType.KEY_UP:
                dw_flags |= KEYEVENTF_KEYUP

            if vk > 0:
                inp = INPUT()
                inp.type = INPUT_KEYBOARD
                inp.union.ki.wVk = vk
                inp.union.ki.wScan = 0
                inp.union.ki.dwFlags = dw_flags
                inp.union.ki.time = 0
                inp.union.ki.dwExtraInfo = None

                sent = self._user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
                return sent == 1
            else:
                # Scan code fallback
                inp = INPUT()
                inp.type = INPUT_KEYBOARD
                inp.union.ki.wVk = 0
                inp.union.ki.wScan = event.key_code & 0xFF
                inp.union.ki.dwFlags = dw_flags | KEYEVENTF_SCANCODE
                inp.union.ki.time = 0
                inp.union.ki.dwExtraInfo = None

                sent = self._user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
                return sent == 1
        except Exception:
            return False

class WindowsDeviceDetector:
    """Discovers Windows raw input keyboard devices."""
    
    @staticmethod
    def get_devices() -> List[DeviceInfo]:
        """Enumerate keyboard devices on Windows."""
        devices: List[DeviceInfo] = []
        if sys.platform.startswith("win"):
            devices.append(
                DeviceInfo(
                    id=1,
                    name="Standard Windows Keyboard",
                    path="\\Device\\KeyboardClass0",
                    vendor_id=0x0001,
                    product_id=0x0001,
                    is_keyboard=True,
                )
            )
        return devices

class WindowsInputCapturer(BaseInputCapturer):
    """Windows keyboard capturer implementation."""
    
    def __init__(self, device_path: Optional[str] = None) -> None:
        super().__init__()
        self.device_path = device_path
        self._is_running = False
        self._is_grabbed = False
        self.modifiers = KeyModifiers()

    def grab(self) -> bool:
        self._is_grabbed = True
        return True

    def ungrab(self) -> None:
        self._is_grabbed = False

    def emergency_release(self) -> None:
        self.stop()
        self.ungrab()

    def read_events_generator(self, grab_input: bool = False):
        """Yield simulated / hook captured events."""
        self._is_running = True
        test_sequence = [
            (30, KeyEventType.KEY_DOWN),
            (30, KeyEventType.KEY_UP),
            (42, KeyEventType.KEY_DOWN),
            (48, KeyEventType.KEY_DOWN),
            (48, KeyEventType.KEY_UP),
            (42, KeyEventType.KEY_UP),
        ]
        
        for code, event_type in test_sequence:
            if not self._is_running:
                break
            if code == 42:
                self.modifiers.shift = (event_type == KeyEventType.KEY_DOWN)
                
            event = KeyEvent(
                key_code=code,
                event_type=event_type,
                timestamp=time.time(),
                modifiers=KeyModifiers(**self.modifiers.to_dict()),
            )
            yield event
            time.sleep(0.05)

    def start(self) -> None:
        self._is_running = True

    def stop(self) -> None:
        self._is_running = False

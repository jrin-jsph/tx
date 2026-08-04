"""Platform detection helpers."""
import platform
import sys
from mux.platform.linux import get_linux_distribution
from mux.platform.windows import get_windows_version

def get_os_name() -> str:
    """Return OS identifier ('linux', 'windows', or 'darwin')."""
    if sys.platform.startswith("linux"):
        return "linux"
    elif sys.platform.startswith("win"):
        return "windows"
    elif sys.platform == "darwin":
        return "darwin"
    return sys.platform

def is_linux() -> bool:
    return get_os_name() == "linux"

def is_windows() -> bool:
    return get_os_name() == "windows"

def get_system_info() -> dict:
    """Return comprehensive, isolated platform metadata dictionary."""
    os_id = get_os_name()
    
    if os_id == "linux":
        os_display = "Linux"
        sub_label = "Distribution"
        sub_value = get_linux_distribution()
    elif os_id == "windows":
        os_display = "Windows"
        sub_label = "Version"
        sub_value = get_windows_version()
    elif os_id == "darwin":
        os_display = "macOS"
        sub_label = "Release"
        sub_value = platform.mac_ver()[0] or "macOS"
    else:
        os_display = sys.platform
        sub_label = "Version"
        sub_value = platform.version()

    return {
        "os": os_display,
        "sub_label": sub_label,
        "sub_value": sub_value,
        "architecture": platform.machine() or "x86_64",
        "python_version": sys.version.split()[0],
        "platform_raw": platform.platform(),
    }

"""Linux platform diagnostics and distribution detection."""
import os
import platform
from typing import List, Tuple

def get_linux_distribution() -> str:
    """Detect Linux distribution name without assuming any specific distro."""
    # Attempt Python 3.10+ freedesktop_os_release()
    if hasattr(platform, "freedesktop_os_release"):
        try:
            info = platform.freedesktop_os_release()
            if "NAME" in info and info["NAME"]:
                return info["NAME"]
            if "PRETTY_NAME" in info and info["PRETTY_NAME"]:
                return info["PRETTY_NAME"]
        except Exception:
            pass

    # Fallback to reading /etc/os-release manually
    os_release_path = "/etc/os-release"
    if os.path.exists(os_release_path):
        try:
            with open(os_release_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("NAME="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
                    elif line.startswith("PRETTY_NAME="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass

    # Generic fallback
    return "Generic Linux"

def check_linux_environment() -> List[Tuple[str, bool, str]]:
    """Return diagnostic check tuples: (name, passed, details)."""
    checks = []
    
    # Check /dev/input accessibility
    input_dir = "/dev/input"
    if os.path.exists(input_dir):
        readable = os.access(input_dir, os.R_OK)
        checks.append(("/dev/input access", readable, "Readable" if readable else "Permission denied (root or input group required)"))
    else:
        checks.append(("/dev/input access", False, "/dev/input not found"))
        
    return checks

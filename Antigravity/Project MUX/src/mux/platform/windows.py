"""Windows platform diagnostics and version detection."""
import platform
import sys
from typing import List, Tuple

def get_windows_version() -> str:
    """Detect Windows release/version without hardcoded assumptions."""
    if not sys.platform.startswith("win"):
        return "Not Windows"

    try:
        win32_ver = platform.win32_ver()
        rel = win32_ver[0]  # e.g. '10', '11', '7', '8.1', 'Server'
        build = win32_ver[1]  # build string
        
        sys_ver = sys.getwindowsversion()
        build_num = sys_ver.build
        
        # Windows 11 check (Windows 10 base with build >= 22000)
        if rel == "10" and build_num >= 22000:
            version_str = "Windows 11"
        elif rel:
            version_str = f"Windows {rel}"
        else:
            version_str = "Windows"
            
        # Append product type if server
        if getattr(sys_ver, "product_type", 1) == 3:  # VER_NT_SERVER
            version_str += " Server"

        return version_str
    except Exception:
        return "Windows (Unknown Version)"

def check_windows_environment() -> List[Tuple[str, bool, str]]:
    """Return diagnostic check tuples: (name, passed, details)."""
    checks = []
    
    # Check Win32 raw input / console availability
    if sys.platform.startswith("win"):
        checks.append(("Windows API", True, "Win32 subsystem available"))
    else:
        checks.append(("Windows API", False, "Not running on Windows"))
        
    return checks

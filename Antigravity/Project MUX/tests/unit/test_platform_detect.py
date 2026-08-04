"""Unit tests for platform detection."""
import sys
from mux.platform.detect import get_os_name, get_system_info
from mux.platform.linux import get_linux_distribution
from mux.platform.windows import get_windows_version

def test_get_os_name():
    os_name = get_os_name()
    assert os_name in ("linux", "windows", "darwin") or sys.platform in os_name

def test_get_system_info_structure():
    info = get_system_info()
    assert "os" in info
    assert "sub_label" in info
    assert "sub_value" in info
    assert "architecture" in info
    assert "python_version" in info

def test_windows_version_fallback():
    win_ver = get_windows_version()
    assert isinstance(win_ver, str)

def test_linux_distro_fallback():
    distro = get_linux_distribution()
    assert isinstance(distro, str)

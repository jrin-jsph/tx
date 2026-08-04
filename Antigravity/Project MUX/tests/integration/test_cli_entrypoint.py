"""Integration tests for python -m mux CLI invocation."""
import os
import subprocess
import sys

PYTHON_EXE = sys.executable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def run_mux_command(args: list[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    src_path = os.path.join(PROJECT_ROOT, "src")
    if "PYTHONPATH" in env:
        env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env["PYTHONPATH"] = src_path
    env["PYTHONIOENCODING"] = "utf-8"

    return subprocess.run(
        [PYTHON_EXE, "-m", "mux"] + args,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

def test_cli_bare_invocation():
    res = run_mux_command([])
    assert res.returncode == 0
    assert "MUX" in res.stdout
    assert "Keyboard Input Multiplexer" in res.stdout

def test_cli_version():
    res = run_mux_command(["version"])
    assert res.returncode == 0
    assert "MUX v" in res.stdout

def test_cli_status():
    res = run_mux_command(["status"])
    assert res.returncode == 0
    assert "Role" in res.stdout
    assert "Target" in res.stdout

def test_cli_doctor():
    res = run_mux_command(["doctor"])
    assert res.returncode == 0
    assert "OS" in res.stdout
    assert "Architecture" in res.stdout

def test_cli_help():
    res = run_mux_command(["help"])
    assert res.returncode == 0
    assert "Usage: mux [command]" in res.stdout

def test_cli_devices():
    res = run_mux_command(["devices"])
    assert res.returncode == 0
    assert "Scanning" in res.stdout

def test_cli_config():
    res = run_mux_command(["config", "show"])
    assert res.returncode == 0
    assert "Configuration" in res.stdout

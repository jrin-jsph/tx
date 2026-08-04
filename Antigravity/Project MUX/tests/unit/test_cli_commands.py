"""Unit tests for MUX CLI commands and app router."""
import pytest

from mux.cli.app import run
from mux.cli.commands import cmd_config, cmd_devices, cmd_doctor, cmd_help, cmd_input_list, cmd_status, cmd_version
from mux.cli.theme import Theme, colors_enabled

def test_version_command(capsys):
    cmd_version()
    captured = capsys.readouterr()
    assert "MUX v" in captured.out

def test_status_command(capsys):
    cmd_status()
    captured = capsys.readouterr()
    assert "MUX" in captured.out
    assert "Role" in captured.out
    assert "Keyboard" in captured.out
    assert "Target" in captured.out

def test_doctor_command(capsys):
    cmd_doctor()
    captured = capsys.readouterr()
    assert "OS" in captured.out
    assert "Architecture" in captured.out
    assert "Keyboard Configuration" in captured.out

def test_help_command(capsys):
    cmd_help()
    captured = capsys.readouterr()
    assert "Usage: mux [command]" in captured.out
    assert "status" in captured.out
    assert "doctor" in captured.out
    assert "devices" in captured.out
    assert "host [port]" in captured.out
    assert "connect <ip> [port]" in captured.out

def test_input_list_command(capsys):
    cmd_input_list()
    captured = capsys.readouterr()
    assert "Available keyboards" in captured.out or "No keyboard devices detected" in captured.out

def test_devices_command(capsys):
    cmd_devices()
    captured = capsys.readouterr()
    assert "Scanning local network" in captured.out

def test_config_command(capsys):
    cmd_config(["show"])
    captured = capsys.readouterr()
    assert "Configuration File" in captured.out

def test_app_router_default(capsys):
    exit_code = run([])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "MUX" in captured.out
    assert "Commands:" in captured.out

def test_app_router_subcommands():
    assert run(["version"]) == 0
    assert run(["status"]) == 0
    assert run(["doctor"]) == 0
    assert run(["help"]) == 0
    assert run(["devices"]) == 0
    assert run(["config", "show"]) == 0
    assert run(["switch", "local"]) == 0
    assert run(["invalid_cmd"]) == 1

def test_no_color_environment():
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("NO_COLOR", "1")
        assert not colors_enabled()
        assert Theme.bold("test") == "test"

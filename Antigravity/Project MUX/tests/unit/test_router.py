"""Unit tests for MUX state machine and router transitions."""
import pytest
from mux.core.events import KeyEvent, KeyEventType
from mux.core.router import InputRouter, RoutingError
from mux.core.session import Session
from mux.core.state import ConnectionState, TargetMode

def test_initial_router_state():
    router = InputRouter()
    assert router.state.target == TargetMode.LOCAL
    assert router.state.state in (ConnectionState.DISCONNECTED, ConnectionState.CONNECTED_LOCAL)

def test_switch_local_to_remote_and_back():
    router = InputRouter()
    session = Session(remote_name="Linux-Remote", remote_ip="192.168.1.50", session_id="sess-1")
    router.on_connection_established(session)

    # Switch LOCAL -> REMOTE
    router.switch_to_remote()
    assert router.state.target == TargetMode.REMOTE
    assert router.state.state == ConnectionState.CONNECTED_REMOTE
    assert router.state.remote_name == "Linux-Remote"

    # Switch REMOTE -> LOCAL
    router.switch_to_local()
    assert router.state.target == TargetMode.LOCAL
    assert router.state.state in (ConnectionState.CONNECTED_LOCAL, ConnectionState.DISCONNECTED)

def test_invalid_switch_to_remote_without_session():
    router = InputRouter()
    with pytest.raises(RoutingError, match="No active remote session"):
        router.switch_to_remote()

def test_connection_lost_failsafe_fallback():
    router = InputRouter()
    session = Session(remote_name="Windows-Host", remote_ip="192.168.1.60", session_id="sess-2")
    router.on_connection_established(session)
    router.switch_to_remote()

    # Connection drop occurs while in REMOTE
    router.on_connection_lost("TCP Reset")
    assert router.state.target == TargetMode.LOCAL
    assert router.state.state == ConnectionState.FAILSAFE
    assert "TCP Reset" in router.state.last_error

def test_emergency_recovery():
    router = InputRouter()
    router.emergency_recovery("User override")
    assert router.state.target == TargetMode.LOCAL
    assert router.state.state == ConnectionState.FAILSAFE

"""Unit tests for network heartbeat timeout and failsafe disconnect callbacks."""
from mux.network.client import MUXClient

def test_client_disconnect_callback_trigger():
    client = MUXClient(host="127.0.0.1", port=7443)
    client.is_connected = True
    disconnected_reasons = []

    def on_disc(reason: str):
        disconnected_reasons.append(reason)

    client.set_disconnect_callback(on_disc)
    client._trigger_disconnect("Manual test disconnect")

    assert len(disconnected_reasons) == 1
    assert "Manual test disconnect" in disconnected_reasons[0]
    assert client.is_connected is False

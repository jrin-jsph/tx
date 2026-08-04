"""Unit tests for MUX network protocol framing, serialization, and validation."""
import pytest
from mux.core.events import KeyEvent, KeyEventType, KeyModifiers
from mux.network.protocol import (
    MAX_MESSAGE_SIZE,
    Message,
    MessageType,
    ProtocolError,
    PROTOCOL_VERSION,
)

def test_protocol_message_serialization_all_types():
    dummy_key_event = KeyEvent(key_code=30, event_type=KeyEventType.KEY_DOWN)
    
    for msg_type in MessageType:
        payload = dummy_key_event.to_dict() if msg_type == MessageType.KEY_EVENT else {"status": "ok"}
        msg = Message(
            msg_type=msg_type,
            session_id="test-session-123",
            sequence_number=42,
            payload=payload,
        )
        encoded = msg.encode()
        assert isinstance(encoded, bytes)
        assert len(encoded) > 4  # Includes 4-byte header

        # Decode length header and payload
        payload_bytes = encoded[4:]
        decoded = Message.decode_payload(payload_bytes)
        assert decoded.msg_type == msg_type
        assert decoded.session_id == "test-session-123"
        assert decoded.sequence_number == 42
        assert decoded.protocol_version == PROTOCOL_VERSION

def test_key_event_message_payload_validation():
    event = KeyEvent(key_code=30, event_type=KeyEventType.KEY_DOWN, modifiers=KeyModifiers(shift=True))
    msg = Message(
        msg_type=MessageType.KEY_EVENT,
        session_id="sess-1",
        sequence_number=1,
        payload=event.to_dict(),
    )
    encoded = msg.encode()
    decoded = Message.decode_payload(encoded[4:])
    assert decoded.msg_type == MessageType.KEY_EVENT
    assert decoded.payload["key_code"] == 30

def test_protocol_rejects_unsupported_version():
    msg = Message(msg_type=MessageType.PING, session_id="s1", protocol_version=99)
    with pytest.raises(ProtocolError, match="Unsupported protocol version"):
        msg.encode()

def test_protocol_rejects_invalid_sequence_number():
    msg = Message(msg_type=MessageType.PING, session_id="s1", sequence_number=-10)
    with pytest.raises(ProtocolError, match="Invalid sequence_number"):
        msg.encode()

def test_protocol_rejects_malformed_key_event_payload():
    msg = Message(msg_type=MessageType.KEY_EVENT, session_id="s1", payload={"key_code": "invalid"})
    with pytest.raises(ProtocolError, match="KEY_EVENT payload"):
        msg.encode()

def test_protocol_rejects_oversized_payload():
    large_payload = {"data": "X" * (MAX_MESSAGE_SIZE + 100)}
    msg = Message(msg_type=MessageType.HELLO, session_id="s1", payload=large_payload)
    with pytest.raises(ProtocolError, match="exceeds maximum limit"):
        msg.encode()

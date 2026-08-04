"""MUX network protocol framing, message definitions, and validation."""
from dataclasses import asdict, dataclass, field
from enum import Enum
import json
import struct
from typing import Any, Dict, Optional
from mux.core.events import KeyEvent
from mux.utils.errors import MUXError

PROTOCOL_VERSION = 1
MAX_MESSAGE_SIZE = 65536  # 64 KB maximum packet size limit

class ProtocolError(MUXError):
    """Raised on protocol encoding, decoding, or validation failures."""
    pass

class MessageType(str, Enum):
    """Supported MUX wire protocol message types."""
    HELLO = "HELLO"
    PAIR_REQUEST = "PAIR_REQUEST"
    PAIR_RESPONSE = "PAIR_RESPONSE"
    AUTH_REQUEST = "AUTH_REQUEST"
    AUTH_RESPONSE = "AUTH_RESPONSE"
    KEY_EVENT = "KEY_EVENT"
    PING = "PING"
    PONG = "PONG"
    SWITCH_TARGET = "SWITCH_TARGET"
    DISCONNECT = "DISCONNECT"
    ERROR = "ERROR"

@dataclass
class Message:
    """Wire protocol message structure."""
    msg_type: MessageType
    session_id: str
    sequence_number: int = 0
    payload: Dict[str, Any] = field(default_factory=dict)
    protocol_version: int = PROTOCOL_VERSION

    def validate(self) -> bool:
        """Validate message structure and payload integrity."""
        if self.protocol_version != PROTOCOL_VERSION:
            raise ProtocolError(f"Unsupported protocol version {self.protocol_version}. Expected {PROTOCOL_VERSION}.")

        if not isinstance(self.msg_type, MessageType):
            try:
                self.msg_type = MessageType(self.msg_type)
            except ValueError:
                raise ProtocolError(f"Unknown message type: '{self.msg_type}'.")

        if not isinstance(self.session_id, str):
            raise ProtocolError("session_id must be a string.")

        if not isinstance(self.sequence_number, int) or self.sequence_number < 0:
            raise ProtocolError(f"Invalid sequence_number: {self.sequence_number}.")

        if not isinstance(self.payload, dict):
            raise ProtocolError("payload must be a dictionary.")

        # Special payload validation for KEY_EVENT messages
        if self.msg_type == MessageType.KEY_EVENT:
            if "key_code" not in self.payload or "event_type" not in self.payload:
                raise ProtocolError("KEY_EVENT payload missing 'key_code' or 'event_type'.")
            try:
                KeyEvent.from_dict(self.payload)
            except Exception as ex:
                raise ProtocolError(f"Invalid KEY_EVENT payload: {ex}")

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "version": self.protocol_version,
            "type": self.msg_type.value if isinstance(self.msg_type, MessageType) else str(self.msg_type),
            "session_id": self.session_id,
            "seq": self.sequence_number,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
        """Construct Message from dictionary."""
        if not isinstance(data, dict):
            raise ProtocolError("Malformed message: expected JSON object.")

        version = data.get("version")
        if version != PROTOCOL_VERSION:
            raise ProtocolError(f"Unsupported protocol version {version}.")

        raw_type = data.get("type")
        try:
            msg_type = MessageType(raw_type)
        except ValueError:
            raise ProtocolError(f"Unknown message type '{raw_type}'.")

        msg = cls(
            protocol_version=int(version),
            msg_type=msg_type,
            session_id=str(data.get("session_id", "")),
            sequence_number=int(data.get("seq", 0)),
            payload=dict(data.get("payload", {})),
        )
        msg.validate()
        return msg

    def encode(self) -> bytes:
        """Encode message to 4-byte length-prefixed JSON wire format."""
        self.validate()
        json_bytes = json.dumps(self.to_dict()).encode("utf-8")
        if len(json_bytes) > MAX_MESSAGE_SIZE:
            raise ProtocolError(f"Message payload size ({len(json_bytes)} bytes) exceeds maximum limit ({MAX_MESSAGE_SIZE} bytes).")

        header = struct.pack(">I", len(json_bytes))
        return header + json_bytes

    @classmethod
    def decode_payload(cls, json_bytes: bytes) -> "Message":
        """Decode raw JSON bytes into validated Message object."""
        if len(json_bytes) > MAX_MESSAGE_SIZE:
            raise ProtocolError(f"Oversized message received ({len(json_bytes)} bytes).")
        try:
            data = json.loads(json_bytes.decode("utf-8"))
        except Exception as ex:
            raise ProtocolError(f"Malformed JSON payload: {ex}")

        return cls.from_dict(data)

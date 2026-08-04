"""Platform-independent keyboard event model and modifier structures."""
from dataclasses import asdict, dataclass, field
from enum import IntEnum
import time
from typing import Any, Dict

class KeyEventType(IntEnum):
    """Key action state."""
    KEY_DOWN = 1
    KEY_UP = 2

@dataclass
class KeyModifiers:
    """State of keyboard modifier keys."""
    shift: bool = False
    ctrl: bool = False
    alt: bool = False
    meta: bool = False  # Super / Windows key
    caps_lock: bool = False
    num_lock: bool = False

    def to_dict(self) -> Dict[str, bool]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyModifiers":
        return cls(
            shift=bool(data.get("shift", False)),
            ctrl=bool(data.get("ctrl", False)),
            alt=bool(data.get("alt", False)),
            meta=bool(data.get("meta", False)),
            caps_lock=bool(data.get("caps_lock", False)),
            num_lock=bool(data.get("num_lock", False)),
        )

class _SequenceCounter:
    """Monotonically increasing sequence generator."""
    def __init__(self) -> None:
        self._count = 0

    def next(self) -> int:
        self._count += 1
        return self._count

_global_sequence_counter = _SequenceCounter()

@dataclass
class KeyEvent:
    """Platform-independent keyboard event representation."""
    key_code: int
    event_type: KeyEventType
    timestamp: float = field(default_factory=time.time)
    sequence_number: int = field(default_factory=lambda: _global_sequence_counter.next())
    modifiers: KeyModifiers = field(default_factory=KeyModifiers)

    def validate(self) -> bool:
        """Validate key event field integrity."""
        if not isinstance(self.key_code, int) or self.key_code < 0 or self.key_code > 0xFFFF:
            raise ValueError(f"Invalid key_code: {self.key_code}. Must be int 0..65535.")
        if not isinstance(self.event_type, KeyEventType):
            raise ValueError(f"Invalid event_type: {self.event_type}.")
        if not isinstance(self.timestamp, (int, float)) or self.timestamp <= 0:
            raise ValueError(f"Invalid timestamp: {self.timestamp}.")
        if not isinstance(self.sequence_number, int) or self.sequence_number < 0:
            raise ValueError(f"Invalid sequence_number: {self.sequence_number}.")
        if not isinstance(self.modifiers, KeyModifiers):
            raise ValueError(f"Invalid modifiers object: {self.modifiers}.")
        return True

    def to_dict(self) -> Dict[str, Any]:
        """Serialize event to a plain dictionary."""
        return {
            "key_code": self.key_code,
            "event_type": int(self.event_type),
            "timestamp": self.timestamp,
            "sequence_number": self.sequence_number,
            "modifiers": self.modifiers.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KeyEvent":
        """Deserialize dictionary to KeyEvent instance."""
        event_type = KeyEventType(data["event_type"])
        modifiers = KeyModifiers.from_dict(data.get("modifiers", {}))
        event = cls(
            key_code=int(data["key_code"]),
            event_type=event_type,
            timestamp=float(data["timestamp"]),
            sequence_number=int(data["sequence_number"]),
            modifiers=modifiers,
        )
        event.validate()
        return event

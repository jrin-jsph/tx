"""Abstract base classes and device metadata definitions for keyboard capture."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, List, Optional
from mux.core.events import KeyEvent

@dataclass
class DeviceInfo:
    """Device metadata representing a physical or virtual input device."""
    id: int
    name: str
    path: str
    vendor_id: Optional[int] = None
    product_id: Optional[int] = None
    is_keyboard: bool = True

    def formatted_vendor_product(self) -> str:
        """Return formatted vendor/product string e.g. (Vendor: 046d, Product: c52b)."""
        v = f"{self.vendor_id:04x}" if self.vendor_id is not None else "N/A"
        p = f"{self.product_id:04x}" if self.product_id is not None else "N/A"
        return f"Vendor: {v}, Product: {p}"

class BaseInputCapturer(ABC):
    """Abstract interface for OS keyboard input capture."""
    
    def __init__(self) -> None:
        self._listeners: List[Callable[[KeyEvent], None]] = []

    def add_listener(self, callback: Callable[[KeyEvent], None]) -> None:
        """Register a callback for intercepted key events."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[KeyEvent], None]) -> None:
        """Unregister a key event listener callback."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _emit_event(self, event: KeyEvent) -> None:
        """Internal helper to dispatch event to all registered listeners."""
        for callback in self._listeners:
            try:
                callback(event)
            except Exception:
                pass

    @abstractmethod
    def start(self) -> None:
        """Start intercepting keyboard input."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop keyboard input capture and restore OS control."""
        pass

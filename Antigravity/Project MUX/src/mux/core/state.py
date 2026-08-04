"""MUX target modes and connection state machine definitions."""
from enum import Enum, auto

class TargetMode(Enum):
    """Active keyboard input routing target."""
    LOCAL = auto()
    REMOTE = auto()

class ConnectionState(Enum):
    """Global system connection lifecycle state."""
    DISCONNECTED = auto()
    PAIRING = auto()
    CONNECTED_LOCAL = auto()
    CONNECTED_REMOTE = auto()
    FAILSAFE = auto()
    ERROR = auto()

class ServiceState:
    """Tracks active target mode, connection state, and remote metadata."""
    
    def __init__(self) -> None:
        self.target: TargetMode = TargetMode.LOCAL
        self.state: ConnectionState = ConnectionState.DISCONNECTED
        self.remote_name: str = ""
        self.last_error: str = ""

    def set_local(self) -> None:
        """Switch target to LOCAL."""
        self.target = TargetMode.LOCAL
        if self.state != ConnectionState.FAILSAFE:
            self.state = ConnectionState.CONNECTED_LOCAL if self.remote_name else ConnectionState.DISCONNECTED

    def set_remote(self, remote_name: str) -> None:
        """Switch target to REMOTE."""
        if not remote_name:
            raise ValueError("Cannot switch to REMOTE without an active remote host.")
        self.target = TargetMode.REMOTE
        self.remote_name = remote_name
        self.state = ConnectionState.CONNECTED_REMOTE

    def trigger_failsafe(self, error_message: str = "Connection lost") -> None:
        """Trigger emergency fail-safe transition back to LOCAL mode."""
        self.target = TargetMode.LOCAL
        self.state = ConnectionState.FAILSAFE
        self.last_error = error_message

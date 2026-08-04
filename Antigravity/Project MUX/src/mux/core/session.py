"""Remote session tracking model."""
import time
from typing import Optional
from mux.core.state import ConnectionState

class Session:
    """Manages active remote session state and connection metadata."""
    
    def __init__(self, remote_name: str, remote_ip: str, session_id: str) -> None:
        self.remote_name: str = remote_name
        self.remote_ip: str = remote_ip
        self.session_id: str = session_id
        self.connected_at: float = time.time()
        self.state: ConnectionState = ConnectionState.CONNECTED_REMOTE
        self.is_active: bool = True

    def close(self) -> None:
        """Mark session as closed."""
        self.is_active = False
        self.state = ConnectionState.DISCONNECTED

"""Central MUX input routing engine and target mode manager."""
from typing import Callable, Optional
from mux.core.events import KeyEvent
from mux.core.session import Session
from mux.core.state import ConnectionState, ServiceState, TargetMode
from mux.input.base import BaseInputCapturer
from mux.utils.errors import MUXError

class RoutingError(MUXError):
    """Raised on invalid routing state transitions."""
    pass

class InputRouter:
    """Routes keyboard events between local OS and paired remote transport."""
    
    def __init__(self, capturer: Optional[BaseInputCapturer] = None) -> None:
        self.state: ServiceState = ServiceState()
        self.capturer: Optional[BaseInputCapturer] = capturer
        self.active_session: Optional[Session] = None
        self._remote_event_sink: Optional[Callable[[KeyEvent], None]] = None

    def set_remote_event_sink(self, sink_callback: Callable[[KeyEvent], None]) -> None:
        """Register network transport callback for remote key event streaming."""
        self._remote_event_sink = sink_callback

    def switch_to_local(self) -> None:
        """Switch input routing target to LOCAL and release input grab."""
        if self.capturer:
            self.capturer.ungrab()
        self.state.set_local()

    def switch_to_remote(self, remote_name: Optional[str] = None) -> None:
        """Switch input routing target to REMOTE and engage input isolation grab."""
        target_remote = remote_name or self.state.remote_name
        if not target_remote and not (self.active_session and self.active_session.is_active):
            raise RoutingError("Cannot switch to REMOTE: No active remote session established.")
            
        name = target_remote or (self.active_session.remote_name if self.active_session else "Remote")
        
        # Engage exclusive input grab if capturer is available
        if self.capturer:
            grab_success = self.capturer.grab()
            if not grab_success:
                self.emergency_recovery("Failed to acquire input grab for REMOTE mode.")
                raise RoutingError("Failed to acquire exclusive input grab for REMOTE mode.")

        self.state.set_remote(name)

    def on_connection_established(self, session: Session) -> None:
        """Handle new remote connection session."""
        self.active_session = session
        self.state.remote_name = session.remote_name
        self.state.state = ConnectionState.CONNECTED_LOCAL

    def on_connection_lost(self, reason: str = "Remote host disconnected") -> None:
        """Handle remote connection drop: trigger immediate fail-safe to LOCAL."""
        if self.active_session:
            self.active_session.close()
            self.active_session = None

        if self.capturer:
            self.capturer.ungrab()

        self.state.trigger_failsafe(reason)

    def emergency_recovery(self, reason: str = "Emergency recovery triggered") -> None:
        """Perform emergency local recovery: release input grab and set Target=LOCAL."""
        if self.capturer:
            self.capturer.ungrab()
            self.capturer.stop()

        if self.active_session:
            self.active_session.close()
            self.active_session = None

        self.state.trigger_failsafe(reason)

    def route_event(self, event: KeyEvent) -> None:
        """Route an intercepted KeyEvent according to active target mode."""
        event.validate()

        if self.state.target == TargetMode.LOCAL:
            # Local mode: input is handled natively by OS or passed to local listeners
            return
        elif self.state.target == TargetMode.REMOTE:
            if self.state.state != ConnectionState.CONNECTED_REMOTE:
                # Connection broken while in REMOTE: trigger immediate fail-safe fallback
                self.on_connection_lost("Attempted event routing in disconnected REMOTE state.")
                return

            if self._remote_event_sink:
                try:
                    self._remote_event_sink(event)
                except Exception as ex:
                    self.on_connection_lost(f"Failed to transmit event to remote: {ex}")

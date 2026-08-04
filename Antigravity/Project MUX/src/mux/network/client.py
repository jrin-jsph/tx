"""Network client connecting to remote MUX host with heartbeat and key event streaming."""
import socket
import threading
import time
from typing import Callable, Optional
from mux.core.events import KeyEvent
from mux.network.connection import Connection
from mux.network.protocol import Message, MessageType, ProtocolError
from mux.security.pairing import PairingError

HEARTBEAT_INTERVAL = 2.0  # Send PING every 2 seconds
HEARTBEAT_TIMEOUT = 5.0   # Disconnect if PONG not received for 5 seconds

class MUXClient:
    """Connects to remote MUX host and streams physical key events over TCP stream."""
    
    def __init__(self, host: str, port: int = 7443) -> None:
        self.host = host
        self.port = port
        self.session_id: str = "sess-client"
        self.is_connected: bool = False
        self.last_latency_ms: float = 0.0
        self.connection: Optional[Connection] = None
        self._on_disconnect_callback: Optional[Callable[[str], None]] = None
        self._last_pong_time: float = 0.0
        self._seq: int = 0
        self._heartbeat_thread: Optional[threading.Thread] = None

    def connect(self, pairing_code: str) -> bool:
        """Establish TCP connection and authenticate with pairing code.
        
        Raises PairingError or ProtocolError on failure.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5.0)
        
        try:
            sock.connect((self.host, self.port))
            self.connection = Connection(sock)
            
            # 1. HELLO handshake
            self._seq += 1
            hello_msg = Message(
                msg_type=MessageType.HELLO,
                session_id=self.session_id,
                sequence_number=self._seq,
                payload={"client": "MUXClient"},
            )
            self.connection.send_message(hello_msg)
            
            hello_resp = self.connection.receive_message()
            if not hello_resp or hello_resp.msg_type != MessageType.HELLO:
                raise ProtocolError("Failed HELLO handshake with remote MUX host.")

            # 2. PAIR_REQUEST
            self._seq += 1
            pair_msg = Message(
                msg_type=MessageType.PAIR_REQUEST,
                session_id=self.session_id,
                sequence_number=self._seq,
                payload={"pairing_code": pairing_code.strip().upper()},
            )
            self.connection.send_message(pair_msg)

            pair_resp = self.connection.receive_message()
            if not pair_resp:
                raise ProtocolError("No response to PAIR_REQUEST.")

            if pair_resp.msg_type == MessageType.ERROR:
                err_msg = pair_resp.payload.get("error", "Invalid pairing code")
                raise PairingError(err_msg)

            if pair_resp.msg_type != MessageType.PAIR_RESPONSE:
                raise ProtocolError(f"Unexpected response to PAIR_REQUEST: {pair_resp.msg_type}")

            self.is_connected = True
            self._last_pong_time = time.time()
            
            # Start background heartbeat thread
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()
            
            return True
        except Exception as ex:
            if self.connection:
                self.connection.close()
                self.connection = None
            self.is_connected = False
            if isinstance(ex, (PairingError, ProtocolError)):
                raise ex
            raise ProtocolError(f"Failed to connect to {self.host}:{self.port} - {ex}")

    def send_key_event(self, event: KeyEvent) -> None:
        """Stream intercepted key event to remote MUX host."""
        if not self.is_connected or not self.connection:
            return

        self._seq += 1
        msg = Message(
            msg_type=MessageType.KEY_EVENT,
            session_id=self.session_id,
            sequence_number=self._seq,
            payload=event.to_dict(),
        )
        try:
            self.connection.send_message(msg)
        except Exception:
            self._trigger_disconnect("Socket write failure on key event streaming.")

    def set_disconnect_callback(self, callback: Callable[[str], None]) -> None:
        """Register callback invoked on connection loss."""
        self._on_disconnect_callback = callback

    def _trigger_disconnect(self, reason: str) -> None:
        if not self.is_connected:
            return
        self.is_connected = False
        if self.connection:
            self.connection.close()
            self.connection = None
        if self._on_disconnect_callback:
            try:
                self._on_disconnect_callback(reason)
            except Exception:
                pass

    def _heartbeat_loop(self) -> None:
        """Periodic PING/PONG heartbeat thread to monitor connection health."""
        while self.is_connected and self.connection:
            time.sleep(HEARTBEAT_INTERVAL)
            if not self.is_connected:
                break

            now = time.time()
            if (now - self._last_pong_time) > HEARTBEAT_TIMEOUT:
                self._trigger_disconnect("Heartbeat timeout (no PONG response from remote host).")
                break

            try:
                self._seq += 1
                start_t = time.time()
                ping_msg = Message(
                    msg_type=MessageType.PING,
                    session_id=self.session_id,
                    sequence_number=self._seq,
                    payload={"time": start_t},
                )
                self.connection.send_message(ping_msg)
                
                pong_msg = self.connection.receive_message()
                if pong_msg and pong_msg.msg_type == MessageType.PONG:
                    self._last_pong_time = time.time()
                    self.last_latency_ms = round((self._last_pong_time - start_t) * 1000.0, 1)
                else:
                    self._trigger_disconnect("Invalid PONG response from remote host.")
                    break
            except Exception:
                self._trigger_disconnect("Heartbeat transmission failure.")
                break

    def disconnect(self) -> None:
        """Gracefully close client connection session."""
        if self.is_connected and self.connection:
            try:
                self._seq += 1
                disc_msg = Message(
                    msg_type=MessageType.DISCONNECT,
                    session_id=self.session_id,
                    sequence_number=self._seq,
                )
                self.connection.send_message(disc_msg)
            except Exception:
                pass
        self._trigger_disconnect("User requested disconnect")

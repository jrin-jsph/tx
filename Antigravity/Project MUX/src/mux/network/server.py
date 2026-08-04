"""TLS TCP network server listening for remote connections and key events."""
import socket
import ssl
import sys
import threading
import time
from typing import Callable, Optional
from mux.core.events import KeyEvent
from mux.input.uinput import LinuxUInputInjector
from mux.input.windows import WindowsInputInjector
from mux.network.connection import Connection
from mux.network.protocol import Message, MessageType, ProtocolError
from mux.platform.detect import is_linux, is_windows
from mux.security.pairing import PairingError, PairingManager

class MUXServer:
    """Listens for remote host connections and executes synthetic keyboard events."""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 7443) -> None:
        self.host = host
        self.port = port
        self.is_running = False
        self.pairing_manager = PairingManager()
        self._server_sock: Optional[socket.socket] = None
        self._threads: list[threading.Thread] = []
        
        # Instantiate platform synthetic key injector
        if is_linux():
            self.injector = LinuxUInputInjector()
        elif is_windows():
            self.injector = WindowsInputInjector()
        else:
            self.injector = None

    def start(self, pairing_code_callback: Optional[Callable[[str], None]] = None) -> None:
        """Start listening socket server in thread."""
        code = self.pairing_manager.generate_code()
        if pairing_code_callback:
            pairing_code_callback(code)

        if self.injector and hasattr(self.injector, "initialize"):
            self.injector.initialize()

        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.bind((self.host, self.port))
        self._server_sock.listen(5)
        self.is_running = True

        server_thread = threading.Thread(target=self._accept_loop, daemon=True)
        server_thread.start()
        self._threads.append(server_thread)

    def _accept_loop(self) -> None:
        while self.is_running and self._server_sock:
            try:
                sock, addr = self._server_sock.accept()
                client_ip = addr[0]
                client_thread = threading.Thread(
                    target=self._handle_client, args=(sock, client_ip), daemon=True
                )
                client_thread.start()
                self._threads.append(client_thread)
            except Exception:
                break

    def _handle_client(self, sock: socket.socket, client_ip: str) -> None:
        conn = Connection(sock)
        session_active = True
        authenticated = False

        while self.is_running and session_active and conn.is_connected:
            try:
                msg = conn.receive_message()
                if not msg:
                    break

                if msg.msg_type == MessageType.HELLO:
                    response = Message(
                        msg_type=MessageType.HELLO,
                        session_id=msg.session_id or "srv-sess",
                        sequence_number=msg.sequence_number + 1,
                        payload={"status": "ready", "server": "MUXServer"},
                    )
                    conn.send_message(response)

                elif msg.msg_type == MessageType.PAIR_REQUEST:
                    submitted_code = str(msg.payload.get("pairing_code", ""))
                    try:
                        self.pairing_manager.verify_code(submitted_code, client_ip=client_ip)
                        authenticated = True
                        response = Message(
                            msg_type=MessageType.PAIR_RESPONSE,
                            session_id=msg.session_id,
                            sequence_number=msg.sequence_number + 1,
                            payload={"status": "success", "message": "Pairing successful"},
                        )
                    except PairingError as pe:
                        response = Message(
                            msg_type=MessageType.ERROR,
                            session_id=msg.session_id,
                            sequence_number=msg.sequence_number + 1,
                            payload={"error": str(pe)},
                        )
                    conn.send_message(response)

                elif msg.msg_type == MessageType.KEY_EVENT:
                    # Execute synthetic key press on host
                    if self.injector and "key_code" in msg.payload:
                        try:
                            event = KeyEvent.from_dict(msg.payload)
                            self.injector.inject_event(event)
                        except Exception:
                            pass

                elif msg.msg_type == MessageType.PING:
                    pong = Message(
                        msg_type=MessageType.PONG,
                        session_id=msg.session_id,
                        sequence_number=msg.sequence_number + 1,
                        payload={"time": time.time()},
                    )
                    conn.send_message(pong)

                elif msg.msg_type == MessageType.DISCONNECT:
                    session_active = False
                    break

            except Exception:
                break

        conn.close()

    def stop(self) -> None:
        """Stop server listening socket."""
        self.is_running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass
            self._server_sock = None
        if self.injector and hasattr(self.injector, "close"):
            self.injector.close()

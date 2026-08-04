"""TCP socket connection wrapper with length-prefixed protocol framing."""
import socket
import struct
from typing import Optional
from mux.network.protocol import MAX_MESSAGE_SIZE, Message, ProtocolError

class Connection:
    """Manages reliable length-prefixed TCP socket communication."""
    
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.is_connected = True

    def send_message(self, msg: Message) -> None:
        """Encode and transmit message over TCP socket stream."""
        if not self.is_connected:
            raise ProtocolError("Cannot send message: Socket is disconnected.")
        
        encoded_data = msg.encode()
        try:
            self.sock.sendall(encoded_data)
        except Exception as ex:
            self.is_connected = False
            raise ProtocolError(f"Socket write failure: {ex}")

    def _read_exact(self, length: int) -> bytes:
        """Read exact byte count from stream."""
        buffer = bytearray()
        while len(buffer) < length:
            chunk = self.sock.recv(length - len(buffer))
            if not chunk:
                self.is_connected = False
                return bytes(buffer)
            buffer.extend(chunk)
        return bytes(buffer)

    def receive_message(self) -> Optional[Message]:
        """Read next length-prefixed Message from socket stream."""
        if not self.is_connected:
            return None

        try:
            header_bytes = self._read_exact(4)
            if len(header_bytes) < 4:
                self.is_connected = False
                return None

            payload_len = struct.unpack(">I", header_bytes)[0]
            if payload_len > MAX_MESSAGE_SIZE:
                self.is_connected = False
                raise ProtocolError(f"Oversized message length header ({payload_len} bytes).")

            payload_bytes = self._read_exact(payload_len)
            if len(payload_bytes) < payload_len:
                self.is_connected = False
                raise ProtocolError("Incomplete payload received on stream.")

            return Message.decode_payload(payload_bytes)
        except Exception as ex:
            self.is_connected = False
            if isinstance(ex, ProtocolError):
                raise ex
            raise ProtocolError(f"Socket read failure: {ex}")

    def close(self) -> None:
        """Close connection socket safely."""
        self.is_connected = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass

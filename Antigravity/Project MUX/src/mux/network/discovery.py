"""UDP local network device discovery broadcaster and listener."""
import json
import socket
import sys
import threading
import time
from typing import Dict, List
from mux.platform.detect import get_system_info

DISCOVERY_PORT = 7444
DISCOVERY_MAGIC = "MUX_DISCOVERY_PING"

class ServiceDiscovery:
    """Discovers MUX instances on the local subnet via UDP broadcasts."""
    
    def __init__(self, port: int = DISCOVERY_PORT) -> None:
        self.port = port
        self._is_listening = False
        self._listener_thread: Optional[threading.Thread] = None
        self._discovered_devices: Dict[str, dict] = {}

    def broadcast_beacon(self, host_name: str, server_port: int = 7443, status: str = "Ready to pair") -> None:
        """Broadcast a single UDP discovery beacon to local subnet."""
        try:
            info = get_system_info()
            beacon_data = {
                "magic": DISCOVERY_MAGIC,
                "host_name": host_name,
                "os": info["os"],
                "port": server_port,
                "status": status,
            }
            payload = json.dumps(beacon_data).encode("utf-8")

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(1.0)
            sock.sendto(payload, ("<broadcast>", self.port))
            sock.close()
        except Exception:
            pass

    def scan(self, timeout_seconds: float = 2.0) -> List[dict]:
        """Scan local subnet for active MUX instances for specified duration."""
        devices: Dict[str, dict] = {}
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(("", self.port))
            sock.settimeout(0.5)

            # Trigger a broadcast ping first
            self.broadcast_beacon(host_name="MUX-Scanner")

            end_time = time.time() + timeout_seconds
            while time.time() < end_time:
                try:
                    data, addr = sock.recvfrom(2048)
                    ip = addr[0]
                    obj = json.loads(data.decode("utf-8", errors="ignore"))
                    if isinstance(obj, dict) and obj.get("magic") == DISCOVERY_MAGIC:
                        if obj.get("host_name") != "MUX-Scanner":
                            devices[ip] = {
                                "ip": ip,
                                "host_name": obj.get("host_name", ip),
                                "os": obj.get("os", "Unknown"),
                                "port": obj.get("port", 7443),
                                "status": obj.get("status", "Ready"),
                            }
                except socket.timeout:
                    continue
                except Exception:
                    break

            sock.close()
        except Exception:
            pass

        return list(devices.values())

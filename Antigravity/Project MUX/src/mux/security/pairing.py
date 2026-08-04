"""Cryptographically secure numeric/alphanumeric pairing code manager."""
import secrets
import time
from typing import Dict, Optional, Tuple
from mux.utils.errors import MUXError

CODE_CHARSET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Unambiguous 32-char set
CODE_LENGTH = 6
CODE_TTL_SECONDS = 300  # 5 minutes expiration
MAX_ATTEMPTS_PER_IP = 5
LOCKOUT_PERIOD_SECONDS = 60

class PairingError(MUXError):
    """Raised on pairing failure or rate limiting."""
    pass

class PairingManager:
    """Manages secure alphanumeric pairing codes, rate limiting, and single-use verification."""
    
    def __init__(self) -> None:
        self._current_code: Optional[str] = None
        self._created_at: float = 0.0
        self._is_used: bool = False
        self._failed_attempts: Dict[str, Tuple[int, float]] = {}  # ip -> (count, timestamp)

    def generate_code(self) -> str:
        """Generate a cryptographically secure 6-character single-use pairing code."""
        code = "".join(secrets.choice(CODE_CHARSET) for _ in range(CODE_LENGTH))
        self._current_code = code
        self._created_at = time.time()
        self._is_used = False
        return code

    def is_expired(self) -> bool:
        """Check if current active pairing code has expired."""
        if not self._current_code:
            return True
        return (time.time() - self._created_at) > CODE_TTL_SECONDS

    def _check_rate_limit(self, client_ip: str) -> None:
        """Enforce rate limiting against brute-force attempts."""
        now = time.time()
        if client_ip in self._failed_attempts:
            count, last_attempt = self._failed_attempts[client_ip]
            if count >= MAX_ATTEMPTS_PER_IP:
                if (now - last_attempt) < LOCKOUT_PERIOD_SECONDS:
                    raise PairingError(f"Too many failed pairing attempts from {client_ip}. Rate limited for 60s.")
                else:
                    # Reset after lockout period
                    self._failed_attempts[client_ip] = (0, now)

    def _record_failure(self, client_ip: str) -> None:
        now = time.time()
        count = self._failed_attempts.get(client_ip, (0, now))[0]
        self._failed_attempts[client_ip] = (count + 1, now)

    def verify_code(self, submitted_code: str, client_ip: str = "127.0.0.1") -> bool:
        """Verify pairing code with single-use and rate-limiting protection.
        
        Raises PairingError on invalid, expired, or rate-limited attempt.
        """
        self._check_rate_limit(client_ip)

        if not self._current_code:
            self._record_failure(client_ip)
            raise PairingError("No pairing session active.")

        if self._is_used:
            self._record_failure(client_ip)
            raise PairingError("Pairing code has already been used.")

        if self.is_expired():
            self._record_failure(client_ip)
            raise PairingError("Pairing code has expired.")

        # Constant-time comparison to prevent timing attacks
        normalized_submitted = submitted_code.strip().upper()
        if not secrets.compare_digest(normalized_submitted, self._current_code):
            self._record_failure(client_ip)
            raise PairingError("Invalid pairing code")

        # Mark single-use
        self._is_used = True
        if client_ip in self._failed_attempts:
            del self._failed_attempts[client_ip]

        return True

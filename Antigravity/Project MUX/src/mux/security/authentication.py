"""Session authentication token verification."""
import secrets
from typing import Dict, Set

class Authenticator:
    """Manages active session tokens and client authentication state."""
    
    def __init__(self) -> None:
        self._authorized_tokens: Set[str] = set()
        self._trusted_fingerprints: Set[str] = set()

    def generate_session_token(self) -> str:
        token = secrets.token_urlsafe(32)
        self._authorized_tokens.add(token)
        return token

    def is_token_valid(self, token: str) -> bool:
        return token in self._authorized_tokens

    def revoke_token(self, token: str) -> None:
        self._authorized_tokens.discard(token)

    def add_trusted_fingerprint(self, fingerprint: str) -> None:
        self._trusted_fingerprints.add(fingerprint)

    def is_fingerprint_trusted(self, fingerprint: str) -> bool:
        return fingerprint in self._trusted_fingerprints

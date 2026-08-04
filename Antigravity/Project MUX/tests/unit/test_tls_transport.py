"""Unit tests for CryptoUtils TLS certificate fingerprinting."""
from mux.security.crypto import CryptoUtils

def test_fingerprint_calculation():
    dummy_cert = b"MIIB...sample_der_bytes..."
    fp = CryptoUtils.get_cert_fingerprint(dummy_cert)
    assert isinstance(fp, str)
    assert len(fp) == 64  # SHA-256 hex digest length

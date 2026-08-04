"""Unit tests for PairingManager security, expiration, rate limiting, and single-use."""
import time
import pytest
from mux.security.pairing import PairingError, PairingManager

def test_pairing_code_generation():
    pm = PairingManager()
    code = pm.generate_code()
    assert len(code) == 6
    assert code.isalnum()
    assert not pm.is_expired()

def test_pairing_code_verification_success():
    pm = PairingManager()
    code = pm.generate_code()
    assert pm.verify_code(code, client_ip="192.168.1.10") is True

def test_pairing_code_single_use_rejection():
    pm = PairingManager()
    code = pm.generate_code()
    assert pm.verify_code(code, client_ip="192.168.1.10") is True
    
    # Second attempt with same code fails
    with pytest.raises(PairingError, match="already been used"):
        pm.verify_code(code, client_ip="192.168.1.10")

def test_pairing_code_expiration_rejection():
    pm = PairingManager()
    code = pm.generate_code()
    pm._created_at = time.time() - 301  # Force expiration (> 300s)
    assert pm.is_expired() is True

    with pytest.raises(PairingError, match="expired"):
        pm.verify_code(code, client_ip="192.168.1.10")

def test_pairing_code_invalid_rejection():
    pm = PairingManager()
    pm.generate_code()
    with pytest.raises(PairingError, match="Invalid pairing code"):
        pm.verify_code("INVALID", client_ip="192.168.1.10")

def test_pairing_rate_limiting():
    pm = PairingManager()
    pm.generate_code()
    ip = "10.0.0.99"

    # 5 failed attempts
    for _ in range(5):
        try:
            pm.verify_code("WRONG", client_ip=ip)
        except PairingError:
            pass

    # 6th attempt triggers rate limiting
    with pytest.raises(PairingError, match="Rate limited"):
        pm.verify_code("WRONG", client_ip=ip)

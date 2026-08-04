"""Unit tests for UDP ServiceDiscovery."""
from mux.network.discovery import ServiceDiscovery

def test_service_discovery_instantiation():
    sd = ServiceDiscovery()
    assert sd.port == 7444
    # Scan with very short timeout
    results = sd.scan(timeout_seconds=0.1)
    assert isinstance(results, list)

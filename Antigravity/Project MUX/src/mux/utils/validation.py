"""Input and parameter validation utilities."""

def validate_port(port: int) -> bool:
    """Validate TCP/UDP port number."""
    return 1 <= port <= 65535

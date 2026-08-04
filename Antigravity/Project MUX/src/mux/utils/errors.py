"""Custom error classes for MUX."""

class MUXError(Exception):
    """Base exception for MUX."""
    pass

class PlatformError(MUXError):
    """Raised when platform operations fail."""
    pass

class ConfigurationError(MUXError):
    """Raised on configuration failures."""
    pass

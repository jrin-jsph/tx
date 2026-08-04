"""ANSI color palette and formatting helpers for MUX CLI."""
import os
import sys

def colors_enabled() -> bool:
    """Check if color output is supported and not disabled."""
    if os.environ.get("NO_COLOR"):
        return False
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False
    return True

def _bullet_char() -> str:
    """Return '●' if supported by stream encoding, else '*'."""
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        "●".encode(encoding)
        return "●"
    except (UnicodeEncodeError, LookupError):
        return "*"

class Theme:
    """Subtle color theme for MUX CLI."""
    
    @staticmethod
    def bold(text: str) -> str:
        return f"\033[1m{text}\033[0m" if colors_enabled() else text

    @staticmethod
    def dim(text: str) -> str:
        return f"\033[2m{text}\033[0m" if colors_enabled() else text

    @staticmethod
    def green(text: str) -> str:
        return f"\033[32m{text}\033[0m" if colors_enabled() else text

    @staticmethod
    def yellow(text: str) -> str:
        return f"\033[33m{text}\033[0m" if colors_enabled() else text

    @staticmethod
    def cyan(text: str) -> str:
        return f"\033[36m{text}\033[0m" if colors_enabled() else text

    @staticmethod
    def red(text: str) -> str:
        return f"\033[31m{text}\033[0m" if colors_enabled() else text

    @staticmethod
    def bullet_green() -> str:
        b = _bullet_char()
        return f"\033[32m{b}\033[0m" if colors_enabled() else b

    @staticmethod
    def bullet_yellow() -> str:
        b = _bullet_char()
        return f"\033[33m{b}\033[0m" if colors_enabled() else b

    @staticmethod
    def bullet_dim() -> str:
        b = _bullet_char()
        return f"\033[90m{b}\033[0m" if colors_enabled() else b

    @staticmethod
    def bullet_red() -> str:
        b = _bullet_char()
        return f"\033[31m{b}\033[0m" if colors_enabled() else b

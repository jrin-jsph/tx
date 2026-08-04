"""Persistent configuration manager for MUX settings."""
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

class ConfigManager:
    """Manages application settings stored in OS-appropriate directories."""
    
    def __init__(self, config_path: Optional[str] = None) -> None:
        if config_path:
            self.config_file = Path(config_path)
        else:
            if sys.platform.startswith("win"):
                appdata = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
                base_dir = Path(appdata) / "mux"
            else:
                base_dir = Path.home() / ".config" / "mux"
            self.config_file = base_dir / "config.json"
            
        self._defaults: Dict[str, Any] = {
            "selected_keyboard_path": None,
            "selected_keyboard_name": None,
            "selected_keyboard_vendor": None,
            "selected_keyboard_product": None,
            "default_port": 7443,
            "host_name": "local-host",
            "trusted_devices": [],
            "emergency_shortcut": "Ctrl+Alt+Escape",
            "terminal_theme": "auto",
            "logging_level": "INFO",
        }
        self._settings: Dict[str, Any] = dict(self._defaults)
        self.load()

    def load(self) -> None:
        """Load settings from JSON config file if present."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._settings.update(data)
            except Exception:
                pass

    def save(self) -> None:
        """Persist current settings to JSON config file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._settings, f, indent=2)
        except Exception:
            pass

    def reset(self) -> None:
        """Reset all configuration settings to factory defaults."""
        self._settings = dict(self._defaults)
        self.save()

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._settings[key] = value
        self.save()

    def set_selected_keyboard(self, path: str, name: str, vendor_id: Optional[int] = None, product_id: Optional[int] = None) -> None:
        """Update selected keyboard configuration."""
        self._settings["selected_keyboard_path"] = path
        self._settings["selected_keyboard_name"] = name
        self._settings["selected_keyboard_vendor"] = vendor_id
        self._settings["selected_keyboard_product"] = product_id
        self.save()

    def add_trusted_device(self, ip_or_fingerprint: str) -> None:
        trusted = self._settings.get("trusted_devices", [])
        if ip_or_fingerprint not in trusted:
            trusted.append(ip_or_fingerprint)
            self._settings["trusted_devices"] = trusted
            self.save()

    @property
    def selected_keyboard_path(self) -> Optional[str]:
        return self._settings.get("selected_keyboard_path")

    @property
    def selected_keyboard_name(self) -> Optional[str]:
        return self._settings.get("selected_keyboard_name")

    @property
    def default_port(self) -> int:
        return int(self._settings.get("default_port", 7443))

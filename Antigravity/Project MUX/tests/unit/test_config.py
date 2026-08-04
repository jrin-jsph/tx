"""Unit tests for ConfigManager."""
import os
import tempfile
from mux.config.manager import ConfigManager

def test_config_manager_defaults_and_reset():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "test_config.json")
        cfg = ConfigManager(config_path=config_path)
        assert cfg.default_port == 7443
        
        cfg.set("default_port", 9000)
        assert cfg.default_port == 9000

        cfg.reset()
        assert cfg.default_port == 7443

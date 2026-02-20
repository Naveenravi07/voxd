from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class ConfigManager:
    """Manages persistent configuration in ~/.config/voxd/config.json"""

    def __init__(self, config_path: Path | None = None):
        if config_path is None:
            config_dir = Path.home() / ".config" / "voxd"
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / "config.json"
        self.config_path = config_path

    def load(self) -> dict[str, Any]:
        """Load config from file, return empty dict if not exists."""
        if not self.config_path.exists():
            return {}
        try:
            with self.config_path.open("r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def save(self, config: dict[str, Any]) -> None:
        """Save config to file."""
        with self.config_path.open("w") as f:
            json.dump(config, f, indent=2)

    def get(self, key: str, default: str = "") -> str:
        """Get a config value."""
        config = self.load()
        return config.get(key, default)

    def set(self, key: str, value: str) -> None:
        """Set a config value."""
        config = self.load()
        config[key] = value
        self.save(config)

    def unset(self, key: str) -> None:
        """Remove a config value."""
        config = self.load()
        if key in config:
            del config[key]
            self.save(config)

    def list_all(self) -> dict[str, Any]:
        """List all config values."""
        return self.load()

    def get_env_with_config(self) -> dict[str, str]:
        """Get environment dict with config values applied."""
        env = dict(os.environ)
        config = self.load()
        
        # Map config keys to env vars
        key_mapping = {
            "api_key": "SARVAM_API_KEY",
            "model": "SARVAM_STT_MODEL",
            "language": "SARVAM_LANGUAGE",
            "output_mode": "VOXD_OUTPUT_MODE",
        }
        
        for config_key, env_key in key_mapping.items():
            if config_key in config:
                env[env_key] = config[config_key]
        
        return env

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .config_manager import ConfigManager


@dataclass(frozen=True)
class AppConfig:
    api_key: str
    model: str
    language_code: str
    socket_path: Path
    runner_dir: Path
    status_path: Path
    capture_command: tuple[str, ...]
    output_mode: str

    @staticmethod
    def from_env(use_config_file: bool = True) -> "AppConfig":
        """Load config from environment, optionally merging with config file."""
        env = dict(os.environ)
        
        # Merge config file values if requested
        if use_config_file:
            config_mgr = ConfigManager()
            env.update(config_mgr.get_env_with_config())
        
        runtime_dir = Path(env.get("XDG_RUNTIME_DIR", "/tmp"))
        base_dir = runtime_dir / "voxd"
        return AppConfig(
            api_key=env.get("SARVAM_API_KEY", ""),
            model=env.get("SARVAM_STT_MODEL", "saaras:v3"),
            language_code=env.get("SARVAM_LANGUAGE", "en-IN"),
            socket_path=Path(env.get("VOXD_SOCKET", str(base_dir / "control.sock"))),
            runner_dir=Path(env.get("VOXD_RUNNER_DIR", str(base_dir))),
            status_path=Path(env.get("VOXD_STATUS_PATH", str(base_dir / "status"))),
            capture_command=tuple(
                env.get(
                    "VOXD_CAPTURE_CMD",
                    "ffmpeg -hide_banner -loglevel error -f pulse -i default -ac 1 -ar 16000 -y {output}",
                ).split()
            ),
            output_mode=env.get("VOXD_OUTPUT_MODE", "auto"),
        )

    def ensure_runtime_dirs(self) -> None:
        self.runner_dir.mkdir(parents=True, exist_ok=True)

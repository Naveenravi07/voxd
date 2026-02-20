from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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
    def from_env() -> "AppConfig":
        runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
        base_dir = runtime_dir / "wisperflow"
        return AppConfig(
            api_key=os.environ.get("SARVAM_API_KEY", ""),
            model=os.environ.get("SARVAM_STT_MODEL", "saaras:v3"),
            language_code=os.environ.get("SARVAM_LANGUAGE", "en-IN"),
            socket_path=Path(os.environ.get("WISPERFLOW_SOCKET", str(base_dir / "control.sock"))),
            runner_dir=Path(os.environ.get("WISPERFLOW_RUNNER_DIR", str(base_dir))),
            status_path=Path(os.environ.get("WISPERFLOW_STATUS_PATH", str(base_dir / "status"))),
            capture_command=tuple(
                os.environ.get(
                    "WISPERFLOW_CAPTURE_CMD",
                    "ffmpeg -hide_banner -loglevel error -f pulse -i default -ac 1 -ar 16000 -y {output}",
                ).split()
            ),
            output_mode=os.environ.get("WISPERFLOW_OUTPUT_MODE", "auto"),
        )

    def ensure_runtime_dirs(self) -> None:
        self.runner_dir.mkdir(parents=True, exist_ok=True)

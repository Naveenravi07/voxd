from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RecordingSession:
    process: subprocess.Popen
    output_path: Path


class AudioRecorder:
    def __init__(self, capture_command: tuple[str, ...]):
        self._capture_command = capture_command
        self._session: RecordingSession | None = None

    @property
    def is_recording(self) -> bool:
        return self._session is not None

    def start(self, output_path: Path) -> None:
        if self._session:
            raise RuntimeError("Recording already in progress")

        command = [arg.format(output=str(output_path)) for arg in self._capture_command]
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        self._session = RecordingSession(process=process, output_path=output_path)

    def stop(self) -> Path:
        if not self._session:
            raise RuntimeError("No recording in progress")

        session = self._session
        self._session = None
        session.process.terminate()
        try:
            session.process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            session.process.kill()
            session.process.wait(timeout=2)
        return session.output_path

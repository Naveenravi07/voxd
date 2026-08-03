from __future__ import annotations

import datetime as dt
import logging
import socket
import subprocess
from pathlib import Path

from .config import AppConfig
from .injector import TextInjector
from .recorder import AudioRecorder
from .sarvam_client import SarvamSTTClient


LOGGER = logging.getLogger("voxd")


def configure_logging(config: AppConfig) -> None:
    config.ensure_runtime_dirs()
    logging.basicConfig(
        filename=config.log_path,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        force=True,
    )


class DictationService:
    def __init__(self, config: AppConfig):
        self._config = config
        self._config.ensure_runtime_dirs()
        self._recorder = AudioRecorder(config.capture_command)
        self._injector = TextInjector(config.output_mode)
        self._stt = SarvamSTTClient(
            api_key=config.api_key,
            model=config.model,
            language_code=config.language_code,
        )
        self._set_state("idle", notify=False)

    def handle_command(self, command: str) -> str:
        command = command.strip().lower()
        try:
            if command == "toggle":
                return self._toggle()
            if command == "status":
                return "recording" if self._recorder.is_recording else "idle"
            if command == "quit":
                if self._recorder.is_recording:
                    self._recorder.stop()
                    self._set_state("idle")
                return "bye"
            return f"error: unknown command {command}"
        except Exception as exc:
            LOGGER.exception("Command failed: %s", command or "<empty>")
            self._recover_after_error()
            return f"error: {type(exc).__name__}: {exc}"

    def _toggle(self) -> str:
        if not self._recorder.is_recording:
            path = self._build_capture_path()
            self._recorder.start(path)
            self._set_state("recording")
            return "recording-started"

        audio_path = self._recorder.stop()
        text = self._stt.transcribe(audio_path)
        output_status = self._injector.send_text(text)
        self._set_state("idle", output_status)
        return f"recording-stopped text-length={len(text)}"

    def _set_state(self, state: str, output_status: str = "", notify: bool = True) -> None:
        self._config.status_path.write_text(f"{state}\n", encoding="utf-8")
        
        if not notify:
            return
        
        if state == "recording":
            subprocess.run(
                ["notify-send", "-u", "low", "-t", "1500", "-a", "voxd", "Recording..."],
                check=False,
            )
        else:
            if output_status == "clipboard":
                message = "Copied to clipboard"
            elif output_status.startswith("typed"):
                message = "Text typed"
            else:
                message = "Stopped"
            subprocess.run(
                ["notify-send", "-u", "low", "-t", "1500", "-a", "voxd", message],
                check=False,
            )

    def _build_capture_path(self) -> Path:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        return self._config.runner_dir / f"capture-{stamp}.wav"

    def _recover_after_error(self) -> None:
        if self._recorder.is_recording:
            try:
                self._recorder.stop()
            except Exception:
                LOGGER.exception("Failed to stop recorder during error recovery")

        try:
            self._set_state("idle")
        except Exception:
            LOGGER.exception("Failed to set idle state during error recovery")


def run_server(config: AppConfig) -> None:
    configure_logging(config)
    config.ensure_runtime_dirs()
    if config.socket_path.exists():
        config.socket_path.unlink()

    LOGGER.info("Starting voxd daemon")
    try:
        service = DictationService(config)
    except Exception:
        LOGGER.exception("Failed to initialize voxd daemon")
        raise

    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
            server.bind(str(config.socket_path))
            config.socket_path.chmod(0o600)
            server.listen(4)
            LOGGER.info("Listening on %s", config.socket_path)

            while True:
                conn, _ = server.accept()
                with conn:
                    data = conn.recv(1024)
                    command = data.decode("utf-8", errors="ignore").strip() if data else ""
                    result = service.handle_command(command)
                    conn.sendall(result.encode("utf-8"))
                    if command.lower() == "quit":
                        LOGGER.info("Stopping voxd daemon")
                        break
    except Exception:
        LOGGER.exception("Daemon crashed")
        raise
    finally:
        if config.socket_path.exists():
            config.socket_path.unlink()
        LOGGER.info("voxd daemon stopped")


def send_command(socket_path: Path, command: str) -> str:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.connect(str(socket_path))
        client.sendall(command.encode("utf-8"))
        response = client.recv(4096)
    return response.decode("utf-8", errors="ignore").strip()

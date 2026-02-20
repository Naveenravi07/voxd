from __future__ import annotations

import os
import shlex
import subprocess


class TextInjector:
    def __init__(self, output_mode: str = "auto"):
        self._output_mode = output_mode

    def send_text(self, text: str) -> str:
        """Send text to output. Returns status message."""
        text = text.strip()
        if not text:
            return "empty"

        # Try clipboard first (works everywhere)
        if self._copy_to_clipboard(text):
            return "clipboard"

        # Fallback to typing
        mode = self._resolve_mode()
        if mode == "x11":
            if self._run_command(["xdotool", "type", "--clearmodifiers", text]):
                return "typed-x11"
        elif mode == "wayland":
            if self._run_command(["wtype", text]):
                return "typed-wayland"
        elif mode == "stdout":
            print(text)
            return "stdout"

        return "clipboard"  # Already copied above

    def _copy_to_clipboard(self, text: str) -> bool:
        """Copy to clipboard. Returns True if successful."""
        # Try wl-copy (Wayland)
        if os.environ.get("WAYLAND_DISPLAY"):
            if self._run_command(["wl-copy"], input_text=text):
                return True

        # Try xclip (X11)
        if os.environ.get("DISPLAY"):
            if self._run_command(["xclip", "-selection", "clipboard"], input_text=text):
                return True

        # Try xsel (X11 fallback)
        if os.environ.get("DISPLAY"):
            if self._run_command(["xsel", "--clipboard", "--input"], input_text=text):
                return True

        return False

    def _resolve_mode(self) -> str:
        if self._output_mode in {"x11", "wayland", "stdout"}:
            return self._output_mode

        if os.environ.get("WAYLAND_DISPLAY"):
            return "wayland"
        if os.environ.get("DISPLAY"):
            return "x11"
        return "stdout"

    def _run_command(self, command: list[str], input_text: str | None = None) -> bool:
        """Run command. Returns True if successful."""
        try:
            if input_text:
                subprocess.run(
                    command,
                    input=input_text.encode("utf-8"),
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                subprocess.run(
                    command,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return True
        except (FileNotFoundError, subprocess.CalledProcessError):
            return False

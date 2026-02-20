from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

from wisperflow.core.config import AppConfig
from wisperflow.core.service import run_server, send_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wisperflow-core")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("serve", help="Run the local dictation daemon")

    toggle = sub.add_parser("toggle", help="Toggle recording state")
    toggle.add_argument("--autostart", action="store_true", help="Start daemon if missing")

    sub.add_parser("status", help="Show daemon status")
    sub.add_parser("quit", help="Stop the daemon")
    return parser


def _start_daemon(config: AppConfig) -> None:
    config.ensure_runtime_dirs()
    with (config.runner_dir / "daemon.log").open("a") as log_file:
        subprocess.Popen(
            [sys.executable, "-m", "wisperflow.cli", "serve"],
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )


def _send_or_fail(socket_path: Path, command: str) -> str:
    if not socket_path.exists():
        raise RuntimeError("daemon-not-running")
    return send_command(socket_path, command)


def daemon(argv: list[str] | None = None) -> int:
    """Entry point for wisperflow-daemon command."""
    config = AppConfig.from_env()
    run_server(config)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    config = AppConfig.from_env()

    if args.cmd == "serve":
        run_server(config)
        return 0

    if args.cmd == "toggle" and args.autostart and not config.socket_path.exists():
        _start_daemon(config)
        for _ in range(25):
            if config.socket_path.exists():
                break
            time.sleep(0.1)

    try:
        reply = _send_or_fail(config.socket_path, args.cmd)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except FileNotFoundError:
        print("daemon-not-running", file=sys.stderr)
        return 1

    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

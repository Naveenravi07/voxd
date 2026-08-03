from __future__ import annotations

import argparse
import subprocess
import sys
import time
import warnings
from pathlib import Path

# Suppress Pydantic v1 warnings from sarvamai package
warnings.filterwarnings("ignore", message=".*Pydantic V1.*", category=UserWarning)

from voxd.core.config import AppConfig
from voxd.core.config_manager import ConfigManager
from voxd.core.service import run_server, send_command


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="voxd",
        description="Voice dictation daemon for Linux",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  voxd toggle              Toggle recording
  voxd toggle --autostart  Start daemon if needed, then toggle
  voxd status              Check daemon status
  voxd logs                Show daemon logs
  voxd config set api_key sk_xxx    Set API key
  voxd config set language hi-IN    Set language
  voxd config list                  Show all config
        """,
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    # Daemon commands
    sub.add_parser("serve", help="Run the dictation daemon (internal use)")
    
    toggle = sub.add_parser("toggle", help="Toggle recording on/off")
    toggle.add_argument("--autostart", action="store_true", help="Start daemon if not running")
    
    sub.add_parser("status", help="Show daemon status (idle/recording)")
    sub.add_parser("quit", help="Stop the daemon")
    logs = sub.add_parser("logs", help="Show daemon log path or recent daemon logs")
    logs.add_argument("-f", "--follow", action="store_true", help="Follow daemon logs")
    logs.add_argument("-n", "--lines", type=int, default=80, help="Number of log lines to show")
    logs.add_argument("--path", action="store_true", help="Only print the log file path")

    # Config commands
    config_parser = sub.add_parser("config", help="Manage configuration")
    config_sub = config_parser.add_subparsers(dest="config_cmd", required=True)
    
    config_set = config_sub.add_parser("set", help="Set a config value")
    config_set.add_argument("key", choices=["api_key", "model", "language", "output_mode"],
                           help="Config key to set")
    config_set.add_argument("value", help="Value to set")
    
    config_get = config_sub.add_parser("get", help="Get a config value")
    config_get.add_argument("key", help="Config key to get")
    
    config_unset = config_sub.add_parser("unset", help="Remove a config value")
    config_unset.add_argument("key", help="Config key to remove")
    
    config_sub.add_parser("list", help="List all config values")
    config_sub.add_parser("path", help="Show config file path")

    return parser


def _start_daemon(config: AppConfig) -> None:
    config.ensure_runtime_dirs()
    with config.log_path.open("a") as log_file:
        subprocess.Popen(
            [sys.executable, "-m", "voxd.cli", "serve"],
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )


def _send_or_fail(socket_path: Path, command: str) -> str:
    if not socket_path.exists():
        raise RuntimeError("daemon-not-running")
    try:
        return send_command(socket_path, command)
    except (ConnectionRefusedError, FileNotFoundError, OSError) as exc:
        raise RuntimeError("daemon-not-running") from exc


def _daemon_not_running_message(config: AppConfig) -> str:
    return (
        "daemon-not-running\n"
        f"socket: {config.socket_path}\n"
        f"logs: {config.log_path}\n"
        "start it with: voxd toggle --autostart"
    )


def _handle_logs_command(config: AppConfig, args: argparse.Namespace) -> int:
    config.ensure_runtime_dirs()

    if args.path:
        print(config.log_path)
        return 0

    if not config.log_path.exists():
        print(f"No log file yet: {config.log_path}", file=sys.stderr)
        print("Start the daemon with: voxd toggle --autostart", file=sys.stderr)
        return 1

    tail_args = ["tail", "-n", str(args.lines)]
    if args.follow:
        tail_args.append("-f")
    tail_args.append(str(config.log_path))
    return subprocess.call(tail_args)


def _handle_config_command(args: argparse.Namespace) -> int:
    """Handle config subcommands."""
    config_mgr = ConfigManager()
    
    if args.config_cmd == "set":
        config_mgr.set(args.key, args.value)
        print(f"Set {args.key} = {args.value}")
        print("Restart daemon for changes to take effect: voxd quit && voxd-daemon &")
        return 0
    
    if args.config_cmd == "get":
        value = config_mgr.get(args.key)
        if value:
            print(value)
        else:
            print(f"{args.key} not set", file=sys.stderr)
            return 1
        return 0
    
    if args.config_cmd == "unset":
        config_mgr.unset(args.key)
        print(f"Unset {args.key}")
        return 0
    
    if args.config_cmd == "list":
        config = config_mgr.list_all()
        if not config:
            print("No config values set")
        else:
            for key, value in config.items():
                # Mask API key
                if key == "api_key" and value:
                    masked = value[:8] + "..." if len(value) > 8 else "***"
                    print(f"{key} = {masked}")
                else:
                    print(f"{key} = {value}")
        return 0
    
    if args.config_cmd == "path":
        print(config_mgr.config_path)
        return 0
    
    return 1


def daemon(argv: list[str] | None = None) -> int:
    """Entry point for voxd-daemon command."""
    config = AppConfig.from_env()
    return _run_server_command(config)


def _run_server_command(config: AppConfig) -> int:
    try:
        run_server(config)
        return 0
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        print(f"daemon-failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        print(f"logs: {config.log_path}", file=sys.stderr)
        return 1


def _wait_for_daemon(config: AppConfig, attempts: int = 30) -> bool:
    for _ in range(attempts):
        try:
            if config.socket_path.exists():
                send_command(config.socket_path, "status")
                return True
        except (ConnectionRefusedError, FileNotFoundError, RuntimeError, OSError):
            pass
        time.sleep(0.1)
    return False


def _autostart_daemon(config: AppConfig) -> None:
    if config.socket_path.exists():
        try:
            send_command(config.socket_path, "status")
            return
        except (ConnectionRefusedError, FileNotFoundError, RuntimeError, OSError):
            try:
                config.socket_path.unlink()
            except FileNotFoundError:
                pass

    _start_daemon(config)
    _wait_for_daemon(config)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    
    # Handle config commands
    if args.cmd == "config":
        return _handle_config_command(args)
    
    config = AppConfig.from_env()

    if args.cmd == "serve":
        return _run_server_command(config)

    if args.cmd == "logs":
        return _handle_logs_command(config, args)

    if args.cmd == "toggle" and args.autostart:
        _autostart_daemon(config)

    try:
        reply = _send_or_fail(config.socket_path, args.cmd)
    except RuntimeError as exc:
        if str(exc) == "daemon-not-running":
            print(_daemon_not_running_message(config), file=sys.stderr)
        else:
            print(str(exc), file=sys.stderr)
        return 1

    if reply.startswith("error:"):
        print(reply, file=sys.stderr)
        print(f"logs: {config.log_path}", file=sys.stderr)
        return 1

    print(reply)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

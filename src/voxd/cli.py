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
  voxd status              Check daemon status
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
    with (config.runner_dir / "daemon.log").open("a") as log_file:
        subprocess.Popen(
            [sys.executable, "-m", "voxd.cli", "serve"],
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,
        )


def _send_or_fail(socket_path: Path, command: str) -> str:
    if not socket_path.exists():
        raise RuntimeError("daemon-not-running")
    return send_command(socket_path, command)


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
    run_server(config)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    
    # Handle config commands
    if args.cmd == "config":
        return _handle_config_command(args)
    
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

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wisperflow-hypr")
    parser.add_argument("command", choices=["toggle", "status", "quit"], nargs="?", default="toggle")
    args = parser.parse_args(argv)

    env = dict(os.environ)
    env.setdefault("WISPERFLOW_OUTPUT_MODE", "wayland")

    cmd = [sys.executable, "-m", "wisperflow.cli", args.command]
    if args.command == "toggle":
        cmd.append("--autostart")

    result = subprocess.run(cmd, env=env)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

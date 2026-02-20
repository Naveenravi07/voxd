from __future__ import annotations

import argparse
import os
import subprocess
import sys
import warnings

# Suppress Pydantic v1 warnings from sarvamai package
warnings.filterwarnings("ignore", message=".*Pydantic V1.*", category=UserWarning)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="voxd-hypr")
    parser.add_argument("command", choices=["toggle", "status", "quit"], nargs="?", default="toggle")
    args = parser.parse_args(argv)

    env = dict(os.environ)
    env.setdefault("VOXD_OUTPUT_MODE", "wayland")

    cmd = [sys.executable, "-m", "voxd.cli", args.command]
    if args.command == "toggle":
        cmd.append("--autostart")

    result = subprocess.run(cmd, env=env)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())

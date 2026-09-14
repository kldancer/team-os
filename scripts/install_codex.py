#!/usr/bin/env python3
"""Backward-compatible Codex installer for the Team OS runtime projection."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from install_runtime import InstallError, default_home, install


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=default_home("codex"))
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        for action in install("codex", args.codex_home, check=args.check):
            print(action)
    except InstallError as error:
        print(f"team-os-install: {error}", file=os.sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

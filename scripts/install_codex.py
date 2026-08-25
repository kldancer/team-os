#!/usr/bin/env python3
"""Safely project the minimal Team OS contract into a Codex home."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "codex"
MANIFEST_NAME = "team-os-install.json"
FILES = {
    "AGENTS.md": SOURCE_ROOT / "AGENTS.md",
    "skills/team-os-plan/SKILL.md": SOURCE_ROOT / "skills/team-os-plan/SKILL.md",
    "skills/team-os-plan/references/capabilities.yaml": ROOT / "roles/capabilities.yaml",
    "skills/team-os-plan/references/module-implementation-plan.md": ROOT
    / "templates"
    / "module-implementation-plan.md",
    "skills/team-os-retrospective/SKILL.md": SOURCE_ROOT / "skills/team-os-retrospective/SKILL.md",
}


class InstallError(ValueError):
    pass


def digest_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def digest_file(path: Path) -> str:
    return digest_bytes(path.read_bytes())


def read_manifest(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        files = payload["files"]
    except (OSError, json.JSONDecodeError, KeyError, TypeError) as error:
        raise InstallError(f"invalid install manifest: {path}: {error}") from error
    if payload.get("version") != 1 or not isinstance(files, dict):
        raise InstallError(f"unsupported install manifest: {path}")
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in files.items()):
        raise InstallError(f"invalid managed file map: {path}")
    return files


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def desired_files() -> dict[str, bytes]:
    missing = [str(path) for path in FILES.values() if not path.is_file()]
    if missing:
        raise InstallError(f"missing projection source: {', '.join(missing)}")
    return {relative: source.read_bytes() for relative, source in FILES.items()}


def verify_target(codex_home: Path, desired: dict[str, bytes], managed: dict[str, str]) -> list[str]:
    errors: list[str] = []
    for relative, content in desired.items():
        target = codex_home / relative
        wanted = digest_bytes(content)
        if not target.is_file():
            errors.append(f"missing: {relative}")
        elif digest_file(target) != wanted:
            errors.append(f"drifted: {relative}")
        elif managed.get(relative) != wanted:
            errors.append(f"unmanaged: {relative}")
    return errors


def install(codex_home: Path, *, check: bool) -> list[str]:
    codex_home = codex_home.expanduser().resolve(strict=False)
    manifest_path = codex_home / MANIFEST_NAME
    desired = desired_files()
    managed = read_manifest(manifest_path)
    if check:
        errors = verify_target(codex_home, desired, managed)
        if errors:
            raise InstallError("; ".join(errors))
        return [f"verified {relative}" for relative in sorted(desired)]

    actions: list[str] = []
    next_managed: dict[str, str] = {}
    for relative, content in desired.items():
        target = codex_home / relative
        wanted = digest_bytes(content)
        previous = managed.get(relative)
        if target.exists():
            if not target.is_file() or target.is_symlink():
                raise InstallError(f"target must be a regular file: {target}")
            current = digest_file(target)
            adoptable_empty_agents = relative == "AGENTS.md" and target.stat().st_size == 0
            if previous is None and current != wanted and not adoptable_empty_agents:
                raise InstallError(f"refusing to overwrite unmanaged file: {target}")
            if previous is not None and current not in {previous, wanted}:
                raise InstallError(f"refusing to overwrite locally modified managed file: {target}")
            if current == wanted:
                actions.append(f"unchanged {relative}")
                next_managed[relative] = wanted
                continue
        atomic_write(target, content)
        actions.append(f"installed {relative}")
        next_managed[relative] = wanted

    stale = sorted(set(managed) - set(desired))
    if stale:
        actions.extend(f"left stale managed file in place: {relative}" for relative in stale)
        next_managed.update({relative: managed[relative] for relative in stale})
    manifest = json.dumps(
        {"version": 1, "source": str(ROOT), "files": next_managed},
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ).encode("utf-8") + b"\n"
    atomic_write(manifest_path, manifest)
    return actions


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--codex-home", type=Path, default=Path(os.environ.get("CODEX_HOME", "~/.codex")))
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        for action in install(args.codex_home, check=args.check):
            print(action)
    except InstallError as error:
        print(f"team-os-install: {error}", file=os.sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

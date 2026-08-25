#!/usr/bin/env python3
"""Unit tests for the bounded Team OS Codex projection."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().with_name("install_codex.py")


class InstallCodexTest(unittest.TestCase):
    def run_installer(self, home: Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--codex-home", str(home), *extra],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_install_is_bounded_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            (home / "AGENTS.md").write_text("", encoding="utf-8")
            unrelated = home / "skills" / "personal" / "SKILL.md"
            unrelated.parent.mkdir(parents=True)
            unrelated.write_text("personal\n", encoding="utf-8")

            first = self.run_installer(home)
            self.assertEqual(first.returncode, 0, first.stderr)
            second = self.run_installer(home)
            self.assertEqual(second.returncode, 0, second.stderr)
            checked = self.run_installer(home, "--check")
            self.assertEqual(checked.returncode, 0, checked.stderr)
            self.assertEqual(unrelated.read_text(encoding="utf-8"), "personal\n")
            role_catalog = home / "skills" / "team-os-plan" / "references" / "capabilities.yaml"
            self.assertIn("delivery-engineer", role_catalog.read_text(encoding="utf-8"))
            module_template = (
                home
                / "skills"
                / "team-os-plan"
                / "references"
                / "module-implementation-plan.md"
            )
            self.assertIn("## 场景与业务链覆盖", module_template.read_text(encoding="utf-8"))

    def test_local_drift_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            first = self.run_installer(home)
            self.assertEqual(first.returncode, 0, first.stderr)
            target = home / "skills" / "team-os-plan" / "SKILL.md"
            target.write_text("local edit\n", encoding="utf-8")

            second = self.run_installer(home)
            self.assertEqual(second.returncode, 2)
            self.assertEqual(target.read_text(encoding="utf-8"), "local edit\n")

    def test_unmanaged_agents_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            target = home / "AGENTS.md"
            target.write_text("user rules\n", encoding="utf-8")

            result = self.run_installer(home)
            self.assertEqual(result.returncode, 2)
            self.assertEqual(target.read_text(encoding="utf-8"), "user rules\n")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).parents[0] / "../skills/team-os-codex/scripts/project_bridge.py"

class ProjectBridgeTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        task = self.root / ".work/tasks/t1"
        task.mkdir(parents=True)
        (task / "plan.json").write_text(json.dumps({
            "controller": "juspctl", "taskId": "t1", "resultOwner": "owner",
            "outcomeContract": {"outcome": "result", "acceptance": ["pass"]},
            "requiresFreeze": False, "remoteRequired": False,
        }), encoding="utf-8")
    def tearDown(self): self.temp.cleanup()
    def invoke(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], text=True, capture_output=True)
    def test_bind_and_inspect_are_idempotent_and_read_only(self):
        first = self.invoke("bind", "--project-root", str(self.root), "--checkout-root", str(self.root), "--task", "t1", "--owner", "owner", "--model", "gpt-6-astra", "--effort", "high")
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.invoke("bind", "--project-root", str(self.root), "--checkout-root", str(self.root), "--task", "t1", "--owner", "owner", "--model", "gpt-6-astra", "--effort", "high")
        self.assertEqual(second.returncode, 0, second.stderr)
        inspected = self.invoke("inspect", "--project-root", str(self.root), "--checkout-root", str(self.root), "--task", "t1", "--require-binding")
        self.assertEqual(inspected.returncode, 0, inspected.stderr)
        self.assertIn('"binding": "current"', inspected.stdout)
        self.assertFalse((self.root / "started").exists())
    def test_astra_rejects_none_reasoning(self):
        result = self.invoke("bind", "--project-root", str(self.root), "--checkout-root", str(self.root), "--task", "t1", "--owner", "owner", "--model", "gpt-6-astra", "--effort", "none")
        self.assertEqual(result.returncode, 2)

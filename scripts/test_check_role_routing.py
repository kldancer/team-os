#!/usr/bin/env python3
"""Unit tests for the role-routing measurement script."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("check_role_routing.py")
SPEC = importlib.util.spec_from_file_location("check_role_routing", SCRIPT)
assert SPEC and SPEC.loader
check_role_routing = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_role_routing
SPEC.loader.exec_module(check_role_routing)

CATALOG = Path(__file__).resolve().parents[1] / "models" / "catalog.yaml"


def write_session(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in entries), encoding="utf-8")


def stamp(minutes_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat().replace("+00:00", "Z")


def message(tools: list[tuple[str, dict]], usage: dict | None = None) -> dict:
    return {
        "type": "message",
        "timestamp": stamp(1),
        "message": {
            "role": "assistant",
            "usage": usage or {},
            "content": [{"type": "toolCall", "id": "c1", "name": name, "arguments": args} for name, args in tools],
        },
    }


class RoleRoutingTest(unittest.TestCase):
    def test_tier_map_reads_agents_and_generic_overrides(self) -> None:
        agents, generics = check_role_routing.tier_map(check_role_routing.read_yaml(CATALOG))
        self.assertEqual(agents["team-os-planner"], "analysis")
        self.assertEqual(agents["team-os-planner-alt"], "adjudication")
        self.assertEqual(agents["team-os-ui-designer"], "vision")
        self.assertEqual(agents["team-os-bounded-worker"], "execution")
        self.assertEqual(generics["task"], "execution")

    def test_dispatch_tiers_execution_share_and_promotions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            seconds = stamp(1)
            write_session(
                root / "-repo" / "2026-01-01T00-00-00-000Z_abc.jsonl",
                [
                    {"type": "model_change", "timestamp": seconds, "model": "kimi-code/k3-256k", "role": "default"},
                    {"type": "model_change", "timestamp": seconds, "model": "kimi-code/k3", "role": "default"},
                    message([("read", {"path": "src/app/Shell.tsx"}), ("bash", {"command": "ls"})]),
                    message([("task", {"tasks": [{"agent": "team-os-planner-alt", "task": "draft"}]})]),
                    message([("task", {"tasks": [{"agent": "scout", "task": "facts"}, {"task": "no agent"}]})]),
                ],
            )
            report = check_role_routing.build_report(root, None, 1, CATALOG)
        self.assertEqual(report["sessionCount"], 1)
        self.assertEqual(report["dispatchTierTotals"]["adjudication"], 1)
        self.assertEqual(report["dispatchTierTotals"]["execution"], 2)
        self.assertEqual(report["planningSplit"]["adjudicationDispatches"], 1)
        self.assertEqual(report["planningSplit"]["shareToAdjudication"], 1.0)
        self.assertTrue(report["targets"]["planningHalfToAdjudication"])
        self.assertEqual(report["mainSession"]["promotionsTo1M"], 1)
        self.assertEqual(report["mainSession"]["uiCallsOnMainTier"], 1)
        self.assertEqual(report["mainSession"]["executionCalls"], 2)
        self.assertEqual(report["mainSession"]["toolCalls"], 4)
        self.assertAlmostEqual(report["mainSession"]["executionShare"], 0.5, places=3)
        self.assertFalse(report["targets"]["mainExecutionShareBelow30Percent"])

    def test_main_context_median_feeds_the_thinning_target(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_session(
                root / "-repo" / "2026-01-01T00-00-00-000Z_c.jsonl",
                [
                    message([("read", {})], usage={"input": 100, "cacheRead": 900}),
                    message([("read", {})], usage={"input": 50_000, "cacheRead": 300_000}),
                ],
            )
            report = check_role_routing.build_report(root, None, 1, CATALOG)
        self.assertEqual(report["mainSession"]["contextSamples"], 2)
        self.assertEqual(report["mainSession"]["contextMedian"], 350_000)
        self.assertFalse(report["targets"]["mainContextMedianBelow200k"])

    def test_folder_filter_and_window_exclude_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_session(root / "-other" / "2026-01-01T00-00-00-000Z_b.jsonl", [message([("read", {})])])
            stale = {
                "type": "message",
                "timestamp": (datetime.now(timezone.utc) - timedelta(days=9)).isoformat().replace("+00:00", "Z"),
                "message": {"role": "assistant", "content": [{"type": "toolCall", "name": "read", "arguments": {}}]},
            }
            write_session(root / "-repo" / "2026-01-01T00-00-00-000Z_a.jsonl", [stale])
            filtered = check_role_routing.build_report(root, "repo", 1, CATALOG)
        self.assertEqual(filtered["sessionCount"], 1)
        self.assertEqual(filtered["mainSession"]["toolCalls"], 0)

    def test_missing_sessions_root_reports_zero_sessions(self) -> None:
        report = check_role_routing.build_report(Path("/nonexistent/sessions"), None, 1, CATALOG)
        self.assertEqual(report["sessionCount"], 0)
        self.assertIsNone(report["mainSession"]["executionShare"])


if __name__ == "__main__":
    unittest.main()

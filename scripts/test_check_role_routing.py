#!/usr/bin/env python3
"""Unit tests for the role-routing measurement and dispatch scripts."""

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

ROUTE = Path(__file__).resolve().with_name("route_work.py")
RSPEC = importlib.util.spec_from_file_location("route_work", ROUTE)
assert RSPEC and RSPEC.loader
route_work = importlib.util.module_from_spec(RSPEC)
sys.modules[RSPEC.name] = route_work
RSPEC.loader.exec_module(route_work)

CATALOG = Path(__file__).resolve().parents[1] / "models" / "catalog.yaml"


def write_session(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(item, ensure_ascii=False) + "\n" for item in entries), encoding="utf-8")


def stamp(minutes_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)).isoformat().replace("+00:00", "Z")


def message(tools: list[tuple[str, dict]], usage: dict | None = None, model: str | None = None) -> dict:
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
        # subscription-tier owner self-execution split
        self.assertEqual(report["tierSplit"]["ownerExecutionCalls"], 2)
        self.assertEqual(report["tierSplit"]["ownerCalls"], 2)
        self.assertAlmostEqual(report["tierSplit"]["ownerExecutionShare"], 1.0, places=3)

    def test_lane_sessions_count_as_execution_not_owner(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            # real layout: top-level file sits directly under the folder dir,
            # lane children live inside the top-level session directory
            write_session(
                root / "-repo" / "2026-01-01T00-00-00-000Z_top.jsonl",
                [
                    {"type": "model_change", "timestamp": stamp(1), "model": "zhipu-coding-plan/glm-5.3", "role": "default"},
                    message([("bash", {"command": "git status --short"})]),
                    message([("read", {"path": "src/a.ts"})]),
                ],
            )
            lane = [
                {
                    "type": "session",
                    "version": 3,
                    "id": "lane-1",
                    "parentSession": str(root / "-repo" / "2026-01-01T00-00-00-000Z_top.jsonl"),
                    "timestamp": stamp(1),
                },
                {"type": "model_change", "timestamp": stamp(1), "model": "teamorouter/deepseek-flash", "role": "default"},
                message([("edit", {"path": "src/b.ts"}), ("bash", {"command": "bun run typecheck"})]),
            ]
            write_session(root / "-repo" / "2026-01-01T00-00-00-000Z_top" / "AdminLane.jsonl", lane)
            report = check_role_routing.build_report(root, None, 1, CATALOG)
        self.assertEqual(report["sessionCount"], 2)
        self.assertEqual(report["tierSplit"]["ownerCalls"], 2)
        self.assertEqual(report["tierSplit"]["ownerExecutionCalls"], 2)
        self.assertEqual(report["tierSplit"]["laneCalls"], 2)
        self.assertEqual(report["tierSplit"]["laneExecutionCalls"], 2)
        # 50% of execution has been delegated to lanes
        self.assertAlmostEqual(report["tierSplit"]["executionDelegatedShare"], 0.5, places=3)

    def test_prod_command_on_subscription_tier_is_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_session(
                root / "-repo" / "2026-01-01T00-00-00-000Z_p.jsonl",
                [
                    {"type": "model_change", "timestamp": stamp(1), "model": "kimi-code/k3", "role": "default"},
                    message([("bash", {"command": "ssh -p 10263 root@119.6.186.139 'docker run --rm hello'"})]),
                    message([("bash", {"command": "ls"})]),
                ],
            )
            report = check_role_routing.build_report(root, None, 1, CATALOG)
        self.assertEqual(len(report["prodCallsOnSubscriptionTier"]), 1)
        result = check_role_routing.gate_report(report)
        self.assertFalse(result["pass"])
        self.assertEqual(result["blocking"][0]["code"], "prod-command-on-subscription-tier")

    def test_gate_flags_ui_without_vision_tier(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            tools = [("read", {"path": f"src/admin-console/page{i}.tsx"}) for i in range(12)]
            write_session(
                root / "-repo" / "2026-01-01T00-00-00-000Z_u.jsonl",
                [
                    {"type": "model_change", "timestamp": stamp(1), "model": "kimi-code/k3", "role": "default"},
                    message(tools),
                ],
            )
            report = check_role_routing.build_report(root, None, 1, CATALOG)
        self.assertGreaterEqual(report["mainSession"]["uiCallsOnMainTier"], 12)
        result = check_role_routing.gate_report(report)
        self.assertFalse(result["pass"])
        codes = [v["code"] for v in result["blocking"]]
        self.assertIn("ui-work-without-vision-tier", codes)

    def test_gate_pass_when_clean(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            top = root / "-repo" / "2026-01-01T00-00-00-000Z_c"
            write_session(
                top / "2026-01-01T00-00-00-000Z_c.jsonl",
                [
                    {"type": "model_change", "timestamp": stamp(1), "model": "zhipu-coding-plan/glm-5.3", "role": "default"},
                    message([("task", {"tasks": [{"agent": "team-os-bounded-worker", "task": "impl"}]})]),
                    message([("hub", {"op": "send"})]),
                ],
            )
            write_session(
                top / "ImplLane.jsonl",
                [
                    {"type": "model_change", "timestamp": stamp(1), "model": "teamorouter/deepseek-flash", "role": "default"},
                    message([("edit", {"path": "src/a.ts"}), ("bash", {"command": "bun run typecheck"})]),
                ],
            )
            report = check_role_routing.build_report(root, None, 1, CATALOG)
        result = check_role_routing.gate_report(report)
        self.assertTrue(result["pass"])
        self.assertEqual(result["blocking"], [])

    def test_task_filter_attributes_to_the_first_mentioning_session(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            early = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat().replace("+00:00", "Z")
            late = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat().replace("+00:00", "Z")
            # owner session: creates the task, then does execution work itself
            write_session(
                root / "-repo" / "2026-01-01T00-00-00-000Z_owner.jsonl",
                [
                    {"type": "model_change", "timestamp": early, "model": "zhipu-coding-plan/glm-5.3", "role": "default"},
                    {
                        "type": "message",
                        "timestamp": early,
                        "message": {
                            "role": "assistant",
                            "usage": {},
                            "content": [{"type": "toolCall", "name": "bash", "arguments": {"command": "./juspctl plan --task t-1"}}],
                        },
                    },
                    {
                        "type": "message",
                        "timestamp": early,
                        "message": {
                            "role": "assistant",
                            "usage": {},
                            "content": [{"type": "toolCall", "name": "read", "arguments": {"path": "src/a.ts", "i": "task t-1"}}],
                        },
                    },
                ],
            )
            # later session that only discusses the same task id
            write_session(
                root / "-repo" / "2026-01-01T00-00-00-000Z_reviewer.jsonl",
                [
                    {
                        "type": "message",
                        "timestamp": late,
                        "message": {
                            "role": "assistant",
                            "usage": {},
                            "content": [{"type": "toolCall", "name": "read", "arguments": {"path": "src/x.tsx", "i": "review t-1"}}],
                        },
                    }
                ],
            )
            report = check_role_routing.build_report(root, None, 1, CATALOG, task="t-1")
        # only the owner session counts, so the reviewer's .tsx read is not attributed
        self.assertEqual(report["sessionCount"], 1)
        self.assertEqual(report["mainSession"]["uiCallsOnMainTier"], 0)
        self.assertEqual(report["tierSplit"]["ownerExecutionCalls"], 2)

    def test_task_filter_without_any_session_reports_a_gap(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_session(
                root / "-repo" / "2026-01-01T00-00-00-000Z_a.jsonl",
                [message([("read", {"path": "src/a.ts"})])],
            )
            report = check_role_routing.build_report(root, None, 1, CATALOG, task="missing-task")
            result = check_role_routing.gate_report(report)
        self.assertEqual(report["sessionCount"], 0)
        self.assertTrue(result["pass"])
        self.assertIn("no-sessions-for-task", [v["code"] for v in result["advisory"]])

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


class RouteWorkTest(unittest.TestCase):
    def test_implement_with_ui_paths_adds_vision_tier(self) -> None:
        packs = route_work.plan_dispatch("t1", "implement", "o", ["src/admin-console/Page.tsx"], "/tmp/x", "", "")
        tiers = [p["tier"] for p in packs]
        # the visual baseline precedes the frontend implementation lane
        self.assertEqual(tiers, ["vision", "ui-impl"])
        self.assertEqual(packs[0]["agent"], "team-os-ui-designer")
        self.assertEqual(packs[1]["agent"], "team-os-ui-implementer")

    def test_implement_without_ui_paths_is_execution_only(self) -> None:
        packs = route_work.plan_dispatch("t2", "implement", "o", ["internal/api/h.go"], "/tmp/x", "", "")
        self.assertEqual([p["tier"] for p in packs], ["execution"])

    def test_research_routes_to_scout(self) -> None:
        packs = route_work.plan_dispatch("t3", "research", "o", [], "/tmp/x", "", "")
        self.assertEqual(packs[0]["agent"], "scout")
        self.assertEqual(packs[0]["tier"], "execution-scout")

    def test_plan_routes_to_planner_alt(self) -> None:
        packs = route_work.plan_dispatch("t4", "plan", "o", [], "/tmp/x", "", "")
        self.assertEqual(packs[0]["agent"], "team-os-planner-alt")
        self.assertEqual(packs[0]["tier"], "adjudication-draft")

    def test_review_routes_to_deep_reviewer(self) -> None:
        packs = route_work.plan_dispatch("t5", "review", "o", [], "/tmp/x", "", "")
        self.assertEqual(packs[0]["agent"], "team-os-deep-reviewer")

    def test_render_writes_packs(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            packs = route_work.plan_dispatch("t6", "implement", "结果是 X", ["src/a.ts"], raw, "", "")
            route_work.render_packs(packs, "t6", "结果是 X", ["src/a.ts"], raw, "", "", 2, 20)
            p = Path(packs[0]["pack"])
            self.assertTrue(p.exists())
            text = p.read_text(encoding="utf-8")
            self.assertIn("结果是 X", text)
            self.assertIn("允许写入", text)
            self.assertIn("停止条件", text)


class StopLossAndCadenceTest(unittest.TestCase):
    def _lane_with_failures(self, text_lines: list[str]) -> Path:
        raw = tempfile.TemporaryDirectory()
        root = Path(raw.name)
        write_session(
            root / "-repo" / "2026-01-01T00-00-00-000Z_owner.jsonl",
            [
                {"type": "model_change", "timestamp": stamp(30), "model": "zhipu-coding-plan/glm-5.3", "role": "default"},
                message([("task", {"tasks": [{"agent": "team-os-bounded-worker", "task": "run"}]})]),
            ],
        )
        entries: list[dict] = [
            {"type": "model_change", "timestamp": stamp(25), "model": "teamorouter/deepseek-flash", "role": "default"}
        ]
        for index, text in enumerate(text_lines):
            entries.append(
                {
                    "type": "message",
                    "timestamp": stamp(20 - index),
                    "message": {
                        "role": "assistant",
                        "usage": {},
                        "content": [{"type": "text", "text": text}],
                    },
                }
            )
        write_session(root / "-repo" / "2026-01-01T00-00-00-000Z_owner" / "RunLane.jsonl", entries)
        self.addCleanup(raw.cleanup)
        return root

    def test_repeated_failure_without_pass_exceeds_budget(self) -> None:
        root = self._lane_with_failures(
            ["FAIL: readyz 超时（MindIE 未注册）", "复跑后 FAIL: readyz 超时（MindIE 未注册）"]
        )
        report = check_role_routing.build_report(root, None, 1, CATALOG)
        result = check_role_routing.gate_report(report)
        codes = [v["code"] for v in result["blocking"]]
        self.assertIn("failure-budget-exceeded", codes)

    def test_verdict_pass_clears_the_budget(self) -> None:
        root = self._lane_with_failures(
            ["FAIL: readyz 超时（MindIE 未注册）", "复跑后 FAIL: readyz 超时（MindIE 未注册）", "VERDICT: readyz PASS"]
        )
        report = check_role_routing.build_report(root, None, 1, CATALOG)
        result = check_role_routing.gate_report(report)
        self.assertNotIn("failure-budget-exceeded", [v["code"] for v in result["blocking"]])

    def test_quoted_goal_text_is_not_a_success_marker(self) -> None:
        root = self._lane_with_failures(
            ["验收=ALL CHECKS PASSED", "FAIL: readyz 超时（MindIE 未注册）", "FAIL: readyz 超时（MindIE 未注册）"]
        )
        report = check_role_routing.build_report(root, None, 1, CATALOG)
        self.assertFalse(report["workerSuccessMarkerSeen"])
        self.assertTrue(report["targets"])  # report still shape-stable

    def test_owner_wait_share_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            entries = [
                {"type": "model_change", "timestamp": stamp(5), "model": "kimi-code/k3-256k", "role": "default"}
            ]
            for _ in range(4):
                entries.append(message([("hub", {"op": "wait"})]))
            entries.append(message([("read", {"path": "src/a.ts"})]))
            write_session(root / "-repo" / "2026-01-01T00-00-00-000Z_a.jsonl", entries)
            report = check_role_routing.build_report(root, None, 1, CATALOG)
            result = check_role_routing.gate_report(report)
        self.assertEqual(report["ownerHubWaits"], 4)
        self.assertIn("owner-wait-share-high", [v["code"] for v in result["advisory"]])

    def test_long_worker_without_verdict_markers_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_session(
                root / "-repo" / "2026-01-01T00-00-00-000Z_owner.jsonl",
                [{"type": "model_change", "timestamp": stamp(30), "model": "kimi-code/k3-256k", "role": "default"}],
            )
            entries = [
                {"type": "model_change", "timestamp": stamp(20), "model": "teamorouter/deepseek-flash", "role": "default"}
            ]
            entries.extend(message([("read", {"path": f"src/f{i}.ts"})]) for i in range(210))
            write_session(root / "-repo" / "2026-01-01T00-00-00-000Z_owner" / "LongLane.jsonl", entries)
            report = check_role_routing.build_report(root, None, 1, CATALOG)
            result = check_role_routing.gate_report(report)
        self.assertIn("worker-cadence-missing", [v["code"] for v in result["advisory"]])


class DispatchPolicySingleSourceTest(unittest.TestCase):
    """The pack the worker receives and the gate that judges it must read the
    same failure budget; a duplicated literal silently drifts."""

    def test_both_scripts_read_the_catalog_policy(self) -> None:
        catalog = check_role_routing.read_yaml(CATALOG)
        policy = check_role_routing.dispatch_policy(catalog)
        self.assertEqual(policy["failureBudget"], 2)
        self.assertEqual(policy["cadenceMinutes"], 20)
        self.assertEqual(route_work.dispatch_policy(CATALOG), policy)

    def test_pack_uses_the_catalog_budget(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            catalog_path = Path(raw) / "catalog.yaml"
            catalog_path.write_text(
                "activePortfolio:\n  dispatchPolicy:\n    failureBudget: 3\n    cadenceMinutes: 7\n",
                encoding="utf-8",
            )
            policy = route_work.dispatch_policy(catalog_path)
            self.assertEqual(policy["failureBudget"], 3)
            self.assertEqual(policy["cadenceMinutes"], 7)
            packs = route_work.plan_dispatch("t", "implement", "o", ["src/a.ts"], raw, "", "")
            route_work.render_packs(
                packs, "t", "o", ["src/a.ts"], raw, "", "", policy["failureBudget"], policy["cadenceMinutes"]
            )
            text = Path(packs[0]["pack"]).read_text(encoding="utf-8")
        self.assertIn("失败预算 = 3 轮", text)
        self.assertIn("每 7 分钟", text)

    def test_gate_uses_catalog_budget_when_not_overridden(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            catalog_path = Path(raw) / "catalog.yaml"
            catalog_path.write_text(
                "activePortfolio:\n  dispatchPolicy:\n    failureBudget: 5\n", encoding="utf-8"
            )
            policy = check_role_routing.dispatch_policy(check_role_routing.read_yaml(catalog_path))
        self.assertEqual(policy["failureBudget"], 5)

    def test_out_flag_controls_pack_directory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            out = Path(raw) / "custom"
            packs = route_work.plan_dispatch("t", "research", "o", [], raw, "", "", str(out))
            self.assertTrue(packs[0]["pack"].startswith(str(out)))
            route_work.render_packs(packs, "t", "o", [], raw, "", "", 2, 20)
            self.assertTrue(Path(packs[0]["pack"]).is_file())


class ConstraintAndEdgeTest(unittest.TestCase):
    """Cross-task learning edge and explicit node edges."""

    def _registry(self, raw: str) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "constraints.json"
        path.write_text(raw, encoding="utf-8")
        return path

    REGISTRY = json.dumps(
        {
            "version": 1,
            "constraints": [
                {
                    "id": "C-A",
                    "claim": "非 root 在 raw docker 拿不到 NPU",
                    "status": "active",
                    "scope": {"workspaces": ["workload"], "profiles": ["npu-arm64"], "keywords": ["npu"]},
                },
                {"id": "C-CLOSED", "claim": "已闭环的教训", "status": "retired", "scope": {}},
                {"id": "C-GLOBAL", "claim": "全局约束", "status": "active", "scope": {}},
                {
                    "id": "C-WS",
                    "claim": "仅按工作区限定",
                    "status": "active",
                    "scope": {"workspaces": ["workload"]},
                },
            ],
        },
        ensure_ascii=False,
    )

    def test_load_skips_retired_constraints(self) -> None:
        loaded = route_work.load_constraints(str(self._registry(self.REGISTRY)))
        self.assertEqual([item["id"] for item in loaded], ["C-A", "C-GLOBAL", "C-WS"])

    def test_scope_decides_by_condition_not_by_shared_workspace(self) -> None:
        loaded = route_work.load_constraints(str(self._registry(self.REGISTRY)))
        ids = lambda result: [item["id"] for item in result]
        # C-A declares keywords: a shared workspace alone must not pull it in
        self.assertEqual(ids(route_work.match_constraints(loaded, ["workload"], "普通任务")), ["C-GLOBAL", "C-WS"])
        self.assertEqual(ids(route_work.match_constraints(loaded, ["admin-console"], "升级 NPU 探针")), ["C-A", "C-GLOBAL"])
        self.assertEqual(ids(route_work.match_constraints(loaded, ["admin-console"], "改表格分组")), ["C-GLOBAL"])
        # profiles are the sharp condition when declared
        self.assertEqual(
            ids(route_work.match_constraints(loaded, [], "普通任务", ["npu-arm64"])), ["C-A", "C-GLOBAL"]
        )

    def test_pack_carries_constraints_and_carry_forward(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            carry_path = Path(raw) / "carry-forward.json"
            carry_path.write_text(
                json.dumps({"injections": [{"code": "context-median-high", "clause": "证据包限 30 行"}]}),
                encoding="utf-8",
            )
            carry = route_work.load_carry_forward(str(carry_path))
            packs = route_work.plan_dispatch("t", "implement", "o", ["src/a.tsx"], raw, "", "")
            route_work.render_packs(
                packs,
                "t",
                "o",
                ["src/a.tsx"],
                raw,
                "",
                "",
                2,
                20,
                [{"id": "C-A", "claim": "约束内容", "derivedFrom": "task-x"}],
                carry,
            )
            text = Path(packs[0]["pack"]).read_text(encoding="utf-8")
        self.assertIn("C-A", text)
        self.assertIn("证据包限 30 行", text)

    def test_edges_name_what_crosses(self) -> None:
        packs = route_work.plan_dispatch("t", "implement", "o", ["src/a.tsx"], "/tmp", "", "")
        stages = [pack["tier"] for pack in packs]
        self.assertEqual(stages, ["vision", "ui-impl"])
        implementation = packs[1]
        self.assertEqual(implementation["dependsOn"], ["vision"])
        self.assertTrue(all(implementation["crosses"]))
        self.assertIn("视觉基线结论", implementation["crosses"][0])
        self.assertTrue(packs[0]["produces"])

    def test_frontend_lane_separates_from_generic_execution(self) -> None:
        ui = route_work.plan_dispatch("t", "implement", "o", ["src/a.tsx"], "/tmp", "", "")
        backend = route_work.plan_dispatch("t", "implement", "o", ["svc/x.go"], "/tmp", "", "")
        self.assertEqual([p["tier"] for p in ui], ["vision", "ui-impl"])
        self.assertEqual([p["tier"] for p in backend], ["execution"])
        self.assertEqual(backend[0]["agent"], "team-os-bounded-worker")

    def test_design_critical_marks_the_k3_escalation_path(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            packs = route_work.plan_dispatch(
                "t", "implement", "o", ["src/design-system/QualityRail.tsx"], raw, "", ""
            )
            route_work.render_packs(
                packs, "t", "o", ["src/design-system/QualityRail.tsx"], raw, "", "", 2, 20,
                None, None, True,
            )
            text = Path(packs[-1]["pack"]).read_text(encoding="utf-8")
        self.assertIn("kimi-code/k3", text)
        plain = route_work.classify(["src/domains/x.tsx"])
        self.assertFalse(plain["designCritical"])
        critical = route_work.classify(["src/design-system/styles.css"])
        self.assertTrue(critical["designCritical"])

    def test_ops_puts_preflight_before_execution(self) -> None:
        packs = route_work.plan_dispatch("t", "ops", "o", ["installer:scripts/deploy/x.sh"], "/tmp", "", "")
        self.assertEqual([pack["tier"] for pack in packs], ["prod-env", "execution"])
        self.assertEqual(packs[1]["dependsOn"], ["prod-env"])

    def test_independent_types_have_no_edge(self) -> None:
        packs = route_work.plan_dispatch("t", "implement", "o", ["src/a.ts"], "/tmp", "", "")
        self.assertEqual(packs[0]["dependsOn"], [])


class CarryForwardGateTest(unittest.TestCase):
    def test_gate_emits_injections_and_writes_carry_forward(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            entries = [
                {"type": "model_change", "timestamp": stamp(5), "model": "kimi-code/k3-256k", "role": "default"}
            ]
            entries.extend(message([("hub", {"op": "wait"})]) for _ in range(4))
            entries.append(message([("read", {"path": "src/a.ts"})]))
            write_session(root / "-repo" / "2026-01-01T00-00-00-000Z_a.jsonl", entries)
            report = check_role_routing.build_report(root, None, 1, CATALOG)
            policy = check_role_routing.dispatch_policy(check_role_routing.read_yaml(CATALOG))
            result = check_role_routing.gate_report(report, policy=policy)
            codes = [item["code"] for item in result["advisory"]]
            self.assertIn("owner-wait-share-high", codes)
            self.assertTrue(result["injections"])
            written = check_role_routing.write_carry_forward(root, None, result)
            self.assertIsNotNone(written)
            payload = json.loads(Path(written).read_text(encoding="utf-8"))
        self.assertTrue(payload["injections"])
        self.assertIn("clause", payload["injections"][0])

    def test_catalog_declares_a_clause_for_every_injected_advisory(self) -> None:
        policy = check_role_routing.dispatch_policy(check_role_routing.read_yaml(CATALOG))
        declared = policy["advisoryInjections"]
        for code in (
            "owner-wait-share-high",
            "owner-execution-share-high",
            "context-median-high",
            "worker-cadence-missing",
            "stop-marker-recorded",
            "planning-not-half-to-adjudication",
        ):
            self.assertIn(code, declared, f"{code} has no injection clause")
            self.assertTrue(str(declared[code]).strip())

    def test_passing_receipts_suppress_the_failure_budget_to_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            write_session(
                root / "-repo" / "2026-01-01T00-00-00-000Z_owner.jsonl",
                [{"type": "model_change", "timestamp": stamp(5), "model": "kimi-code/k3-256k", "role": "default"}],
            )
            failures = [
                {"type": "model_change", "timestamp": stamp(5), "model": "teamorouter/deepseek-flash", "role": "default"}
            ]
            for _ in range(2):
                failures.append(
                    {
                        "type": "message",
                        "timestamp": stamp(1),
                        "message": {
                            "role": "assistant",
                            "usage": {},
                            "content": [{"type": "text", "text": "FAIL: readyz 超时"}],
                        },
                    }
                )
            write_session(root / "-repo" / "2026-01-01T00-00-00-000Z_owner" / "RunLane.jsonl", failures)
            report = check_role_routing.build_report(root, None, 1, CATALOG)
        blocked = check_role_routing.gate_report(report, receipts_passed=False)
        self.assertIn("failure-budget-exceeded", [v["code"] for v in blocked["blocking"]])
        suppressed = check_role_routing.gate_report(report, receipts_passed=True)
        self.assertNotIn("failure-budget-exceeded", [v["code"] for v in suppressed["blocking"]])
        self.assertIn("failure-budget-exceeded", [v["code"] for v in suppressed["advisory"]])


class SessionFactsTest(unittest.TestCase):
    """The code node that replaces hand-written session forensics."""

    def test_facts_count_turns_tokens_tools_and_hub_ops(self) -> None:
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "session_facts", Path(__file__).resolve().with_name("session_facts.py")
        )
        assert spec and spec.loader
        session_facts = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = session_facts
        spec.loader.exec_module(session_facts)

        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            entries = [
                {"type": "model_change", "timestamp": stamp(5), "model": "kimi-code/k3-256k", "role": "default"},
                {
                    "type": "message",
                    "timestamp": stamp(4),
                    "message": {
                        "role": "assistant",
                        "usage": {"input": 100, "cacheRead": 900, "output": 10},
                        "content": [
                            {"type": "toolCall", "name": "hub", "arguments": {"op": "wait"}},
                            {"type": "toolCall", "name": "read", "arguments": {"path": "src/a.ts"}},
                        ],
                    },
                },
                {
                    "type": "message",
                    "timestamp": stamp(3),
                    "message": {
                        "role": "assistant",
                        "usage": {"input": 50, "cacheRead": 50, "output": 5},
                        "content": [{"type": "toolCall", "name": "task", "arguments": {"tasks": [{"agent": "scout"}]}}],
                    },
                },
            ]
            write_session(root / "-repo" / "2026-01-01T00-00-00-000Z_a.jsonl", entries)
            files = session_facts.session_files(root, None)
            facts = session_facts.scan(files[0], None)
        self.assertEqual(facts["toolCalls"], 3)
        self.assertEqual(facts["executionCalls"], 1)
        self.assertEqual(facts["hubOps"], {"wait": 1})
        self.assertEqual(facts["dispatches"], {"scout": 1})
        self.assertEqual(sum(facts["inputTokens"].values()), 150)
        self.assertEqual(sum(facts["cacheReadTokens"].values()), 950)


if __name__ == "__main__":
    unittest.main()

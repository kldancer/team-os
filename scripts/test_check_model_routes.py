#!/usr/bin/env python3
"""Unit tests for the model-route verification script."""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().with_name("check_model_routes.py")
SPEC = importlib.util.spec_from_file_location("check_model_routes", SCRIPT)
assert SPEC and SPEC.loader
check_model_routes = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = check_model_routes
SPEC.loader.exec_module(check_model_routes)


def write_stats(path: Path, rows: list[tuple], tool_rows: list[tuple]) -> None:
    connection = sqlite3.connect(path)
    with connection:
        connection.execute(
            """
            create table messages (
                id integer primary key autoincrement, session_file text, entry_id text,
                folder text, model text, provider text, api text, timestamp integer,
                input_tokens integer, output_tokens integer, cache_read_tokens integer,
                cost_total real, agent_type text
            )
            """
        )
        connection.execute(
            """
            create table tool_calls (
                id integer primary key autoincrement, session_file text, entry_id text,
                tool_call_id text, folder text, tool_name text, model text, provider text,
                timestamp integer, agent_type text, args_chars integer, result_chars integer
            )
            """
        )
        connection.executemany(
            "insert into messages (model, provider, timestamp, input_tokens, output_tokens,"
            " cache_read_tokens, cost_total, agent_type) values (?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        connection.executemany(
            "insert into tool_calls (model, agent_type, timestamp, tool_name, args_chars, result_chars)"
            " values (?, ?, ?, ?, ?, ?)",
            tool_rows,
        )
    connection.close()


class ModelRouteCheckTest(unittest.TestCase):
    def test_mismatched_and_missing_roles_are_reported(self) -> None:
        expected = {"default": "router/fast-free", "plan_owner": "router/sol", "ui_deep": "router/astra"}
        issues = check_model_routes.check_routes(
            expected,
            {"default": "router/fast-free", "plan_owner": "router/luna", "ui_deep": ""},
        )
        joined = "\n".join(issues)
        self.assertIn("plan_owner", joined)
        self.assertIn("router/luna", joined)
        self.assertIn("ui_deep", joined)
        self.assertNotIn("default", joined)

    def test_matching_roles_produce_no_issues(self) -> None:
        expected = {role: f"router/{role}" for role in check_model_routes.ROLES}
        self.assertEqual(check_model_routes.check_routes(expected, dict(expected)), [])
        self.assertIn("plan_alt", check_model_routes.ROLES)

    def test_thinking_level_suffix_is_not_treated_as_drift(self) -> None:
        expected = {role: f"router/{role}" for role in check_model_routes.ROLES}
        configured = dict(expected)
        configured["default"] = f"{expected['default']}:high"
        self.assertEqual(check_model_routes.check_routes(expected, configured), [])
        self.assertEqual(
            check_model_routes.split_selector("router/fast-free:xhigh"),
            ("router/fast-free", "xhigh"),
        )
        self.assertEqual(check_model_routes.split_selector("router/sol"), ("router/sol", ""))

    def test_agent_chains_read_both_string_and_list_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            agents = Path(raw)
            (agents / "team-os-bounded-worker.md").write_text(
                '---\nname: w\nmodel: ["@fast_worker", "deepseek/deepseek-flash"]\ntools: [read]\n---\n\nbody\n',
                encoding="utf-8",
            )
            (agents / "team-os-planner.md").write_text(
                "---\nname: p\nmodel: router/sol\n---\n", encoding="utf-8"
            )
            chains = check_model_routes.agent_chains(agents)
        self.assertEqual(
            chains["team-os-bounded-worker"], ["@fast_worker", "deepseek/deepseek-flash"]
        )
        self.assertEqual(chains["team-os-planner"], ["router/sol"])

    def test_chain_drift_and_mixed_billing_classes_are_rejected(self) -> None:
        billing = {"deepseek": "pay-as-you-go", "kimi-code": "subscription"}
        aliases = {"@fast_worker": "deepseek"}
        declared = {"worker": ["@fast_worker", "deepseek/deepseek-flash"]}
        self.assertEqual(
            check_model_routes.check_chains(
                {"worker": ["@fast_worker", "deepseek/deepseek-flash"]}, declared, billing, aliases
            ),
            [],
        )
        mixed = check_model_routes.check_chains(
            {"worker": ["@fast_worker", "kimi-code/kimi-for-coding"]}, declared, billing, aliases
        )
        self.assertIn("mixes billing classes", "\n".join(mixed))
        undeclared = check_model_routes.check_chains(
            {"worker": ["@fast_worker"], "helper": ["@fast_worker"]}, declared, billing, aliases
        )
        self.assertIn("not declared in catalog", "\n".join(undeclared))
        missing = check_model_routes.check_chains({}, declared, billing, aliases)
        self.assertIn("missing from omp/agents", "\n".join(missing))
        unlisted = check_model_routes.check_chains(
            {"worker": ["@fast_worker", "ghost/model"]}, declared, billing, aliases
        )
        self.assertIn("outside ompProviderBilling", "\n".join(unlisted))
        assert check_model_routes.check_chains(
            {"worker": ["@fast_worker"]}, {"worker": ["@fast_worker"]}, billing, aliases
        ) == []

    def test_unconfigured_alias_is_reported(self) -> None:
        issues = check_model_routes.check_chains(
            {"worker": ["@ghost"]},
            {"worker": ["@ghost"]},
            {"deepseek": "pay-as-you-go"},
            {"@fast_worker": "deepseek"},
        )
        self.assertIn("binds undeclared alias", "\n".join(issues))

    def test_usage_report_aggregates_actual_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            stats = Path(raw) / "stats.db"
            now = int(time.time() * 1000)
            write_stats(
                stats,
                [
                    ("gpt-5.6-sol", "cliproxyapi", now, 100, 10, 900, 0.0, "main"),
                    ("gpt-5.6-sol", "cliproxyapi", now, 200, 20, 1800, 0.0, "subagent"),
                    ("deepseek-v4-flash", "teamorouter", now, 300, 30, 2700, 0.5, "subagent"),
                    ("deepseek-v4-flash", "teamorouter", now - 40 * 86400 * 1000, 1, 1, 1, 0.1, "subagent"),
                ],
                [
                    ("deepseek-v4-flash", "subagent", now, "read", 100, 12000),
                    ("gpt-5.6-sol", "main", now, "grep", 50, 5000),
                ],
            )
            report = check_model_routes.usage_report(
                stats, 7, {"analysis": ["kimi-"], "execution": ["deepseek-"]}
            )
        self.assertTrue(report["available"])
        rows = {(row["model"], row["agentType"]): row for row in report["byModel"]}
        self.assertEqual(rows[("deepseek-v4-flash", "subagent")]["messages"], 1)
        self.assertEqual(rows[("gpt-5.6-sol", "main")]["messages"], 1)
        tiers = {(row["tier"], row["agentType"]): row for row in report["byTier"]}
        self.assertEqual(tiers[("execution", "subagent")]["messages"], 1)
        self.assertEqual(tiers[("standby", "subagent")]["messages"], 1)
        self.assertEqual(check_model_routes.tier_of("glm-5.3-flash", {"vision": ["glm-5.3-flash"], "adjudication": ["glm-"]}), "vision")
        self.assertEqual(check_model_routes.tier_of("glm-5", {"vision": ["glm-5.3-flash"], "adjudication": ["glm-"]}), "adjudication")
        self.assertIsNotNone(tiers[("execution", "subagent")]["offPeakShare"])
        self.assertEqual(report["contextCharsByModel"][0]["resultChars"], 12000)

    def test_task_agent_overrides_are_checked_against_the_catalog(self) -> None:
        expected = {"task": "@fast_worker", "scout": "@fast_worker"}
        aliases = {"@fast_worker"}
        roles = {"fast_worker": "router/fast"}
        self.assertEqual(
            check_model_routes.check_task_overrides(expected, dict(expected), aliases, roles), []
        )
        drift = check_model_routes.check_task_overrides(expected, {"task": "@fast_worker"}, aliases, roles)
        self.assertEqual(len(drift), 1)
        self.assertIn("scout", drift[0])
        undeclared = check_model_routes.check_task_overrides(
            {"task": "@ghost"}, {"task": "@ghost"}, aliases, roles
        )
        self.assertIn("undeclared alias", undeclared[0])
        unconfigured = check_model_routes.check_task_overrides(
            {"task": "@fast_worker"}, {"task": "@fast_worker"}, aliases, {"fast_worker": ""}
        )
        self.assertIn("does not configure", unconfigured[0])

    def test_context_waste_reports_baseline_and_repeated_calls(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            stats = Path(raw) / "stats.db"
            now = int(time.time() * 1000)
            write_stats(
                stats,
                [
                    ("kimi-k3-256k", "kimi-code", now - 500, 7000, 10, 600, 0.0, "subagent"),
                    ("kimi-k3-256k", "kimi-code", now - 400, 100, 10, 900, 0.0, "subagent"),
                    ("kimi-k3", "kimi-code", now - 300, 900, 10, 12000, 0.0, "main"),
                ],
                [
                    ("kimi-k3-256k", "subagent", now - 399, "read", 400, 4000),
                    ("kimi-k3-256k", "subagent", now - 398, "read", 400, 4000),
                    ("kimi-k3-256k", "subagent", now - 397, "grep", 60, 1000),
                ],
            )
            report = check_model_routes.usage_report(stats, 7, {})
        waste = report["contextWaste"]
        self.assertEqual(waste["subagentSessions"], 1)
        self.assertEqual(waste["subagentBaselineTokens"]["median"], 7600)
        self.assertEqual(waste["toolCalls"], 3)
        self.assertEqual(waste["repeatedToolCalls"], 1)
        self.assertEqual(waste["repeatedResultChars"], 4000)
        self.assertAlmostEqual(waste["repeatedCharShare"], 0.444, places=3)

    def test_declared_temporary_binding_is_accepted_but_real_drift_is_not(self) -> None:
        expected = {role: f"router/{role}" for role in check_model_routes.ROLES}
        configured = dict(expected)
        configured["default"] = "backup/glm-5.3:high"
        temporary = {"default": {"selector": "backup/glm-5.3:high", "revertTo": "router/default"}}
        self.assertEqual(check_model_routes.check_routes(expected, configured, temporary), [])
        self.assertNotEqual(check_model_routes.check_routes(expected, configured, {}), [])
        drifted = dict(configured)
        drifted["default"] = "backup/other-model"
        self.assertNotEqual(check_model_routes.check_routes(expected, drifted, temporary), [])

    def test_quota_window_verdict_and_action(self) -> None:
        policy = {"kimi-code": {"warmAt": 0.7, "downgradeAt": 0.9}}
        self.assertEqual(check_model_routes.quota_window_verdict(0.2, 0.7, 0.9, "ok"), "ok")
        self.assertEqual(check_model_routes.quota_window_verdict(0.75, 0.7, 0.9, "ok"), "warm")
        self.assertEqual(check_model_routes.quota_window_verdict(0.95, 0.7, 0.9, "ok"), "downgrade")
        self.assertEqual(check_model_routes.quota_window_verdict(0.4, 0.7, 0.9, "exhausted"), "exhausted")
        with tempfile.TemporaryDirectory() as raw:
            db = Path(raw) / "agent.db"
            missing = check_model_routes.quota_windows(db, 24, policy)
            self.assertFalse(missing["available"])
            self.assertIn("unknown", missing["action"])
            connection = sqlite3.connect(db)
            with connection:
                connection.execute(
                    "create table usage_history (id integer primary key, recorded_at integer, provider text,"
                    " account_key text, email text, account_id text, limit_id text, label text,"
                    " window_label text, used_fraction real, status text, resets_at integer)"
                )
                now = int(time.time() * 1000)
                connection.executemany(
                    "insert into usage_history (recorded_at, provider, window_label, used_fraction, status, resets_at)"
                    " values (?, ?, ?, ?, ?, ?)",
                    [
                        (now - 3600_000, "kimi-code", "5h limit", 0.3, "ok", now + 3600_000),
                        (now, "kimi-code", "5h limit", 0.92, "ok", now + 3600_000),
                    ],
                )
            connection.close()
            report = check_model_routes.quota_windows(db, 24, policy)
        self.assertTrue(report["available"])
        window = report["providers"][0]
        self.assertEqual(window["verdict"], "downgrade")
        self.assertEqual(window["peakFraction"], 0.92)
        self.assertEqual(window["samples"], 2)
        self.assertIn("kimi-code", report["action"])

    def test_missing_stats_database_reports_unavailable_instead_of_zero(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            report = check_model_routes.usage_report(Path(raw) / "absent.db", 7, {})
        self.assertFalse(report["available"])
        self.assertEqual(report["byTier"], [])
        self.assertEqual(report["byModel"], [])

    def test_cli_checks_the_live_binding_against_the_catalog(self) -> None:
        catalog = check_model_routes.read_yaml(check_model_routes.CATALOG)
        expected = check_model_routes.expected_routes(catalog)
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            overrides = check_model_routes.expected_task_overrides(catalog)
            home.joinpath("config.yml").write_text(
                "modelRoles:\n"
                + "".join(f"  {role}: {selector}\n" for role, selector in expected.items())
                + "task:\n  agentModelOverrides:\n"
                + "".join(f'    {agent}: "{alias}"\n' for agent, alias in overrides.items()),
                encoding="utf-8",
            )
            ok = subprocess.run(
                [sys.executable, str(SCRIPT), "--home", str(home), "--stats-db", str(home / "none.db")],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(ok.returncode, 0, ok.stderr)
            payload = json.loads(ok.stdout)
            self.assertEqual(payload["issues"], [])
            self.assertTrue(payload["routes"]["plan_owner"]["reserved"])
            self.assertFalse(payload["routes"]["default"]["reserved"])

            home.joinpath("config.yml").write_text(
                "modelRoles:\n"
                + "".join(f"  {role}: {selector}\n" for role, selector in expected.items())
                + "  default: router/gpt-expensive\n"
                + "task:\n  agentModelOverrides:\n"
                + "".join(f'    {agent}: "{alias}"\n' for agent, alias in overrides.items()),
                encoding="utf-8",
            )
            drifted = subprocess.run(
                [sys.executable, str(SCRIPT), "--home", str(home), "--stats-db", str(home / "none.db")],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(drifted.returncode, 2)
            self.assertIn("runtime binds", drifted.stderr)


if __name__ == "__main__":
    unittest.main()

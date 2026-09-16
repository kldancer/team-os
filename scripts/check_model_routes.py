#!/usr/bin/env python3
"""Verify runtime model-role bindings against the Team OS model catalog.

The catalog (`models/catalog.yaml`) owns the intended role -> selector mapping.
Each harness configures its own binding (for OMP: `<profile>/agent/config.yml`),
which is runtime user config and therefore can drift silently. This script
compares the two, checks that every projected agent binds to a declared alias,
and summarizes what the runtime actually resolved from its local usage
statistics so that a reserved GPT role never silently backs regular execution.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "models" / "catalog.yaml"
AGENTS_DIR = ROOT / "omp" / "agents"
ROLES = ("default", "plan_owner", "ui_deep", "deep_review", "fast_worker")
RESERVED_ROLES = ("plan_owner", "ui_deep", "deep_review")


class RouteError(ValueError):
    pass


def read_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - environment dependent
        raise RouteError(f"PyYAML is required to read {path}: {error}") from error
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise RouteError(f"cannot read {path}: {error}") from error
    if not isinstance(payload, dict):
        raise RouteError(f"{path} must contain a mapping")
    return payload


def expected_routes(catalog: dict) -> dict[str, str]:
    portfolio = catalog.get("activePortfolio")
    if not isinstance(portfolio, dict):
        raise RouteError("catalog is missing activePortfolio")
    selectors = portfolio.get("ompResolvedSelectors")
    if not isinstance(selectors, dict):
        raise RouteError("catalog is missing activePortfolio.ompResolvedSelectors")
    return {role: str(selectors.get(role, "")) for role in ROLES}


def declared_aliases(catalog: dict) -> set[str]:
    portfolio = catalog.get("activePortfolio")
    aliases = portfolio.get("ompRoleAliases") if isinstance(portfolio, dict) else None
    if not isinstance(aliases, dict):
        raise RouteError("catalog is missing activePortfolio.ompRoleAliases")
    return {f"@{alias}" for alias in aliases}


def configured_routes(config: dict) -> dict[str, str]:
    roles = config.get("modelRoles")
    if not isinstance(roles, dict):
        raise RouteError("runtime config is missing modelRoles")
    return {role: str(roles.get(role, "")) for role in ROLES}


def agent_bindings(agents_dir: Path) -> dict[str, str]:
    bindings: dict[str, str] = {}
    if not agents_dir.is_dir():
        return bindings
    for path in sorted(agents_dir.glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("model:"):
                bindings[path.stem] = line.split(":", 1)[1].strip().strip('"').strip("'")
                break
    return bindings


def split_selector(selector: str) -> tuple[str, str]:
    """Split a `model:thinking-level` selector into its model and level parts."""
    model, separator, level = selector.rpartition(":")
    if not separator or not level:
        return selector, ""
    return model, level


def check_routes(expected: dict[str, str], configured: dict[str, str]) -> list[str]:
    issues: list[str] = []
    for role in ROLES:
        want = expected.get(role, "")
        have = configured.get(role, "")
        if not want:
            issues.append(f"catalog does not declare role: {role}")
            continue
        want_model, _ = split_selector(want)
        have_model, _ = split_selector(have)
        if have_model != want_model:
            issues.append(
                f"role {role}: runtime binds {have or '<missing>'}, catalog expects {want}"
            )
    return issues


def expected_task_overrides(catalog: dict) -> dict[str, str]:
    portfolio = catalog.get("activePortfolio")
    overrides = portfolio.get("ompTaskAgentModelOverrides") if isinstance(portfolio, dict) else None
    if not isinstance(overrides, dict):
        raise RouteError("catalog is missing activePortfolio.ompTaskAgentModelOverrides")
    return {str(agent): str(alias) for agent, alias in overrides.items()}


def configured_task_overrides(config: dict) -> dict[str, str]:
    task = config.get("task")
    overrides = task.get("agentModelOverrides") if isinstance(task, dict) else None
    if not isinstance(overrides, dict):
        return {}
    return {str(agent): str(alias) for agent, alias in overrides.items()}


def check_task_overrides(
    expected: dict[str, str], configured: dict[str, str], aliases: set[str], roles: dict[str, str]
) -> list[str]:
    issues: list[str] = []
    for agent, alias in sorted(expected.items()):
        have = configured.get(agent, "")
        if have != alias:
            issues.append(
                f"task.agentModelOverrides.{agent}: runtime binds {have or '<missing>'}, catalog expects {alias}"
            )
            continue
        if alias not in aliases:
            issues.append(f"task.agentModelOverrides.{agent} uses undeclared alias {alias}")
            continue
        role = alias.lstrip("@")
        if role not in ROLES:
            issues.append(f"task.agentModelOverrides.{agent} binds unknown role {role}")
        elif not roles.get(role):
            issues.append(f"task.agentModelOverrides.{agent} binds role {role} the runtime does not configure")
    return issues


def check_bindings(bindings: dict[str, str], aliases: set[str], configured: dict[str, str]) -> list[str]:
    issues: list[str] = []
    for name, alias in sorted(bindings.items()):
        if not alias.startswith("@"):
            issues.append(f"agent {name} is not bound to a role alias: {alias or '<missing>'}")
            continue
        if alias not in aliases:
            issues.append(f"agent {name} binds undeclared alias {alias}")
            continue
        role = alias.lstrip("@")
        if role not in ROLES:
            issues.append(f"agent {name} binds unknown role {role}")
        elif not configured.get(role):
            issues.append(f"agent {name} binds role {role} that the runtime does not configure")
    return issues


def usage_report(stats_db: Path, days: int) -> dict:
    report = {
        "statsDb": str(stats_db),
        "windowDays": days,
        "available": False,
        "byModel": [],
        "contextCharsByModel": [],
        "reservedShare": None,
    }
    if not stats_db.is_file():
        return report
    try:
        connection = sqlite3.connect(f"file:{stats_db}?mode=ro", uri=True)
    except sqlite3.Error:
        return report
    with connection:
        cutoff_ms = int((time.time() - days * 86400) * 1000)
        rows = connection.execute(
            """
            select model, agent_type, count(*), sum(input_tokens), sum(output_tokens),
                   sum(cache_read_tokens), round(sum(cost_total), 4)
            from messages where timestamp >= ?
            group by 1, 2 order by 4 desc
            """,
            (cutoff_ms,),
        ).fetchall()
        chars = connection.execute(
            """
            select model, agent_type, count(*), sum(result_chars)
            from tool_calls where timestamp >= ?
            group by 1, 2 order by 4 desc
            """,
            (cutoff_ms,),
        ).fetchall()
    report["available"] = True
    report["byModel"] = [
        {
            "model": row[0],
            "agentType": row[1],
            "messages": row[2],
            "inputTokens": row[3] or 0,
            "outputTokens": row[4] or 0,
            "cacheReadTokens": row[5] or 0,
            "cost": row[6] or 0.0,
        }
        for row in rows
    ]
    report["contextCharsByModel"] = [
        {"model": row[0], "agentType": row[1], "toolCalls": row[2], "resultChars": row[3] or 0}
        for row in chars
    ]
    subagent = [row for row in rows if row[1] == "subagent"]
    total = sum(row[2] for row in subagent)
    reserved = sum(row[2] for row in subagent if row[0].startswith("gpt"))
    report["reservedShare"] = round(reserved / total, 3) if total else None
    return report


def collect(profile: str, home: Path | None, stats_db: Path, days: int) -> dict:
    catalog = read_yaml(CATALOG)
    target = home or Path("~/.omp/profiles").expanduser() / profile / "agent"
    config_path = target / "config.yml"
    config = read_yaml(config_path)
    expected = expected_routes(catalog)
    configured = configured_routes(config)
    issues = check_routes(expected, configured)
    aliases = declared_aliases(catalog)
    bindings = agent_bindings(AGENTS_DIR)
    issues.extend(check_bindings(bindings, aliases, configured))
    task_overrides = configured_task_overrides(config)
    issues.extend(
        check_task_overrides(expected_task_overrides(catalog), task_overrides, aliases, configured)
    )
    return {
        "profile": profile,
        "runtimeHome": str(target),
        "routes": {
            role: {
                "expected": expected.get(role, ""),
                "configured": configured.get(role, ""),
                "thinkingLevel": split_selector(configured.get(role, ""))[1] or None,
                "reserved": role in RESERVED_ROLES,
            }
            for role in ROLES
        },
        "agentBindings": bindings,
        "taskAgentModelOverrides": task_overrides,
        "issues": issues,
        "usage": usage_report(stats_db, days),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="team-os", help="OMP profile name")
    parser.add_argument("--home", type=Path, help="override the runtime agent directory")
    parser.add_argument("--stats-db", type=Path, help="override the runtime stats database")
    parser.add_argument("--stats-days", type=int, default=7, help="usage window in days")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = args.home or Path("~/.omp/profiles").expanduser() / args.profile / "agent"
    stats_db = args.stats_db or target.parent / "stats.db"
    try:
        report = collect(args.profile, args.home, stats_db, args.stats_days)
    except RouteError as error:
        print(f"check-model-routes: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if report["issues"]:
        for issue in report["issues"]:
            print(f"check-model-routes: {issue}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

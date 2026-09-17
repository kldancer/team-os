#!/usr/bin/env python3
"""Verify runtime model-role bindings against the Team OS model catalog.

The catalog (`models/catalog.yaml`) owns the intended role -> selector mapping.
Each harness configures its own binding (for OMP: `<profile>/agent/config.yml`),
which is runtime user config and therefore can drift silently. This script
compares the two, checks that every projected agent chain matches the declared
fallback chain, that no chain mixes billing classes, and summarizes what the
runtime actually resolved from its local usage statistics per portfolio tier.
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
ROLES = ("default", "plan_owner", "plan_alt", "ui_deep", "deep_review", "fast_worker", "fast_alt")
RESERVED_ROLES = ("plan_owner", "plan_alt", "ui_deep", "deep_review", "fast_alt")
PEAK_HOURS = (9, 10, 11, 14, 15, 16, 17)


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


def portfolio_of(catalog: dict) -> dict:
    portfolio = catalog.get("activePortfolio")
    if not isinstance(portfolio, dict):
        raise RouteError("catalog is missing activePortfolio")
    return portfolio


def mapping_key(portfolio: dict, key: str) -> dict:
    value = portfolio.get(key)
    if not isinstance(value, dict):
        raise RouteError(f"catalog is missing activePortfolio.{key}")
    return value


def expected_routes(catalog: dict) -> dict[str, str]:
    selectors = mapping_key(portfolio_of(catalog), "ompResolvedSelectors")
    return {role: str(selectors.get(role, "")) for role in ROLES}


def declared_aliases(catalog: dict) -> set[str]:
    aliases = mapping_key(portfolio_of(catalog), "ompRoleAliases")
    return {f"@{alias}" for alias in aliases}


def configured_routes(config: dict) -> dict[str, str]:
    roles = config.get("modelRoles")
    if not isinstance(roles, dict):
        raise RouteError("runtime config is missing modelRoles")
    return {role: str(roles.get(role, "")) for role in ROLES}


def agent_chains(agents_dir: Path) -> dict[str, list[str]]:
    """Read each projected agent's model chain, accepting a string or a list."""
    chains: dict[str, list[str]] = {}
    if not agents_dir.is_dir():
        return chains
    import yaml

    for path in sorted(agents_dir.glob("*.md")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("model:"):
                continue
            raw = line.split(":", 1)[1].strip()
            if raw.startswith("["):
                parsed = yaml.safe_load(raw)
                chain = [str(item) for item in parsed] if isinstance(parsed, list) else [raw]
            else:
                chain = [raw.strip('"').strip("'")]
            chains[path.stem] = chain
            break
    return chains


def declared_chains(catalog: dict) -> dict[str, list[str]]:
    chains = mapping_key(portfolio_of(catalog), "ompAgentFallbacks")
    return {str(agent): [str(item) for item in chain] for agent, chain in chains.items()}


def provider_billing(catalog: dict) -> dict[str, str]:
    billing = mapping_key(portfolio_of(catalog), "ompProviderBilling")
    return {str(provider): str(kind) for provider, kind in billing.items()}


def split_selector(selector: str) -> tuple[str, str]:
    """Split a `model:thinking-level` selector into its model and level parts."""
    model, separator, level = selector.rpartition(":")
    if not separator or not level:
        return selector, ""
    return model, level


def selector_provider(selector: str) -> str:
    model, _ = split_selector(selector)
    return model.split("/", 1)[0] if "/" in model else ""


def role_providers(configured: dict[str, str]) -> dict[str, str]:
    return {role: selector_provider(selector) for role, selector in configured.items() if selector}


def alias_providers(configured: dict[str, str]) -> dict[str, str]:
    return {f"@{role}": provider for role, provider in role_providers(configured).items()}


def temporary_bindings(catalog: dict) -> dict[str, dict]:
    portfolio = catalog.get("activePortfolio") or {}
    declared = portfolio.get("temporaryBindings") or {}
    if not isinstance(declared, dict):
        raise RouteError("activePortfolio.temporaryBindings must be a mapping")
    return {str(role): dict(entry or {}) for role, entry in declared.items()}


def check_routes(
    expected: dict[str, str], configured: dict[str, str], temporary: dict[str, dict] | None = None
) -> list[str]:
    issues: list[str] = []
    temporary = temporary or {}
    for role in ROLES:
        want = expected.get(role, "")
        have = configured.get(role, "")
        if not want:
            issues.append(f"catalog does not declare role: {role}")
            continue
        override = temporary.get(role) or {}
        declared_override, _ = split_selector(str(override.get("selector", "")))
        have_model, _ = split_selector(have)
        if declared_override and declared_override == have_model:
            continue
        want_model, _ = split_selector(want)
        if have_model != want_model:
            issues.append(
                f"role {role}: runtime binds {have or '<missing>'}, catalog expects {want}"
            )
    return issues


def check_role_billing(configured: dict[str, str], billing: dict[str, str]) -> list[str]:
    issues: list[str] = []
    for role, provider in sorted(role_providers(configured).items()):
        if provider not in billing:
            issues.append(f"role {role} binds provider {provider} outside ompProviderBilling")
    return issues


def expected_task_overrides(catalog: dict) -> dict[str, str]:
    overrides = mapping_key(portfolio_of(catalog), "ompTaskAgentModelOverrides")
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


def check_chains(
    chains: dict[str, list[str]],
    declared: dict[str, list[str]],
    billing: dict[str, str],
    aliases: dict[str, str],
) -> list[str]:
    """Each projected agent must carry exactly its declared chain, inside one cost tier."""
    issues: list[str] = []
    declared_aliases_in_chains = set(aliases)
    for name in sorted(set(chains) | set(declared)):
        chain = chains.get(name)
        if chain is None:
            issues.append(f"agent {name} is declared in the catalog but missing from omp/agents")
            continue
        want = declared.get(name)
        if want is None:
            issues.append(f"agent {name} is not declared in catalog ompAgentFallbacks")
            continue
        if chain != want:
            issues.append(f"agent {name}: chain {chain} does not match declared {want}")
        kinds: set[str] = set()
        for selector in chain:
            provider = aliases.get(selector, "") if selector.startswith("@") else selector_provider(selector)
            if selector.startswith("@") and selector not in declared_aliases_in_chains:
                issues.append(f"agent {name} binds undeclared alias {selector}")
            if provider in billing:
                kinds.add(billing[provider])
            else:
                issues.append(
                    f"agent {name} uses provider {provider or '<unresolved>'} outside ompProviderBilling"
                )
        if len(kinds) > 1:
            issues.append(
                f"agent {name} mixes billing classes {sorted(kinds)}: a fallback chain stays inside one cost tier"
            )
    return issues


def channel_policy(policy: dict, provider: str) -> dict:
    """Resolve a provider to its window policy entry (matched by the catalog `channel` field)."""
    entry = policy.get(provider)
    if isinstance(entry, dict):
        return entry
    for value in policy.values():
        if isinstance(value, dict) and str(value.get("channel") or "") == provider:
            return value
    return {}


def quota_window_verdict(used: float | None, warm: float, downgrade: float, status: str) -> str:
    if status and status != "ok":
        return "exhausted"
    if used is None:
        return "unknown"
    if used >= downgrade:
        return "downgrade"
    if used >= warm:
        return "warm"
    return "ok"


def quota_windows(quota_db: Path, hours: int, policy: dict) -> dict:
    """Subscription window guardrail: current usage, trend and the required action."""
    report = {
        "database": str(quota_db),
        "windowHours": hours,
        "available": False,
        "providers": [],
        "action": None,
        "runbook": None,
    }
    if not quota_db.is_file():
        report["action"] = "no-quota-database: window state unknown, do not assume headroom"
        return report
    try:
        connection = sqlite3.connect(f"file:{quota_db}?mode=ro", uri=True)
    except sqlite3.Error:
        return report
    with connection:
        cutoff = int((time.time() - hours * 3600) * 1000)
        rows = connection.execute(
            """
            select provider, window_label, used_fraction, status, resets_at, recorded_at
            from usage_history where recorded_at >= ? order by recorded_at
            """,
            (cutoff,),
        ).fetchall()
    if not rows:
        report["action"] = "no-recent-samples: window state unknown, do not assume headroom"
        return report
    report["available"] = True
    grouped: dict[tuple[str, str], list] = {}
    for provider, window_label, used, status, resets, recorded in rows:
        grouped.setdefault((str(provider), str(window_label)), []).append((recorded, used, status, resets))
    for (provider, window_label), samples in sorted(grouped.items()):
        latest = samples[-1]
        rules = channel_policy(policy, provider)
        warm = rules.get("warmAt", 0.7)
        downgrade = rules.get("downgradeAt", 0.9)
        verdict = quota_window_verdict(latest[1], warm, downgrade, latest[2])
        if verdict == "exhausted" and rules.get("onExhausted"):
            report["runbook"] = {
                "trigger": f"{provider} {window_label} exhausted",
                "steps": rules["onExhausted"],
            }
        report["providers"].append(
            {
                "provider": provider,
                "window": window_label,
                "usedFraction": latest[1],
                "status": latest[2],
                "verdict": verdict,
                "resetsAt": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime((latest[3] or 0) / 1000)),
                "samples": len(samples),
                "peakFraction": max((item[1] or 0) for item in samples),
                "recordedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime((latest[0] or 0) / 1000)),
            }
        )
    worst = {"ok": 0, "warm": 1, "downgrade": 2, "exhausted": 3, "unknown": 1}
    top = max(report["providers"], key=lambda item: worst.get(item["verdict"], 1), default=None)
    if top:
        report["action"] = {
            "ok": "headroom-ok",
            "warm": f"{top['provider']} window at {top['usedFraction']}: move heavy review and planning off-peak, keep short work on the 256K tier",
            "downgrade": f"{top['provider']} window at {top['usedFraction']}: route new planning and review to the other subscription tier and disclose the switch",
            "exhausted": f"{top['provider']} window exhausted: stop dispatching that tier, use the standby or pay-as-you-go channel and disclose",
            "unknown": "window state unknown: do not assume headroom",
        }[top["verdict"]]
    return report


def tier_of(model: str, tiers: dict) -> str:
    """Classify a runtime model id into a portfolio tier by longest matching prefix."""
    best_tier, best_length = "", 0
    for tier, prefixes in tiers.items():
        for prefix in prefixes:
            name = str(prefix)
            if model.startswith(name) and len(name) > best_length:
                best_tier, best_length = str(tier), len(name)
    if best_tier:
        return best_tier
    if model.startswith("gpt"):
        return "standby"
    return "other"


def context_waste(connection: sqlite3.Connection, cutoff_ms: int) -> dict:
    """Two measurable context-waste signals: subagent baseline cost and repeated tool calls."""
    first_calls = connection.execute(
        """
        select coalesce(session_file, ''), min(timestamp) from messages
        where timestamp >= ? and agent_type = 'subagent' group by 1
        """,
        (cutoff_ms,),
    ).fetchall()
    baselines = []
    for session_file, stamp in first_calls:
        row = connection.execute(
            "select input_tokens, cache_read_tokens from messages"
            " where coalesce(session_file, '') = ? and timestamp = ? limit 1",
            (session_file, stamp),
        ).fetchone()
        if row:
            baselines.append((row[0] or 0) + (row[1] or 0))
    baselines.sort()
    totals = connection.execute(
        "select count(*), coalesce(sum(result_chars), 0) from tool_calls where timestamp >= ?",
        (cutoff_ms,),
    ).fetchone()
    repeats = connection.execute(
        """
        select count(*), coalesce(sum(result_chars), 0) from tool_calls where timestamp >= ? and exists (
            select 1 from tool_calls earlier
            where earlier.session_file is tool_calls.session_file
              and earlier.tool_name is tool_calls.tool_name
              and earlier.args_chars is tool_calls.args_chars
              and earlier.timestamp < tool_calls.timestamp
        )
        """,
        (cutoff_ms,),
    ).fetchone()
    calls = totals[0] or 0
    repeat_calls = repeats[0] or 0

    def percentile(values: list[int], fraction: float) -> int | None:
        if not values:
            return None
        return values[min(len(values) - 1, int(len(values) * fraction))]

    return {
        "subagentSessions": len(baselines),
        "subagentBaselineTokens": {
            "min": baselines[0] if baselines else None,
            "median": percentile(baselines, 0.5),
            "p90": percentile(baselines, 0.9),
        },
        "toolCalls": calls,
        "repeatedToolCalls": repeat_calls,
        "repeatedCallShare": round(repeat_calls / calls, 3) if calls else None,
        "repeatedResultChars": repeats[1] or 0,
        "repeatedCharShare": round((repeats[1] or 0) / (totals[1] or 1), 3) if totals[1] else None,
    }


def usage_report(stats_db: Path, days: int, tiers: dict, quota_db: Path | None = None, quota_policy: dict | None = None) -> dict:
    report = {
        "statsDb": str(stats_db),
        "windowDays": days,
        "available": False,
        "peakHours": list(PEAK_HOURS),
        "byTier": [],
        "byModel": [],
        "contextCharsByModel": [],
        "contextWaste": {},
        "quotaWindows": {},
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
                   sum(cache_read_tokens), round(sum(cost_total), 4),
                   case when cast(strftime('%w', timestamp / 1000, 'unixepoch', 'localtime') as integer)
                                 between 1 and 5
                             and cast(strftime('%H', timestamp / 1000, 'unixepoch', 'localtime') as integer)
                                 in (9, 10, 11, 14, 15, 16, 17)
                        then 1 else 0 end as peak
            from messages where timestamp >= ?
            group by 1, 2, 8 order by 3 desc
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
    report["contextWaste"] = context_waste(connection, cutoff_ms)
    report["contextCharsByModel"] = [
        {"model": row[0], "agentType": row[1], "toolCalls": row[2], "resultChars": row[3] or 0}
        for row in chars
    ]
    aggregate: dict[tuple[str, str], dict] = {}
    for model, agent_type, messages, input_tokens, output_tokens, cache_read, cost, peak in rows:
        tier = tier_of(str(model), tiers)
        bucket = aggregate.setdefault(
            (tier, str(agent_type)),
            {
                "tier": tier,
                "agentType": agent_type,
                "messages": 0,
                "inputTokens": 0,
                "outputTokens": 0,
                "cacheReadTokens": 0,
                "cost": 0.0,
                "offPeakMessages": 0,
            },
        )
        bucket["messages"] += messages or 0
        bucket["inputTokens"] += input_tokens or 0
        bucket["outputTokens"] += output_tokens or 0
        bucket["cacheReadTokens"] += cache_read or 0
        bucket["cost"] += cost or 0.0
        if not peak:
            bucket["offPeakMessages"] += messages or 0
    for bucket in aggregate.values():
        bucket["cost"] = round(bucket["cost"], 4)
        bucket["offPeakShare"] = (
            round(bucket["offPeakMessages"] / bucket["messages"], 3) if bucket["messages"] else None
        )
        report["byTier"].append(bucket)
    report["byTier"].sort(key=lambda row: -row["messages"])
    if quota_db is not None:
        report["quotaWindows"] = quota_windows(quota_db, min(days, 2) * 24, quota_policy or {})
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
    return report


def collect(profile: str, home: Path | None, stats_db: Path, days: int, quota_db: Path | None = None) -> dict:
    catalog = read_yaml(CATALOG)
    target = home or Path("~/.omp/profiles").expanduser() / profile / "agent"
    config_path = target / "config.yml"
    config = read_yaml(config_path)
    expected = expected_routes(catalog)
    configured = configured_routes(config)
    billing = provider_billing(catalog)
    temporary = temporary_bindings(catalog)
    issues = check_routes(expected, configured, temporary)
    issues.extend(check_role_billing(configured, billing))
    chains = agent_chains(AGENTS_DIR)
    aliases = declared_aliases(catalog)
    issues.extend(check_chains(chains, declared_chains(catalog), billing, alias_providers(configured)))
    task_overrides = configured_task_overrides(config)
    issues.extend(
        check_task_overrides(expected_task_overrides(catalog), task_overrides, aliases, configured)
    )
    portfolio_quota = portfolio_of(catalog).get("quotaWindows") or {}
    quota_path = quota_db or target / "agent.db"
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
        "agentChains": chains,
        "temporaryBindings": {
            role: {
                **entry,
                "active": split_selector(str(configured.get(role, "")))[0] == split_selector(str(entry.get("selector", "")))[0],
            }
            for role, entry in temporary.items()
        },
        "taskAgentModelOverrides": task_overrides,
        "issues": issues,
        "usage": usage_report(stats_db, days, portfolio_of(catalog).get("tiers") or {}, quota_path, portfolio_quota),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="team-os", help="OMP profile name")
    parser.add_argument("--home", type=Path, help="override the runtime agent directory")
    parser.add_argument("--stats-db", type=Path, help="override the runtime stats database")
    parser.add_argument("--stats-days", type=int, default=7, help="usage window in days")
    parser.add_argument("--quota-db", type=Path, help="override the runtime agent database holding provider window usage")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    target = args.home or Path("~/.omp/profiles").expanduser() / args.profile / "agent"
    stats_db = args.stats_db or target.parent / "stats.db"
    try:
        report = collect(args.profile, args.home, stats_db, args.stats_days, args.quota_db)
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

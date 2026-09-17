#!/usr/bin/env python3
"""Measure whether the runtime actually routes work to the intended tier.

`check_model_routes.py` proves the bindings resolve; this script proves the
workflow *uses* them. It reads session transcripts only, and answers the four
routing questions that the catalog's routing rules assert:

1. planning split — dispatches to the analysis tier versus the adjudication tier;
2. vision tier — dispatches to the vision-tier agent and UI work done elsewhere;
3. cross-vendor review — dispatches to the judgement tier;
4. main-session thinning — how much execution work the main session still does
   itself, plus how often a context promotion to the 1M variant happened.

Nothing is guessed: missing sessions or an unreadable catalog are reported as
explicit gaps, and every metric carries the sample size behind it.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "models" / "catalog.yaml"
EXECUTION_TOOLS = ("bash", "read", "grep", "glob", "edit", "write")
UI_MARKERS = (".tsx", ".css", "admin-console", "portal", "console", "screenshot", ".png", "figma")
DEFAULT_PROFILE_ROOT = Path("~/.omp/profiles").expanduser()


class RoutingError(ValueError):
    pass


def read_yaml(path: Path) -> dict:
    try:
        import yaml
    except ImportError as error:  # pragma: no cover - environment dependent
        raise RoutingError(f"PyYAML is required to read {path}: {error}") from error
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise RoutingError(f"cannot read {path}: {error}") from error
    if not isinstance(payload, dict):
        raise RoutingError(f"{path} must contain a mapping")
    return payload


def tier_map(catalog: dict) -> tuple[dict[str, str], dict[str, str]]:
    """agent name -> tier, plus generic task/scout/sonic -> tier."""
    portfolio = catalog.get("activePortfolio") or {}
    alias_tier = portfolio.get("tiers") or {}
    aliases = portfolio.get("ompRoleAliases") or {}
    role_tier: dict[str, str] = {}
    for alias, model in aliases.items():
        for tier, prefixes in alias_tier.items():
            if any(str(model).startswith(str(prefix)) for prefix in prefixes):
                role_tier[str(alias)] = str(tier)
    agents: dict[str, str] = {}
    for agent, chain in (portfolio.get("ompAgentFallbacks") or {}).items():
        head = str(chain[0]) if chain else ""
        role = head.lstrip("@")
        if role in role_tier:
            agents[str(agent)] = role_tier[role]
    generics: dict[str, str] = {}
    for name, alias in (portfolio.get("ompTaskAgentModelOverrides") or {}).items():
        role = str(alias).lstrip("@")
        generics[str(name)] = role_tier.get(role, "execution")
    return agents, generics


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def session_files(root: Path, folder: str | None) -> list[Path]:
    if not root.is_dir():
        return []
    files = sorted(root.glob("*/[0-9]*.jsonl"))
    if folder:
        files = [path for path in files if folder in str(path.parent.name)]
    return files


def scan_session(path: Path, cutoff: datetime, agents: dict[str, str], generics: dict[str, str]) -> dict:
    dispatches: dict[str, int] = {}
    turns: dict[str, int] = {}
    execution_calls = 0
    total_calls = 0
    ui_calls_outside_vision = 0
    promotions = 0
    context_samples: list[int] = []
    current: str | None = None
    previous: str | None = None
    with path.open(errors="replace") as handle:
        lines = [line for line in handle if '"toolCall"' in line or '"model_change"' in line]
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        stamp = parse_timestamp(entry.get("timestamp"))
        if stamp is not None and stamp < cutoff:
            continue
        if entry.get("type") == "model_change":
            model = str(entry.get("model") or "")
            if previous is not None and "k3-256k" in previous and model.endswith("/k3"):
                promotions += 1
            previous, current = model, model
            continue
        message = entry.get("message") or {}
        if message.get("role") != "assistant":
            continue
        usage = message.get("usage") or {}
        if isinstance(usage, dict):
            measured = (usage.get("input") or 0) + (usage.get("cacheRead") or 0)
            if measured:
                context_samples.append(int(measured))
        model = str(current or "")
        turns[model] = turns.get(model, 0) + 1
        for block in message.get("content") or []:
            if not isinstance(block, dict) or block.get("type") != "toolCall":
                continue
            name = str(block.get("name") or "")
            arguments = json.dumps(block.get("arguments") or {}, ensure_ascii=False)
            total_calls += 1
            if name in EXECUTION_TOOLS:
                execution_calls += 1
            if name in ("task", "eval"):
                for item in block.get("arguments", {}).get("tasks") or []:
                    agent = str(item.get("agent") or "task")
                    tier = agents.get(agent) or generics.get(agent) or "execution"
                    dispatches[f"{agent}:{tier}"] = dispatches.get(f"{agent}:{tier}", 0) + 1
            if name not in ("task", "eval") and any(marker in arguments for marker in UI_MARKERS):
                ui_calls_outside_vision += 1
    return {
        "session": path.parent.name,
        "file": path.name,
        "turns": turns,
        "dispatches": dispatches,
        "toolCalls": total_calls,
        "executionCalls": execution_calls,
        "uiCallsOnMainTier": ui_calls_outside_vision,
        "promotions": promotions,
        "contextSamples": context_samples,
    }


def build_report(root: Path, folder: str | None, days: int, catalog_path: Path) -> dict:
    catalog = read_yaml(catalog_path)
    agents, generics = tier_map(catalog)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    files = session_files(root, folder)
    sessions = [scan_session(path, cutoff, agents, generics) for path in files]
    dispatches: dict[str, int] = {}
    tier_totals: dict[str, int] = {}
    turns: dict[str, int] = {}
    tool_calls = execution_calls = ui_main = promotions = 0
    context_samples: list[int] = []
    for session in sessions:
        context_samples.extend(session.get("contextSamples") or [])
        for key, count in session["dispatches"].items():
            dispatches[key] = dispatches.get(key, 0) + count
            tier_totals[key.rsplit(":", 1)[-1]] = tier_totals.get(key.rsplit(":", 1)[-1], 0) + count
        for model, count in session["turns"].items():
            turns[model] = turns.get(model, 0) + count
        tool_calls += session["toolCalls"]
        execution_calls += session["executionCalls"]
        ui_main += session["uiCallsOnMainTier"]
        promotions += session["promotions"]
    planning_split = {
        "analysisDispatches": sum(count for key, count in dispatches.items() if key.startswith("team-os-planner:")),
        "adjudicationDispatches": sum(count for key, count in dispatches.items() if key.startswith("team-os-planner-alt:")),
    }
    total_planning = planning_split["analysisDispatches"] + planning_split["adjudicationDispatches"]
    planning_split["shareToAdjudication"] = (
        round(planning_split["adjudicationDispatches"] / total_planning, 3) if total_planning else None
    )
    return {
        "sessionsRoot": str(root),
        "folderFilter": folder,
        "windowDays": days,
        "catalog": str(catalog_path),
        "sessionCount": len(sessions),
        "dispatches": dispatches,
        "dispatchTierTotals": tier_totals,
        "planningSplit": planning_split,
        "visionTierDispatches": sum(count for key, count in dispatches.items() if key.startswith("team-os-ui-designer:")),
        "judgementTierDispatches": sum(count for key, count in dispatches.items() if key.startswith("team-os-deep-reviewer:")),
        "mainSession": {
            "turns": turns,
            "toolCalls": tool_calls,
            "executionCalls": execution_calls,
            "executionShare": round(execution_calls / tool_calls, 3) if tool_calls else None,
            "uiCallsOnMainTier": ui_main,
            "promotionsTo1M": promotions,
            "contextMedian": (
                sorted(context_samples)[len(context_samples) // 2] if context_samples else None
            ),
            "contextSamples": len(context_samples),
        },
        "targets": {
            "planningHalfToAdjudication": (
                planning_split["shareToAdjudication"] is None or planning_split["shareToAdjudication"] >= 0.5
            ),
            "visionTierUsed": any(key.startswith("team-os-ui-designer:") for key in dispatches),
            "judgementTierUsed": any(key.startswith("team-os-deep-reviewer:") for key in dispatches),
            "mainExecutionShareBelow30Percent": (execution_calls / tool_calls) < 0.30 if tool_calls else None,
            "mainContextMedianBelow200k": (
                sorted(context_samples)[len(context_samples) // 2] < 200_000 if context_samples else None
            ),
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="team-os", help="OMP profile name")
    parser.add_argument("--sessions-root", type=Path, help="override the sessions directory")
    parser.add_argument("--folder", help="only count sessions whose folder name contains this text")
    parser.add_argument("--days", type=int, default=1, help="window in days")
    parser.add_argument("--catalog", type=Path, default=CATALOG, help="model catalog path")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.sessions_root or DEFAULT_PROFILE_ROOT / args.profile / "agent" / "sessions"
    try:
        report = build_report(root, args.folder, args.days, args.catalog)
    except RoutingError as error:
        print(f"check-role-routing: {error}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

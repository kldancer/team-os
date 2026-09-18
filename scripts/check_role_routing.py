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

Since 2026-09-17 the script also:

- counts lane/evidence child sessions (`parentSession` points at a top-level
  session) so the execution tier's real workload is not invisible;
- splits execution calls by *model tier*: calls made while the top-level
  session ran a subscription-tier model (kimi-code, zhipu-coding-plan,
  cliproxyapi, teamorouter gpt) are "owner self-execution", calls inside lane
  child sessions are "lane execution";
- detects production-remote commands (ssh/scp/docker run|exec|push, kubectl,
  helm, rsync) issued from the subscription-tier main session;
- `--task <id>` scopes every metric to the sessions that mention that task, so
  closing one task is never blocked by another task's sessions;
- `--gate` turns the metrics into a pass/fail compliance gate: blocking
  violations (subscription-tier production access, UI work without a vision
  dispatch) must be fixed before a task closes; advisory violations are
  reported without blocking.

Nothing is guessed: missing sessions or an unreadable catalog are reported as
explicit gaps, and every metric carries the sample size behind it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "models" / "catalog.yaml"
EXECUTION_TOOLS = ("bash", "read", "grep", "glob", "edit", "write")
# UI markers must be precise: this script now blocks task closure on main-tier
# UI work without a vision dispatch, so generic tokens such as "console" or
# "portal" (which appear in backend hosts, log lines and curl targets) are not
# markers. Only file-path-shaped or surface-specific evidence counts.
UI_MARKERS = (
    ".tsx",
    ".css",
    ".vue",
    ".svelte",
    "admin-console",
    "jusp-console",
    "portal-auth",
    "screenshot",
    ".png",
    ".svg",
    "figma",
)
DEFAULT_PROFILE_ROOT = Path("~/.omp/profiles").expanduser()

# Model tiers: execution tier models are deepseek; everything else on the
# subscription tiers (kimi-code, zhipu-coding-plan, cliproxyapi, gpt via
# teamorouter) counts as owner/subscription-tier work when used in the main
# session. Lane child sessions are execution work regardless of the model
# string inside them because lanes are resolved to the execution tier.
EXECUTION_MODEL_PATTERN = re.compile(r"deepseek")

# Production-remote command patterns. A main-session bash call matching these
# while on a subscription-tier model is a blocking violation: remote probes
# must go through prod-env executors or execution-tier workers.
PROD_COMMAND_PATTERN = re.compile(
    r"(ssh\s|scp\s|rsync\s|docker\s+(run|exec|push|login)\s|kubectl\s|helm\s|curl\s)",
    re.IGNORECASE,
)
DEFAULT_PROD_HOSTS = ("119.6.186.139", "119.6.186.140", "10.10.60.184")
# Stop-loss: the same acceptance point failing this many rounds must halt the
# loop and send the owner back to replanning (retro 2026-09-17: run1-run4 of the
# mindie task all failed step 1, D1 was known unfixable from run2 onward).
# The value is a catalog fact (activePortfolio.dispatchPolicy); this fallback is
# only used when the catalog cannot be read.
FAILURE_BUDGET_FALLBACK = 2
# Structured progress markers the dispatch pack requires from every worker.
# Markers must be *emitted*, not quoted from the dispatch pack. The pack template
# itself contains `VERDICT: <验收点> PASS|FAIL` and `STOP: <原因>`, so placeholders
# and contract narration are excluded: a marker counts only when it carries a
# concrete value.
VERDICT_PATTERN = re.compile(r"VERDICT:\s*([^\s<|]+)\s+(PASS|FAIL)(?![|])", re.IGNORECASE)
STOP_PATTERN = re.compile(r"\bSTOP:\s*(?!<)([^\s].{0,60})", re.IGNORECASE)
CONTRACT_NARRATION = ("回传", "失败预算", "写集合", "包内")
# Free-form failure signature: workers frequently quote the script's own failure
# line. The same normalised failure text repeating across messages is the
# observable form of "kept retrying the same acceptance point".
FAIL_SIGNATURE_PATTERN = re.compile(r"FAIL[:：]\s*([^\"\\`]{6,72})")
# PASS must be a machine-verifiable marker. Quoted goal text such as
# "ALL CHECKS PASSED" appears in pack narration and must not count as success.
IP_PATTERN = re.compile(r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b")


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


def dispatch_policy(catalog: dict) -> dict:
    """Failure budget, cadence and advisory injections from the catalog.

    Single source of truth: the gate and the pack generator both read it, so a
    verdict can be turned into the constraint that the next dispatch carries.
    """
    policy = (catalog.get("activePortfolio") or {}).get("dispatchPolicy") or {}
    budget = policy.get("failureBudget")
    cadence = policy.get("cadenceMinutes")
    injections = policy.get("advisoryInjections")
    return {
        "failureBudget": int(budget) if isinstance(budget, int) and budget > 0 else FAILURE_BUDGET_FALLBACK,
        "cadenceMinutes": int(cadence) if isinstance(cadence, int) and cadence > 0 else 30,
        "advisoryInjections": dict(injections) if isinstance(injections, dict) else {},
    }


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


def first_mention(path: Path, task: str) -> datetime | None:
    """Earliest timestamp of a transcript entry mentioning the task id."""
    earliest: datetime | None = None
    with path.open(errors="replace") as handle:
        for line in handle:
            if task not in line:
                continue
            entry = _safe_entry(line)
            stamp = parse_timestamp(entry.get("timestamp"))
            if stamp is not None and (earliest is None or stamp < earliest):
                earliest = stamp
    return earliest


def session_key(path: Path, owner: Path) -> str:
    """Identity of the session a file belongs to.

    Top-level sessions live at `<folder>/<stem>.jsonl`; their lane children live
    at `<folder>/<stem>/<lane>.jsonl`. Both map to the same key `<stem>`.
    """
    if _is_lane_file(path, owner):
        return owner.name
    return path.stem


def select_task_group(
    files: list[tuple[Path, Path]], task: str
) -> list[tuple[Path, Path]]:
    """Attribute a task to its owning session.

    `one-outcome-has-one-owner`: the task belongs to the session that mentioned
    it first (plus that session's lane children). A later session that merely
    reviews or discusses the same id does not extend the task's scope, so the
    gate is not contaminated by unrelated work.
    """
    groups: dict[str, list[tuple[Path, Path]]] = {}
    for path, owner in files:
        groups.setdefault(session_key(path, owner), []).append((path, owner))
    best: tuple[datetime, str, list[tuple[Path, Path]]] | None = None
    for key, members in groups.items():
        top_level = [path for path, owner in members if not _is_lane_file(path, owner)]
        earliest: datetime | None = None
        for member in top_level:
            stamp = first_mention(member, task)
            if stamp is not None and (earliest is None or stamp < earliest):
                earliest = stamp
        if earliest is None:
            continue
        if best is None or earliest < best[0]:
            best = (earliest, key, sorted(members, key=lambda item: str(item[0])))
    if best is None:
        return []
    return best[2]


def _safe_entry(line: str) -> dict:
    try:
        entry = json.loads(line)
    except json.JSONDecodeError:
        return {}
    return entry if isinstance(entry, dict) else {}


def line_mentions(entry: dict, task: str) -> bool:
    return task in json.dumps(entry, ensure_ascii=False)


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def is_subscription_model(model: str) -> bool:
    """True when the main session ran a subscription-tier model for this call.

    deepseek-* is the execution tier; everything else (kimi-code, glm,
    cliproxyapi gpt, teamorouter gpt) is subscription-tier owner work.
    """
    return not bool(EXECUTION_MODEL_PATTERN.search(model or ""))


def session_files(root: Path, folder: str | None) -> list[tuple[Path, Path]]:
    """Return (top_level_file, owning_top_level_dir) pairs.

    Top-level sessions are `<folder>/<session-dir-or-file>/…jsonl` matching
    `[0-9]*.jsonl`. Lane/evidence child sessions live inside the top-level
    session's directory (e.g. `AdminComputeLane.jsonl`) and declare
    `parentSession` pointing at the owning top-level session; they are grouped
    under their owner for lane-execution accounting.
    """
    if not root.is_dir():
        return []
    pairs: list[tuple[Path, Path]] = []
    for top in sorted(root.glob("*/[0-9]*.jsonl")):
        if folder and folder not in str(top.parent.name):
            continue
        pairs.append((top, top.parent))
    for top_dir in sorted(root.glob("*/[0-9]*")):
        if not top_dir.is_dir():
            continue
        if folder and folder not in str(top_dir.parent.name):
            continue
        for child in sorted(top_dir.glob("*.jsonl")):
            if child.name == "events.jsonl" or re.match(r"[0-9]", child.name):
                continue
            pairs.append((child, top_dir))
    # dedupe, keep deterministic order
    seen: set[tuple[str, str]] = set()
    out: list[tuple[Path, Path]] = []
    for f, owner in pairs:
        key = (str(f), str(owner))
        if key in seen:
            continue
        seen.add(key)
        out.append((f, owner))
    return out


def _is_lane_file(path: Path, owner_dir: Path) -> bool:
    """True when path is a child session inside the owner's directory
    (parentSession points at the top-level session)."""
    return path.parent == owner_dir and path.parent.name.startswith("2026-")


def scan_session(
    path: Path,
    owner_dir: Path,
    cutoff: datetime,
    agents: dict[str, str],
    generics: dict[str, str],
    prod_hosts: tuple[str, ...],
    task: str | None = None,
) -> dict | None:
    dispatches: dict[str, int] = {}
    turns: dict[str, int] = {}
    execution_calls = 0
    total_calls = 0
    ui_calls_outside_vision = 0
    promotions = 0
    context_samples: list[int] = []
    owner_execution = 0
    owner_calls = 0
    owner_all_calls = 0
    lane_execution = 0
    lane_calls = 0
    prod_calls: list[dict] = []
    verdicts: list[tuple[str, str, str]] = []
    stops = 0
    hub_waits = 0
    owner_all = 0
    failure_signatures: dict[str, int] = {}
    success_seen = False
    current: str | None = None
    previous: str | None = None
    is_lane = _is_lane_file(path, owner_dir)
    with path.open(errors="replace") as handle:
        raw = handle.readlines()
    window: tuple[datetime, datetime] | None = None
    if task:
        mentions = [
            parse_timestamp(entry.get("timestamp"))
            for entry in (_safe_entry(line) for line in raw)
            if line_mentions(entry, task)
        ]
        stamps = [stamp for stamp in mentions if stamp is not None]
        if not stamps:
            return None
        # A long-lived session can cover several tasks. Attribution is the span
        # between the first and last mention of the task id, so work belonging
        # to other tasks in the same session is not charged to this one.
        window = (min(stamps), max(stamps))
    for line in raw:
        for point, outcome in VERDICT_PATTERN.findall(line):
            verdicts.append((str(point), outcome.upper(), ""))
        if not any(word in line for word in CONTRACT_NARRATION):
            stops += len(STOP_PATTERN.findall(line))
        if is_lane:
            seen_here: set[str] = set()
            for raw_signature in FAIL_SIGNATURE_PATTERN.findall(line):
                normalized = re.sub(r"[\s`'\"“”。，、]+", "", str(raw_signature))[:24]
                if normalized and normalized not in seen_here:
                    seen_here.add(normalized)
                    failure_signatures[normalized] = failure_signatures.get(normalized, 0) + 1
            if any(outcome == "PASS" for _, outcome in VERDICT_PATTERN.findall(line)):
                success_seen = True
    lines = [line for line in raw if '"toolCall"' in line or '"model_change"' in line]
    for line in lines:
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        stamp = parse_timestamp(entry.get("timestamp"))
        if stamp is not None and stamp < cutoff:
            continue
        if window is not None and stamp is not None and not (window[0] <= stamp <= window[1]):
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
            if measured and not is_lane:
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
            # tier-split accounting
            if is_lane:
                lane_calls += 1
                if name in EXECUTION_TOOLS:
                    lane_execution += 1
            else:
                owner_all_calls += 1
                if name == "hub" and '"op": "wait"' in arguments:
                    hub_waits += 1
                if name in ("hub", "todo", "task"):
                    continue
                owner_calls += 1
                if name in EXECUTION_TOOLS and is_subscription_model(model):
                    owner_execution += 1
                if (
                    name == "bash"
                    and is_subscription_model(model)
                    and PROD_COMMAND_PATTERN.search(arguments)
                    and any(host in arguments or IP_PATTERN.search(arguments) for host in prod_hosts)
                ):
                    prod_calls.append(
                        {"at": entry.get("timestamp", ""), "tool": name, "args": arguments[:220]}
                    )
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
        "ownerExecutionCalls": owner_execution,
        "ownerCalls": owner_calls,
        "laneExecutionCalls": lane_execution,
        "laneCalls": lane_calls,
        "prodCalls": prod_calls,
        "verdicts": verdicts,
        "stops": stops,
        "hubWaits": hub_waits,
        "ownerAllCalls": owner_all_calls,
        "failureSignatures": failure_signatures,
        "successSeen": success_seen,
    }


def build_report(
    root: Path,
    folder: str | None,
    days: int,
    catalog_path: Path,
    prod_hosts: tuple[str, ...] = DEFAULT_PROD_HOSTS,
    task: str | None = None,
) -> dict:
    catalog = read_yaml(catalog_path)
    agents, generics = tier_map(catalog)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    files = session_files(root, folder)
    if task:
        files = select_task_group(files, task)
    scanned = [
        scan_session(path, owner, cutoff, agents, generics, prod_hosts, task) for path, owner in files
    ]
    sessions = [session for session in scanned if session is not None]
    dispatches: dict[str, int] = {}
    tier_totals: dict[str, int] = {}
    turns: dict[str, int] = {}
    tool_calls = execution_calls = ui_main = promotions = 0
    owner_exec = owner_calls = lane_exec = lane_calls = 0
    context_samples: list[int] = []
    prod_calls: list[dict] = []
    verdicts: list[tuple[str, str, str]] = []
    stops = 0
    hub_waits = 0
    owner_all = 0
    failure_signatures: dict[str, int] = {}
    success_seen = False
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
        owner_exec += session["ownerExecutionCalls"]
        owner_calls += session["ownerCalls"]
        lane_exec += session["laneExecutionCalls"]
        lane_calls += session["laneCalls"]
        prod_calls.extend(session["prodCalls"])
        verdicts.extend(session["verdicts"])
        stops += session["stops"]
        hub_waits += session["hubWaits"]
        owner_all += session.get("ownerAllCalls", 0)
        for signature, count in (session.get("failureSignatures") or {}).items():
            failure_signatures[signature] = failure_signatures.get(signature, 0) + count
        success_seen = success_seen or bool(session.get("successSeen"))
    planning_split = {
        "analysisDispatches": sum(count for key, count in dispatches.items() if key.startswith("team-os-planner:")),
        "adjudicationDispatches": sum(count for key, count in dispatches.items() if key.startswith("team-os-planner-alt:")),
    }
    total_planning = planning_split["analysisDispatches"] + planning_split["adjudicationDispatches"]
    planning_split["shareToAdjudication"] = (
        round(planning_split["adjudicationDispatches"] / total_planning, 3) if total_planning else None
    )
    owner_share = round(owner_exec / owner_calls, 3) if owner_calls else None
    thinning = round(owner_exec / (owner_exec + lane_exec), 3) if (owner_exec + lane_exec) else None
    context_median = sorted(context_samples)[len(context_samples) // 2] if context_samples else None
    return {
        "sessionsRoot": str(root),
        "folderFilter": folder,
        "taskFilter": task,
        "windowDays": days,
        "catalog": str(catalog_path),
        "sessionCount": len(sessions),
        "sessions": [
            {
                "file": session["file"],
                "laneCalls": session["laneCalls"],
                "verdicts": session["verdicts"],
            }
            for session in sessions
        ],
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
            "contextMedian": context_median,
            "contextSamples": len(context_samples),
        },
        "tierSplit": {
            "ownerCalls": owner_calls,
            "ownerExecutionCalls": owner_exec,
            "ownerExecutionShare": owner_share,
            "laneCalls": lane_calls,
            "laneExecutionCalls": lane_exec,
            "laneExecutionShare": round(lane_exec / lane_calls, 3) if lane_calls else None,
            "executionDelegatedShare": thinning,
        },
        "prodCallsOnSubscriptionTier": prod_calls,
        "workerVerdicts": [
            {"acceptancePoint": point, "outcome": outcome} for point, outcome, _ in verdicts
        ],
        "stopMarkers": stops,
        "ownerHubWaits": hub_waits,
        "ownerAllCalls": owner_all,
        "repeatedFailures": dict(
            sorted(failure_signatures.items(), key=lambda item: -item[1])[:6]
        ),
        "workerSuccessMarkerSeen": success_seen,
        "targets": {
            "planningHalfToAdjudication": (
                planning_split["shareToAdjudication"] is None or planning_split["shareToAdjudication"] >= 0.5
            ),
            "visionTierUsed": any(key.startswith("team-os-ui-designer:") for key in dispatches),
            "judgementTierUsed": any(key.startswith("team-os-deep-reviewer:") for key in dispatches),
            "mainExecutionShareBelow30Percent": (execution_calls / tool_calls) < 0.30 if tool_calls else None,
            "mainContextMedianBelow200k": context_median is not None and context_median < 200_000,
        },
    }


def injections_for(advisory: list[dict], policy: dict) -> dict[str, str]:
    """Map each fired advisory to the clause the next dispatch must carry.

    An advisory with no clause cannot change the next run; the catalog decides
    which ones are allowed to exist.
    """
    declared = policy.get("advisoryInjections") or {}
    return {code: str(clause) for code, clause in declared.items()}


def gate_report(
    report: dict,
    ui_call_threshold: int = 10,
    budget: int | None = None,
    policy: dict | None = None,
    receipts_passed: bool | None = None,
) -> dict:
    """Turn a report into a pass/fail compliance gate.

    Blocking violations must be fixed before a task closes:
      - production-remote commands from the subscription-tier main session;
      - UI-touching calls on the main tier without any vision-tier dispatch
        (beyond a small tolerance).
    Advisory violations are reported without blocking: owner execution share,
    context median, planning split, 1M promotions.
    """
    policy = policy or {"advisoryInjections": {}}
    if budget is None:
        budget = FAILURE_BUDGET_FALLBACK
    blocking: list[dict] = []
    advisory: list[dict] = []
    if report.get("taskFilter") and report.get("sessionCount", 0) == 0:
        advisory.append(
            {
                "code": "no-sessions-for-task",
                "detail": f"no session transcript in the window mentions task {report['taskFilter']}; "
                "the gate could not verify this task, treat the routing evidence as a gap",
            }
        )
    prod_calls = report.get("prodCallsOnSubscriptionTier") or []
    if prod_calls:
        blocking.append(
            {
                "code": "prod-command-on-subscription-tier",
                "count": len(prod_calls),
                "detail": "ssh/scp/docker/kubectl/helm/rsync to a production host from the "
                "subscription-tier main session; route through prod-env executors or execution-tier workers",
                "samples": prod_calls[:5],
            }
        )
    ui_main = report["mainSession"]["uiCallsOnMainTier"]
    vision = report["visionTierDispatches"]
    if ui_main > ui_call_threshold and vision == 0:
        blocking.append(
            {
                "code": "ui-work-without-vision-tier",
                "count": ui_main,
                "detail": f"{ui_main} UI-touching calls on the main tier with zero vision-tier dispatches",
            }
        )
    # stop-loss: the same acceptance point failing round after round means the
    # loop must stop and the owner must replan, not try the next hypothesis.
    failures: dict[str, int] = {}
    passed: set[str] = set()
    for item in report.get("workerVerdicts") or []:
        point = str(item.get("acceptancePoint"))
        if item.get("outcome") == "PASS":
            passed.add(point)
        else:
            failures[point] = failures.get(point, 0) + 1
    exceeded = {
        point: count for point, count in failures.items() if count >= budget and point not in passed
    }
    if exceeded:
        detail = ", ".join(f"{point}×{count}" for point, count in sorted(exceeded.items()))
        blocking.append(
            {
                "code": "failure-budget-exceeded",
                "count": sum(exceeded.values()),
                "detail": f"acceptance points failed at least {budget} rounds without a later PASS "
                f"({detail}); stop the workers, record STOP, and take the decision back to planning",
            }
        )
    # Evidence order: deterministic gate receipts outrank text-level signals.
    # When every declared gate passed, repeated failure text in the transcript
    # (test output, quoted logs) is history, not an open loop.
    repeated = report.get("repeatedFailures") or {}
    worst = {key: count for key, count in repeated.items() if count >= budget}
    if worst and not report.get("workerSuccessMarkerSeen"):
        detail = ", ".join(f"{key}×{count}" for key, count in sorted(worst.items(), key=lambda i: -i[1])[:3])
        entry = {
            "code": "failure-budget-exceeded",
            "count": sum(worst.values()),
            "detail": f"the same failure repeated at least {budget} times with no success marker "
            f"({detail}); stop the workers, record STOP, and take the decision back to planning",
        }
        if receipts_passed is True:
            entry["detail"] += (
                " — suppressed to advisory because every declared gate has a passing receipt"
            )
            advisory.append(entry)
        else:
            blocking.append(entry)
    if report.get("stopMarkers"):
        advisory.append(
            {
                "code": "stop-marker-recorded",
                "detail": f"{report['stopMarkers']} STOP marker(s) present: a replan/acceptance decision "
                "must exist before any retry",
            }
        )
    owner_all = report.get("ownerAllCalls") or report["tierSplit"]["ownerCalls"]
    waits = report.get("ownerHubWaits") or 0
    if owner_all and waits / owner_all >= 0.35:
        advisory.append(
            {
                "code": "owner-wait-share-high",
                "detail": f"{waits}/{owner_all} owner calls are hub waits: replace polling with a "
                "cadence contract, and use the wait to advance planning or evidence",
            }
        )
    for session in report.get("sessions") or []:
        if session.get("laneCalls", 0) >= 200 and not (session.get("verdicts") or []):
            advisory.append(
                {
                    "code": "worker-cadence-missing",
                    "detail": f"{session.get('file')}: {session['laneCalls']} calls with no "
                    "VERDICT marker; long workers must report structured beats",
                }
            )
    split = report["planningSplit"]["shareToAdjudication"]
    if split is not None and split < 0.5:
        advisory.append(
            {
                "code": "planning-not-half-to-adjudication",
                "detail": f"shareToAdjudication={split} below 0.5; draft planning goes to @plan_alt",
            }
        )
    owner_share = report["tierSplit"]["ownerExecutionShare"]
    if owner_share is not None and owner_share > 0.30:
        advisory.append(
            {
                "code": "owner-execution-share-high",
                "detail": f"ownerExecutionShare={owner_share} above 0.30; batch reads and commands go to the execution tier",
            }
        )
    median = report["mainSession"]["contextMedian"]
    if median is not None and median >= 200_000:
        advisory.append(
            {
                "code": "context-median-high",
                "detail": f"contextMedian={median} at or above 200k; default to k3-256k and thin the main session",
            }
        )
    if report["mainSession"]["promotionsTo1M"]:
        advisory.append(
            {
                "code": "promotion-to-1m",
                "detail": f"{report['mainSession']['promotionsTo1M']} context promotion(s) to the 1M variant",
            }
        )
    injections = injections_for(advisory, policy)
    for item in advisory:
        clause = injections.get(str(item.get("code")))
        if clause:
            item["injection"] = clause
    return {
        "pass": not blocking,
        "blocking": blocking,
        "advisory": advisory,
        "injections": list(
            {
                str(item.get("code")): {"code": str(item.get("code")), "clause": clause}
                for item in advisory
                for clause in [injections.get(str(item.get("code")))]
                if clause
            }.values()
        ),
        "metrics": {
            "ownerExecutionShare": report["tierSplit"]["ownerExecutionShare"],
            "contextMedian": report["mainSession"]["contextMedian"],
            "planningShareToAdjudication": report["planningSplit"]["shareToAdjudication"],
            "visionTierDispatches": report["visionTierDispatches"],
            "judgementTierDispatches": report["judgementTierDispatches"],
            "executionDelegatedShare": report["tierSplit"]["executionDelegatedShare"],
        },
    }


def write_carry_forward(project_root: Path, task: str | None, result: dict) -> Path | None:
    """Persist the injections so the next dispatch packs carry them.

    This is the loop that turns a verdict into a change: close-time advisories
    become execution constraints in the following round's packs, and disappear
    automatically when they stop firing.
    """
    injections = result.get("injections") or []
    target = project_root / ".work" / "dispatch" / "carry-forward.json"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "generatedAt": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "task": task,
            "injections": injections,
        }
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        return None
    return target


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default="team-os", help="OMP profile name")
    parser.add_argument("--sessions-root", type=Path, help="override the sessions directory")
    parser.add_argument("--folder", help="only count sessions whose folder name contains this text")
    parser.add_argument("--task", help="only count sessions whose transcript mentions this task id")
    parser.add_argument("--days", type=int, default=1, help="window in days")
    parser.add_argument("--catalog", type=Path, default=CATALOG, help="model catalog path")
    parser.add_argument("--gate", action="store_true", help="emit a pass/fail compliance gate instead of raw metrics")
    parser.add_argument("--ui-call-threshold", type=int, default=10, help="main-tier UI calls tolerated without a vision dispatch")
    parser.add_argument("--prod-hosts", nargs="*", default=list(DEFAULT_PROD_HOSTS), help="production hosts to flag")
    parser.add_argument("--failure-budget", type=int, default=None, help="rounds an acceptance point may fail before the loop must stop (default: catalog dispatchPolicy.failureBudget)")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="project root receiving .work/dispatch/carry-forward.json")
    parser.add_argument("--receipts-passed", action="store_true", help="the task's declared gates all have passing receipts (deterministic layer done)")
    parser.add_argument("--receipts-missing", action="store_true", help="the task's declared gates lack passing receipts")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.sessions_root or DEFAULT_PROFILE_ROOT / args.profile / "agent" / "sessions"
    try:
        report = build_report(root, args.folder, args.days, args.catalog, tuple(args.prod_hosts), args.task)
    except RoutingError as error:
        print(f"check-role-routing: {error}", file=sys.stderr)
        return 2
    if args.gate:
        try:
            policy = dispatch_policy(read_yaml(args.catalog))
        except RoutingError:
            policy = {"failureBudget": FAILURE_BUDGET_FALLBACK, "advisoryInjections": {}}
        budget = args.failure_budget if args.failure_budget is not None else policy["failureBudget"]
        receipts_passed: bool | None = None
        if args.receipts_passed:
            receipts_passed = True
        elif args.receipts_missing:
            receipts_passed = False
        result = gate_report(report, args.ui_call_threshold, budget, policy, receipts_passed)
        written = write_carry_forward(args.project_root, report.get("taskFilter"), result)
        if written is not None:
            result["carryForward"] = str(written)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result["pass"] else 1
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

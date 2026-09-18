#!/usr/bin/env python3
"""Session facts as one command instead of a hand-written script each time.

Every review in this repo previously re-derived the same numbers with ad-hoc
heredocs (per-session turns and tokens, tool histograms, hub op mix, idle gaps,
dispatch lists). Deterministic transformations belong in a code node: same
input, one correct answer, no model in the loop.

Usage:

  python3 scripts/session_facts.py --session <file-or-dir> [--since HH:MM] [--until HH:MM]
  python3 scripts/session_facts.py --profile team-os --folder jusuan-installer --days 1 \
      [--task <task-id>] [--json]

`--task` scopes the window to the spans that mention the task id, matching the
attribution rule used by check_role_routing.py.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEFAULT_PROFILE_ROOT = Path("~/.omp/profiles").expanduser()
EXECUTION_TOOLS = ("bash", "read", "grep", "glob", "edit", "write")
# Same precision rule as the gate: pack-template placeholders and contract
# narration are not emitted markers.
MARKERS = ("VERDICT:", "STOP:")
CONTRACT_NARRATION = ("回传", "失败预算", "写集合", "包内")
PLACEHOLDER = re.compile(r"(VERDICT|STOP):\s*<")
LOCAL_TZ = datetime.now().astimezone().tzinfo


class FactError(ValueError):
    pass


def parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def session_files(root: Path, folder: str | None) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.is_dir():
        return []
    files = sorted(root.glob("*/[0-9]*.jsonl"))
    if folder:
        files = [path for path in files if folder in path.parent.name]
    for top in sorted(root.glob("*/[0-9]*")):
        if not top.is_dir() or (folder and folder not in top.parent.name):
            continue
        files.extend(sorted(child for child in top.glob("*.jsonl") if not child.name[0].isdigit()))
    return files


def task_window(path: Path, task: str) -> tuple[datetime, datetime] | None:
    stamps: list[datetime] = []
    with path.open(errors="replace") as handle:
        for line in handle:
            if task not in line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            stamp = parse_timestamp(entry.get("timestamp"))
            if stamp is not None:
                stamps.append(stamp)
    if not stamps:
        return None
    return min(stamps), max(stamps)


def scan(path: Path, window: tuple[datetime, datetime] | None) -> dict:
    turns: collections.Counter[str] = collections.Counter()
    input_tokens: collections.Counter[str] = collections.Counter()
    cache_tokens: collections.Counter[str] = collections.Counter()
    output_tokens: collections.Counter[str] = collections.Counter()
    tools: collections.Counter[str] = collections.Counter()
    hub_ops: collections.Counter[str] = collections.Counter()
    dispatches: collections.Counter[str] = collections.Counter()
    markers: collections.Counter[str] = collections.Counter()
    stamps: list[datetime] = []
    current: str | None = None
    with path.open(errors="replace") as handle:
        for line in handle:
            if any(marker in line for marker in MARKERS) and not any(
                word in line for word in CONTRACT_NARRATION
            ):
                scrubbed = PLACEHOLDER.sub("", line)
                for marker in MARKERS:
                    markers[marker] += scrubbed.count(marker)
            if '"toolCall"' not in line and '"model_change"' not in line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            stamp = parse_timestamp(entry.get("timestamp"))
            if window is not None and stamp is not None and not (window[0] <= stamp <= window[1]):
                continue
            if entry.get("type") == "model_change":
                current = str(entry.get("model") or "")
                continue
            message = entry.get("message") or {}
            if message.get("role") != "assistant":
                continue
            if stamp is not None:
                stamps.append(stamp)
            model = str(current or "?")
            turns[model] += 1
            usage = message.get("usage") or {}
            if isinstance(usage, dict):
                input_tokens[model] += usage.get("input") or 0
                cache_tokens[model] += usage.get("cacheRead") or 0
                output_tokens[model] += usage.get("output") or 0
            for block in message.get("content") or []:
                if not isinstance(block, dict) or block.get("type") != "toolCall":
                    continue
                name = str(block.get("name") or "")
                tools[name] += 1
                arguments = block.get("arguments") or {}
                if name == "hub":
                    hub_ops[str(arguments.get("op"))] += 1
                if name in ("task", "eval"):
                    for item in arguments.get("tasks") or []:
                        dispatches[str(item.get("agent") or "task")] += 1
    stamps.sort()
    gaps = [
        (round((later - earlier).total_seconds() / 60, 1), earlier.astimezone(LOCAL_TZ), later.astimezone(LOCAL_TZ))
        for earlier, later in zip(stamps, stamps[1:])
        if (later - earlier).total_seconds() > 180
    ]
    return {
        "session": path.name,
        "turns": dict(turns),
        "inputTokens": dict(input_tokens),
        "cacheReadTokens": dict(cache_tokens),
        "outputTokens": dict(output_tokens),
        "tools": dict(tools.most_common()),
        "hubOps": dict(hub_ops),
        "dispatches": dict(dispatches.most_common()),
        "markers": dict(markers),
        "first": stamps[0].astimezone(LOCAL_TZ).strftime("%m-%d %H:%M") if stamps else None,
        "last": stamps[-1].astimezone(LOCAL_TZ).strftime("%m-%d %H:%M") if stamps else None,
        "idleGaps": [
            {"minutes": minutes, "from": start.strftime("%H:%M"), "to": end.strftime("%H:%M")}
            for minutes, start, end in sorted(gaps, reverse=True)[:5]
        ],
        "executionCalls": sum(count for name, count in tools.items() if name in EXECUTION_TOOLS),
        "toolCalls": sum(tools.values()),
    }


def render(report: dict) -> str:
    lines = []
    for session in report["sessions"]:
        lines.append(f"## {session['session']}  {session['first']} → {session['last']}")
        lines.append(
            f"  调用 {session['toolCalls']}（执行类 {session['executionCalls']}）；工具 "
            + ", ".join(f"{name}×{count}" for name, count in list(session["tools"].items())[:8])
        )
        if session["hubOps"]:
            lines.append("  hub: " + ", ".join(f"{op}×{count}" for op, count in session["hubOps"].items()))
        if session["dispatches"]:
            lines.append("  派工: " + ", ".join(f"{agent}×{count}" for agent, count in session["dispatches"].items()))
        tokens = sum(session["inputTokens"].values()) + sum(session["cacheReadTokens"].values())
        lines.append(f"  token(input+cacheRead) {tokens:,}；轮次 " + ", ".join(
            f"{model.split('/')[-1]}×{count}" for model, count in session["turns"].items()))
        if session["markers"]:
            lines.append("  标记: " + ", ".join(f"{k}×{v}" for k, v in session["markers"].items()))
        if session["idleGaps"]:
            lines.append("  最长空档: " + ", ".join(
                f"{gap['minutes']}min({gap['from']}→{gap['to']})" for gap in session["idleGaps"][:3]))
    totals = {
        "sessions": len(report["sessions"]),
        "toolCalls": sum(item["toolCalls"] for item in report["sessions"]),
        "executionCalls": sum(item["executionCalls"] for item in report["sessions"]),
    }
    lines.append("")
    lines.append(
        f"合计：{totals['sessions']} 会话，{totals['toolCalls']} 次调用，执行类 {totals['executionCalls']}"
    )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, help="session jsonl file or directory")
    parser.add_argument("--profile", default="team-os", help="OMP profile name")
    parser.add_argument("--sessions-root", type=Path, help="override the sessions directory")
    parser.add_argument("--folder", help="only sessions whose folder name contains this text")
    parser.add_argument("--days", type=int, default=1, help="window in days (ignored with --task)")
    parser.add_argument("--task", help="scope to the spans mentioning this task id")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of a text summary")
    args = parser.parse_args(argv)

    root = args.session or args.sessions_root or DEFAULT_PROFILE_ROOT / args.profile / "agent" / "sessions"
    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    files = session_files(root, args.folder)
    if not files:
        print(f"session-facts: no sessions under {root}", file=sys.stderr)
        return 2
    sessions = []
    for path in files:
        window = task_window(path, args.task) if args.task else None
        if args.task and window is None:
            continue
        if window is None:
            window = (cutoff, datetime.now(timezone.utc))
        facts = scan(path, window)
        if facts["toolCalls"]:
            sessions.append(facts)
    report = {"root": str(root), "folder": args.folder, "task": args.task, "sessions": sessions}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

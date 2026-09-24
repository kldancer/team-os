#!/usr/bin/env python3
"""Bind Codex to an existing project plan; never execute deployment stages.

Only `plan` invokes the project's known local planner. `bind` writes a runtime
receipt, `inspect` checks it without replaying anything. Identity is reported by
the caller, not attested by this helper. No shell, daemon, model call or OMP import.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}\Z")
MODELS = ("gpt-6-astra", "gpt-6-sol")


def safe_id(value: str) -> str:
    if not ID.fullmatch(value):
        raise ValueError("task and owner must be simple identifiers (1-64 characters)")
    return value


def rooted(root: Path, relative: str) -> Path:
    path = root / relative
    if not path.resolve().is_relative_to(root):
        raise ValueError(f"path escapes project: {relative}")
    return path


def load_plan(root: Path, task: str) -> tuple[dict, str, Path]:
    path = rooted(root, f".work/tasks/{safe_id(task)}/plan.json")
    raw = path.read_bytes()
    plan = json.loads(raw)
    if not isinstance(plan, dict) or plan.get("taskId") != task:
        raise ValueError("project plan taskId mismatch")
    if plan.get("controller") != "juspctl":
        raise ValueError("unsupported controller; use the project's native contract")
    contract = plan.get("outcomeContract")
    if not isinstance(contract, dict) or not contract.get("outcome") or not contract.get("acceptance"):
        raise ValueError("project plan lacks outcome/acceptance")
    safe_id(plan.get("resultOwner", ""))
    return plan, hashlib.sha256(raw).hexdigest(), path


def receipt_path(root: Path, task: str, digest: str) -> Path:
    return rooted(root, f".work/tasks/{task}/runtime/codex/{digest}.json")


def write_receipt(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # An immutable per-plan receipt avoids overwriting another owner/model's
    # binding. Write then link atomically so concurrent binders cannot replace it.
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode()
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=".binding-")
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
        try:
            os.link(temporary, path)
        except FileExistsError:
            if path.read_bytes() != data:
                raise ValueError("binding already exists with different identity; keep original receipt")
    finally:
        os.unlink(temporary)


def bind(root: Path, task: str, owner: str, model: str | None,
         checkout: Path, effort: str | None = None, version: str | None = None) -> dict:
    plan, digest, path = load_plan(root, task)
    if safe_id(owner) != plan["resultOwner"]:
        raise ValueError("owner differs from project plan; hand off in project workflow first")
    if model is not None and model not in MODELS:
        raise ValueError("model outside this adapter's evaluated family")
    if model == "gpt-6-astra" and effort == "none":
        raise ValueError("Astra does not support none reasoning")
    checkout = checkout.resolve(strict=True)
    if not checkout.is_dir():
        raise ValueError("checkout must be a directory")
    payload = {
        "version": 1, "harness": "codex", "harnessVersion": version,
        "projectRoot": str(root), "checkoutRoot": str(checkout),
        "taskId": task, "owner": owner, "plan": str(path), "planSha256": digest,
        "reportedModel": model, "reportedEffort": effort,
        "identitySource": "caller-reported" if model else "unavailable",
        "authorization": "project-contract-and-user-session-only",
    }
    write_receipt(receipt_path(root, task, digest), payload)
    return payload


def inspect(root: Path, task: str, checkout: Path | None = None) -> dict:
    plan, digest, path = load_plan(root, task)
    binding_path = receipt_path(root, task, digest)
    binding = json.loads(binding_path.read_text()) if binding_path.is_file() else None
    if binding is not None:
        expected = {"version": 1, "harness": "codex", "projectRoot": str(root),
                    "taskId": task, "owner": plan["resultOwner"], "plan": str(path),
                    "planSha256": digest}
        if not isinstance(binding, dict) or any(binding.get(k) != v for k, v in expected.items()):
            raise ValueError("invalid runtime binding")
        if checkout is not None and binding.get("checkoutRoot") != str(checkout.resolve()):
            raise ValueError("checkout differs from runtime binding")
    return {
        "taskId": task, "owner": plan["resultOwner"], "planSha256": digest,
        "binding": "current" if binding else "missing-or-plan-changed",
        "runtime": binding,
        "requiresFreeze": plan.get("requiresFreeze"),
        "remoteRequired": plan.get("remoteRequired"),
        "projectState": "query-project-runner; binding-is-not-task-status",
        "nextReadOnlyArgv": [[str(root / "juspctl"), action, "--task", task]
                             for action in ("status", "resume")],
        "execution": "use-project-entry-after-current-user-authorization-and-project-checks",
    }


def plan_command(args: argparse.Namespace, root: Path) -> list[str]:
    runner = rooted(root, ".agents/scripts/juspctl.py")
    if not runner.is_file():
        raise ValueError("juspctl is unavailable; use project-native planning, do not invent an engine")
    command = [sys.executable, str(runner), "plan", "--task", safe_id(args.task),
               "--result-owner", safe_id(args.owner), "--changed-from", "explicit",
               "--lane", args.lane, "--target", args.target, "--outcome", args.outcome]
    for flag, values in (("--acceptance", args.acceptance), ("--changed", args.changed),
                         ("--non-goal", args.non_goal)):
        for value in values:
            command.extend([flag, value])
    if args.plan_doc:
        command.extend(["--plan-doc", str(args.plan_doc.resolve())])
    if args.freeze:
        command.append("--freeze")
    if args.browser_required:
        command.append("--browser-required")
    return command


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name in ("plan", "bind", "inspect"):
        p = sub.add_parser(name)
        p.add_argument("--project-root", type=Path, required=True)
        p.add_argument("--task", required=True)
        if name in ("plan", "bind"):
            p.add_argument("--owner", required=True)
            p.add_argument("--model", choices=MODELS)
            p.add_argument("--effort", choices=("none", "low", "medium", "high", "xhigh", "max", "ultra"))
            p.add_argument("--harness-version")
            p.add_argument("--checkout-root", type=Path, required=True)
        else:
            p.add_argument("--checkout-root", type=Path)
            p.add_argument("--require-binding", action="store_true")
        if name == "plan":
            p.add_argument("--outcome", required=True)
            p.add_argument("--acceptance", action="append", required=True)
            p.add_argument("--changed", action="append", required=True)
            p.add_argument("--non-goal", action="append", default=[])
            p.add_argument("--lane", required=True)
            p.add_argument("--target", required=True)
            p.add_argument("--plan-doc", type=Path)
            p.add_argument("--freeze", action="store_true")
            p.add_argument("--browser-required", action="store_true")
            p.add_argument("--execute", action="store_true", help="run local planner; otherwise preview argv")
    args = parser.parse_args(argv)
    try:
        root = args.project_root.expanduser().resolve(strict=True)
        safe_id(args.task)
        if args.action == "inspect":
            payload = inspect(root, args.task, args.checkout_root)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 2 if args.require_binding and payload["binding"] != "current" else 0
        if args.model == "gpt-6-astra" and args.effort == "none":
            raise ValueError("Astra does not support none reasoning")
        if args.action == "plan":
            command = plan_command(args, root)
            print(json.dumps({"argv": command, "cwd": str(root), "timeoutSeconds": 60}, ensure_ascii=False), flush=True)
            if not args.execute:
                return 0
            existing = rooted(root, f".work/tasks/{args.task}/plan.json")
            if existing.exists():
                raise ValueError("task already has a plan; inspect/resume or revise through project-native planner")
            # This local helper may only plan in its own checkout; multi-workspace
            # integration plans must be prepared through the project native path.
            if args.checkout_root.resolve(strict=True) != root:
                raise ValueError("plan checkout must equal project root; use bind for explicit cross-workspace plans")
            result = subprocess.run(command, cwd=root, timeout=60, check=False)
            if result.returncode:
                return result.returncode
        payload = bind(root, args.task, args.owner, args.model, args.checkout_root,
                       args.effort, args.harness_version)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        print(f"codex-bridge: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

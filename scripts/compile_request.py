#!/usr/bin/env python3
"""Compile a short natural-language request into a minimal Team OS contract.

The compiler is deliberately conservative: it classifies intent and supplies
workflow defaults, but it never grants remote, production, destructive, or
credential authority. The owner still reads the project contract and confirms
any decision that cannot be inferred safely.

Examples:
  python3 compile_request.py --request "修复 Console 登录后概览页空白" --json
  python3 compile_request.py --request "只分析上传失败原因" --mode diagnose
  python3 compile_request.py --request "按结论推进模型页面筛选改造" --out .work/request-compile.json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


MODES = ("auto", "diagnose", "design", "implement", "verify", "resume")

UI_RE = re.compile(
    r"ui|前端|页面|登录页|界面|视觉|截图|组件|样式|主题|交互|console|浏览器|playwright|figma|响应式",
    re.IGNORECASE,
)
BROWSER_RE = re.compile(
    r"浏览器|真实入口|playwright|console|network|devtools|截图|视觉|页面验收|登录态|登录页|登录入口",
    re.IGNORECASE,
)
REMOTE_RE = re.compile(
    r"生产|线上|远端|部署|发布|rollout|deploy|refresh|推送|push|harbor|kubernetes|集群",
    re.IGNORECASE,
)
DESTRUCTIVE_RE = re.compile(
    r"删除|清理|销毁|覆盖|迁移|重置|drop\b|delete\b|destroy\b|wipe\b",
    re.IGNORECASE,
)
CREDENTIAL_RE = re.compile(
    r"密码|口令|token|密钥|凭据|cookie|登录账号|authorization|secret",
    re.IGNORECASE,
)
SECRET_VALUE_RE = re.compile(
    r"(?i)(?:token|password|passwd|secret|cookie|authorization|api[_-]?key)\s*[:=]\s*[^\s,;]+"
    r"|Bearer\s+[^\s,;]+"
)
DIAGNOSE_RE = re.compile(r"只分析|仅分析|排查|诊断|为什么|原因|定位原因|调查", re.IGNORECASE)
DESIGN_RE = re.compile(r"设计|规划|方案|架构|比较方案|评审方案", re.IGNORECASE)
VERIFY_RE = re.compile(r"只验证|仅验证|验收|回归|冒烟|healthcheck|guard|smoke", re.IGNORECASE)
RESUME_RE = re.compile(r"继续|恢复|上次|原任务|原 outcome|原结果", re.IGNORECASE)
IMPLEMENT_RE = re.compile(
    r"按结论|开始推进|实现|修复|整改|改造|更新|补强|开发|落地|完成|改成|调整|优化|增加|补充|替换",
    re.IGNORECASE,
)


def _signal(pattern: re.Pattern[str], text: str) -> bool:
    return bool(pattern.search(text))


def redact_text(text: str) -> str:
    """Remove obvious inline credential values before printing or persisting."""
    return SECRET_VALUE_RE.sub("<redacted>", text)


def classify_mode(request: str, explicit: str = "auto") -> tuple[str, str]:
    """Return (mode, reason), with explicit mode taking precedence."""
    if explicit != "auto":
        return explicit, "explicit"
    # Specific phrases must win over broad implementation words such as
    # "定位并修复" or "继续修复".
    if _signal(RESUME_RE, request):
        return "resume", "resume-signal"
    if _signal(DIAGNOSE_RE, request) and not re.search(
        r"(?:定位|分析|排查)(?:后|并)(?:修复|整改)", request, re.I
    ):
        return "diagnose", "diagnostic-signal"
    if _signal(DESIGN_RE, request) and not _signal(IMPLEMENT_RE, request):
        return "design", "design-signal"
    if _signal(VERIFY_RE, request) and not _signal(IMPLEMENT_RE, request):
        return "verify", "verification-signal"
    if _signal(IMPLEMENT_RE, request):
        return "implement", "implementation-signal"
    return "auto", "owner-classifies-after-reading-project-facts"


def _flow_owner(mode: str) -> str:
    return {
        "diagnose": "diagnose",
        "design": "design",
        "implement": "deliver-change",
        "verify": "guard",
        "resume": "resume-current-owner",
        "auto": "owner-classifies",
    }[mode]


def _authority(project_root: Path) -> list[str]:
    candidates = [
        (project_root / "AGENTS.md", "project AGENTS.md"),
        (project_root / ".agents" / "config" / "gates.json", ".agents/config/gates.json"),
        (project_root / "docs", "project docs/formal design"),
        (project_root / ".work", "project .work recovery state"),
    ]
    return [label for path, label in candidates if path.exists()]


def compile_request(request: str, *, mode: str = "auto", project_root: str | Path = ".") -> dict[str, Any]:
    """Build a deterministic draft contract from a short request.

    This function intentionally does not inspect source files or infer write
    paths. Those are owner responsibilities after the project authority is
    loaded; keeping that boundary prevents the helper from becoming a broad
    scanner or an authorization oracle.
    """
    normalized = " ".join(request.strip().split())
    if not normalized:
        raise ValueError("request must not be empty")
    if mode not in MODES:
        raise ValueError(f"unsupported mode: {mode}")

    root = Path(project_root).expanduser().resolve()
    resolved_mode, reason = classify_mode(normalized, mode)
    ui = _signal(UI_RE, normalized)
    browser = _signal(BROWSER_RE, normalized)
    remote = _signal(REMOTE_RE, normalized)
    destructive = _signal(DESTRUCTIVE_RE, normalized)
    credentials = _signal(CREDENTIAL_RE, normalized)
    confirmation_required = remote or destructive or credentials
    safe_request = redact_text(normalized)

    acceptance = [
        "满足项目定义的用户可验证结果",
        "只运行机器计划判定适用的 Gate/healthcheck/smoke",
        "记录 PASS|FAIL|SKIP、未验项和授权外边界",
    ]
    if browser:
        acceptance.append("若计划声明浏览器需求，补齐真实入口证据并写入项目 .work")

    role_hints = ["@plan_owner"]
    if ui:
        role_hints.append("按需 @ui_deep / @ui_impl / @ui_qa，不默认串行启用")
    if resolved_mode == "diagnose":
        role_hints.append("需要独有事实时才启用 @fast_worker")

    questions: list[str] = []
    if remote:
        questions.append("远端/生产动作需要用户明确授权和目标入口")
    if destructive:
        questions.append("删除、清理、迁移或覆盖需要确认精确对象、回退和授权")
    if credentials:
        questions.append("凭据或登录态只按项目安全合同使用，不从自然语言推断授权")

    return {
        "version": 1,
        "input": {"request": safe_request, "mode": mode},
        "intent": {"mode": resolved_mode, "reason": reason, "flowOwner": _flow_owner(resolved_mode)},
        "signals": {
            "ui": ui,
            "browser": browser,
            "remote": remote,
            "destructive": destructive,
            "credentials": credentials,
        },
        "defaults": {
            "ownerRole": "@plan_owner",
            "topology": "solo",
            "nonGoals": [
                "不扩大为无关的全量扫描、构建、部署或生产写",
                "不为 Gate、重试或专家输入建立新的顶层结果",
                "不创建没有独有证据收益的 worker",
            ],
            "authority": _authority(root) or ["项目 AGENTS.md、正式设计、机器计划和命中 Skill"],
            "scopePolicy": "由 owner 根据项目事实确定最小读写集合；用户不需要预填路径表",
            "acceptance": acceptance,
            "stopConditions": [
                "需要产品决策、权限或高风险授权时暂停并询问",
                "失败预算耗尽、根因越过写集合或证据与合同矛盾时回 owner 重新定界",
            ],
        },
        "routing": {
            "roles": role_hints,
            "browser": "select-by-evidence" if browser else "project-gates-only",
            "collaboration": "solo-unless-independent-evidence-or-mutual-exclusive-write-set",
        },
        "confirmation": {
            "required": confirmation_required,
            "reasons": questions,
        },
        "ownerInstruction": (
            f"按当前项目规范处理：{safe_request}。先读取会改变执行路径的项目事实，"
            "自动生成最小结果合同并选择最小拓扑；只有需要产品决策、高风险授权或"
            "真实入口条件不成立时才停下询问。完成后返回实际变更、验证证据、未验项和风险。"
        ),
    }


def _render_summary(payload: dict[str, Any]) -> str:
    intent = payload["intent"]
    signals = payload["signals"]
    confirmation = payload["confirmation"]
    lines = [
        f"intent: {intent['mode']} ({intent['reason']})",
        f"flow owner: {intent['flowOwner']}",
        f"topology: {payload['defaults']['topology']}",
        f"browser route: {payload['routing']['browser']}",
        f"confirmation: {'required' if confirmation['required'] else 'not indicated'}",
        f"signals: ui={signals['ui']} remote={signals['remote']} destructive={signals['destructive']} credentials={signals['credentials']}",
        f"owner instruction: {payload['ownerInstruction']}",
    ]
    if confirmation["reasons"]:
        lines.append("ask only: " + "；".join(confirmation["reasons"]))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, help="one-line natural-language request")
    parser.add_argument("--mode", choices=MODES, default="auto", help="optional explicit intent")
    parser.add_argument("--project-root", default=".", help="project root used for authority discovery")
    parser.add_argument("--out", type=Path, help="optional JSON receipt path; no file is written by default")
    parser.add_argument("--json", action="store_true", help="print the complete JSON draft")
    args = parser.parse_args(argv)

    try:
        payload = compile_request(args.request, mode=args.mode, project_root=args.project_root)
    except ValueError as error:
        parser.error(str(error))
    encoded = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
    sys.stdout.write(encoded if args.json else _render_summary(payload) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

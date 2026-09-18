#!/usr/bin/env python3
"""One-command tiered dispatch generator.

Turns a task outcome into concrete dispatch packs so that the daily flow does
not depend on the owner remembering who to send what to. The script decides
the tier matrix from the task type and the touched paths, writes a
self-contained dispatch pack per required tier (worker-pack format), and
prints the dispatch list (tier / agent / pack path / why).

Tier matrix:

  implement -> execution (team-os-bounded-worker); if UI paths are touched,
               also vision (team-os-ui-designer) for the visual baseline
  research  -> execution scout evidence pack
  ui        -> vision baseline + execution implementation
  plan      -> adjudication draft (@plan_alt) + analysis adjudication
  review    -> adjudication findings (team-os-deep-reviewer)
  ops       -> execution worker + prod-env preflight reminder

Usage:

  python3 route_work.py --task <id> --type <implement|research|ui|plan|review|ops> \
      --outcome "<one-line user-visible result>" \
      [--paths a.tsx,b.go] [--write-set "a.tsx;b.go"] [--read-only "…"] \
      [--out .work/dispatch] [--cwd /abs/path]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Stop-loss facts live in models/catalog.yaml (activePortfolio.dispatchPolicy);
# these fallbacks only apply when the catalog cannot be read, so the pack and the
# gate can never disagree about the budget.
DEFAULT_CATALOG = Path(__file__).resolve().parents[1] / "models" / "catalog.yaml"
FAILURE_BUDGET_FALLBACK = 2
CADENCE_MINUTES_FALLBACK = 20

# design-critical: the subset where K3 (Design Arena #1) should implement
# instead of the deepseek workhorse — design-system/shared visual components.
DESIGN_CRITICAL_PATTERN = re.compile(r"design-system|QualityRail|StatusPill|styles\.css|theme|tokens", re.IGNORECASE)

UI_FILE_PATTERN = re.compile(r"\.(tsx|css|vue|svelte)$|admin-console|/console/|\.png$|figma", re.IGNORECASE)
REMOTE_PATTERN = re.compile(r"internal/(api|server|billing|runtime)|deploy|helm|chart|rollout|migration", re.IGNORECASE)

# Node edges must name what crosses. An edge without a named product is an
# "and then" chain, not a dependency.
EDGES: dict[tuple[str, str], str] = {
    ("vision", "execution"): "视觉基线结论（组件语义、状态矩阵、样式合同）",
    ("vision", "ui-impl"): "视觉基线结论与设计合同（组件语义、状态矩阵、样式合同）",
    ("adjudication-draft", "execution"): "接口与失败面矩阵（草案中已裁决的部分）",
    ("execution-scout", "execution"): "压缩证据包（文件:行号 + 关键原句）",
    ("execution-scout", "vision"): "压缩证据包（文件:行号 + 关键原句）",
    ("prod-env", "execution"): "preflight 判定表（目标可用性、容量、权限）",
    ("judgement", "execution"): "findings（异厂挑战结论）",
}
AGENT = {
    "execution": "team-os-bounded-worker",
    "ui-impl": "team-os-ui-implementer",
    "execution-scout": "scout",
    "vision": "team-os-ui-designer",
    "adjudication-draft": "team-os-planner-alt",
    "judgement": "team-os-deep-reviewer",
}


def dispatch_policy(catalog_path: Path | None = None) -> dict:
    """Read the failure budget and cadence from the catalog (single source)."""
    path = catalog_path or DEFAULT_CATALOG
    policy: dict = {}
    try:
        import yaml

        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        policy = (payload.get("activePortfolio") or {}).get("dispatchPolicy") or {}
    except (ImportError, OSError, ValueError):
        policy = {}
    budget = policy.get("failureBudget")
    cadence = policy.get("cadenceMinutes")
    injections = policy.get("advisoryInjections")
    return {
        "failureBudget": int(budget) if isinstance(budget, int) and budget > 0 else FAILURE_BUDGET_FALLBACK,
        "cadenceMinutes": int(cadence) if isinstance(cadence, int) and cadence > 0 else CADENCE_MINUTES_FALLBACK,
        "advisoryInjections": dict(injections) if isinstance(injections, dict) else {},
    }


def load_constraints(path: str | None) -> list[dict]:
    """Constraints derived from accepted results (cross-task learning edge)."""
    if not path:
        return []
    target = Path(path)
    if not target.is_file():
        return []
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    entries = payload.get("constraints") if isinstance(payload, dict) else None
    if not isinstance(entries, list):
        return []
    return [
        entry
        for entry in entries
        if isinstance(entry, dict)
        and str(entry.get("status") or "active") == "active"
        and entry.get("id")
        and entry.get("claim")
    ]


def match_constraints(
    constraints: list[dict], workspaces: list[str], text: str, profiles: list[str] | None = None
) -> list[dict]:
    """A constraint applies on its *condition*, not on a shared workspace.

    Profiles and keywords are the precise conditions; a workspace list alone is
    too coarse (an infra constraint scoped to `ai-gateway` must not leak into a
    frontend task that also touches ai-gateway). So: profiles/keywords decide
    when present, workspaces only when nothing sharper is declared.
    """
    lowered = text.lower()
    profile_set = {str(item) for item in (profiles or [])}
    matched = []
    for entry in constraints:
        scope = entry.get("scope") if isinstance(entry.get("scope"), dict) else {}
        names = {str(item) for item in (scope.get("workspaces") or [])}
        declared_profiles = {str(item) for item in (scope.get("profiles") or [])}
        keywords = [str(item).lower() for item in (scope.get("keywords") or [])]
        if not names and not declared_profiles and not keywords:
            matched.append(entry)
            continue
        if declared_profiles or keywords:
            if declared_profiles & profile_set or any(keyword in lowered for keyword in keywords):
                matched.append(entry)
            continue
        if names & set(workspaces):
            matched.append(entry)
    return matched


def load_carry_forward(path: str | None) -> list[dict]:
    """Advisories from the last gate run, carried into this round's packs.

    A verdict that does not change what runs next is a report; this file is how
    an advisory becomes an execution constraint.
    """
    if not path:
        return []
    target = Path(path)
    if not target.is_file():
        return []
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    injections = payload.get("injections") if isinstance(payload, dict) else None
    return [item for item in injections or [] if isinstance(item, dict) and item.get("clause")]


def classify(paths: list[str]) -> dict:
    ui = any(UI_FILE_PATTERN.search(p) for p in paths)
    remote = any(REMOTE_PATTERN.search(p) for p in paths)
    design_critical = any(DESIGN_CRITICAL_PATTERN.search(p) for p in paths)
    return {"ui": ui, "remote": remote, "designCritical": design_critical}


def pack_for(
    tier: str,
    task: str,
    outcome: str,
    paths: list[str],
    cwd: str,
    write_set: str,
    read_only: str,
    failure_budget: int,
    cadence_minutes: int,
    constraints: list[dict] | None = None,
    carry: list[dict] | None = None,
    pack_meta: dict | None = None,
    design_critical: bool = False,
) -> str:
    """Render a worker-pack markdown body for one tier."""
    write = write_set or (", ".join(paths) if paths else "<绝对路径或 glob>")
    meta = pack_meta or {}
    crossings = meta.get("crosses") or []
    produces = meta.get("produces") or []
    crosses_block = "\n".join(f"- {item}" for item in crossings) or "无（本包不依赖前置节点，可并行启动）"
    produces_block = "\n".join(f"- {item}" for item in produces) or "无（本包为末跳，产物由 owner 集成）"
    carry_block = "\n".join(f"- `{item.get('code')}`：{item['clause']}" for item in (carry or [])) or "无"
    design_block = (
        "本包为设计关键实现：派发前由 owner 把角色 `ui_impl` 显式重绑到 `kimi-code/k3`（standby 阶梯），"
        "收据披露实际模型，包闭合后回滚；不升级则按默认 DeepSeek 执行。"
        if design_critical
        else "否——按默认 DeepSeek 执行；触发视觉验收失败预算时再议升级。"
    )
    constraints_block = "\n".join(
        f"- `{item['id']}`：{item['claim']}（来源：{item.get('derivedFrom') or item.get('evidence') or 'n/a'}）"
        for item in (constraints or [])
    ) or "无（本任务不命中任何跨任务约束）"
    body = f"""# 派工包：{task} / {tier}

本包由 `route_work.py` 生成，自足：下游不需要读设计正文或仓库清单推断意图。合同不完整时停止并回报。

- **前置输入（跨过什么）**：{crosses_block}
- **下一跳产物**：{produces_block}
- **本轮携带的执行约束**：{carry_block}
- **design-critical**：{design_block}

## 1. 目标

{outcome}

## 2. 写集合与边界

- 允许写入：`{write}`
- 禁止写入：`<其它域、共享设计系统、其它仓库>`
- 允许读取：`<路径:起-止>`（已知位置必须给区间）
- 禁止读取：`<已蒸馏进本包的文档>`
- 保护：不覆盖未提交改动；路径重叠时停止回报

## 3. 适用约束（跨任务学习边）

{constraints_block}

## 4. 前提与验证状态

派工包的前提必须**逐条标注状态**，禁止把未验证的假设写成事实（复盘：把"vendor 基座行为"标为未知的包，在 20 分钟内就需重构）：

| 前提 | 状态 | 依据 |
| --- | --- | --- |
| `<环境/接口/数据前提>` | verified / **unknown** / risk | `<命令 + 输出摘要 或 "待验证">` |

规则：`unknown` 的前提不得作为实现方向的基础；worker 一旦证实某条 `unknown` 前提不成立，立即按第 6 节停线回报，不自行换方向。

## 5. 变更步骤

1. `<文件>` — `<符号/函数/组件>`：<要发生的行为变化>
2. …

## 6. 合同

- 接口/签名：<代码或签名>
- 数据结构与字段：<字段、类型、必填性>
- 状态与错误语义：<状态码、错误分支、幂等键>
- 复用既有模式：<示例文件:行>

## 7. 验收

- 命令：<精确命令>
- 预期：<通过标准、收据或证据>
- 不要求：<不属于本包验证范围的构建、浏览器、远端动作>

## 8. 停止条件与失败预算

停止并回报，不自行决策：路径缺失；与现有改动重叠；需要跨边界合同决策；需要生产/远端写、提交或推送。

**失败预算 = {failure_budget} 轮**：同一验收点连续 {failure_budget} 轮 FAIL，或新证据表明阻断根因**不在本包写集合内**，立即停线——不再换下一个修复假设、不重建、不复跑。停线时回传 `STOP: <原因>`，并把"当前假设、已排除项、需要 owner 裁决的点"写清，由 owner 回到规划（改验收 / 改 owner / 升级用户）。

## 9. 节拍与输出格式

每 {cadence_minutes} 分钟或每完成一步，回传一段结构化进展（不超过 8 行）：当前假设 → 本轮证据（命令 + 关键输出）→ 下一步 → 是否需要裁决。

最终/停线输出必须包含机器可读标记，门禁按它们判定：

- `VERDICT: <验收点> PASS|FAIL`（每个验收点一行，PASS 必须附证据引用）
- `STOP: <原因>`（超出失败预算时必填）

其余输出：实际修改路径（相对仓库根）、行为变化（一段话）、验证命令与结果（收据引用）、未解决风险与需要的决策。
"""
    return body


def plan_dispatch(
    task: str,
    task_type: str,
    outcome: str,
    paths: list[str],
    cwd: str,
    write_set: str,
    read_only: str,
    out_dir: str | None = None,
) -> list[dict]:
    """Decide the tier matrix and render the packs."""
    kind = classify(paths)
    tiers: list[tuple[str, str, str]] = []  # (tier, agent, reason)

    if task_type == "implement":
        if kind["ui"]:
            # the visual baseline is a real predecessor: it crosses into the
            # frontend implementation lane (ui_impl), not the generic worker
            tiers.append(("vision", AGENT["vision"], "涉及 UI 文件，先出视觉基线再实现"))
            tiers.append(("ui-impl", AGENT["ui-impl"], "前端实现由 ui_impl 承担（DeepSeek 按量）"))
        else:
            tiers.append(("execution", AGENT["execution"], "实现与验证由执行档承担"))
    elif task_type == "research":
        tiers.append(("execution-scout", AGENT["execution-scout"], "只读证据包由 scout 取回"))
    elif task_type == "ui":
        tiers.append(("vision", AGENT["vision"], "视觉/交互深度设计"))
        tiers.append(("ui-impl", AGENT["ui-impl"], "视觉基线后的前端实现"))
    elif task_type == "plan":
        tiers.append(("adjudication-draft", AGENT["adjudication-draft"], "规划草稿对半交研判档起草"))
        tiers.append(("analysis", "plan_owner", "跨仓合同与取舍由分析档裁决（本会话）"))
    elif task_type == "review":
        tiers.append(("judgement", AGENT["judgement"], "冻结候选须一条异厂 findings 或显式豁免"))
        tiers.append(("execution", AGENT["execution"], "按 findings 整改"))
    elif task_type == "ops":
        if kind["remote"]:
            tiers.append(("prod-env", "prod-env 执行器", "远端写/刷新先取得 preflight，再按已授权计划执行"))
        tiers.append(("execution", AGENT["execution"], "运维变更由执行档实现"))
    else:  # pragma: no cover - argparse restricts values
        raise ValueError(f"unknown task type {task_type}")

    order = [tier for tier, _agent, _reason in tiers]
    packs: list[dict] = []
    for index, (tier, agent, reason) in enumerate(tiers):
        name = f"{task}-{tier}"
        base = (out_dir.rstrip("/") if out_dir else f"{cwd.rstrip('/')}/.work/dispatch")
        depends_on = [earlier for earlier in order[:index] if (earlier, tier) in EDGES]
        packs.append(
            {
                "tier": tier,
                "agent": agent,
                "reason": reason,
                "pack": f"{base}/{name}.md",
                "dependsOn": depends_on,
                "crosses": [EDGES[(earlier, tier)] for earlier in depends_on],
                "produces": sorted(
                    {product for (source, _target), product in EDGES.items() if source == tier}
                ),
            }
        )
    return packs


def render_packs(
    packs: list[dict],
    task: str,
    outcome: str,
    paths: list[str],
    cwd: str,
    write_set: str,
    read_only: str,
    failure_budget: int,
    cadence_minutes: int,
    constraints: list[dict] | None = None,
    carry: list[dict] | None = None,
    design_critical: bool = False,
) -> None:
    critical = design_critical
    for p in packs:
        Path(p["pack"]).parent.mkdir(parents=True, exist_ok=True)
        Path(p["pack"]).write_text(
            pack_for(
                p["tier"],
                task,
                outcome,
                paths,
                cwd,
                write_set,
                read_only,
                failure_budget,
                cadence_minutes,
                constraints,
                carry,
                p,
                critical,
            ),
            encoding="utf-8",
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task", required=True, help="task id")
    parser.add_argument("--type", required=True, choices=("implement", "research", "ui", "plan", "review", "ops"))
    parser.add_argument("--outcome", required=True, help="one-line user-visible result")
    parser.add_argument("--paths", default="", help="comma-separated touched paths")
    parser.add_argument("--write-set", default="", help="write set; default = paths")
    parser.add_argument("--read-only", default="", help="read-only hints")
    parser.add_argument("--cwd", default=".", help="working directory (absolute path preferred)")
    parser.add_argument("--out", default=None, help="dispatch output directory override")
    parser.add_argument("--constraints", default=None, help="cross-task constraint registry (JSON); injects applicable claims")
    parser.add_argument("--profiles", default="", help="comma-separated gate profiles the plan matched (constraint scope)")
    parser.add_argument("--carry-forward", default=None, help="advisories from the last gate run to carry into these packs")
    parser.add_argument("--design-critical", action="store_true", help="mark the frontend lane design-critical (K3 escalation path)")
    parser.add_argument("--failure-budget", type=int, default=None, help="rounds an acceptance point may fail before the worker must stop (default: catalog dispatchPolicy)")
    parser.add_argument("--cadence-minutes", type=int, default=None, help="structured progress beat interval required from the worker (default: catalog dispatchPolicy)")
    args = parser.parse_args(argv)

    paths = [p.strip() for p in args.paths.split(",") if p.strip()]
    cwd = str(Path(args.cwd).resolve())
    policy = dispatch_policy()
    budget = args.failure_budget if args.failure_budget is not None else policy["failureBudget"]
    cadence = args.cadence_minutes if args.cadence_minutes is not None else policy["cadenceMinutes"]
    workspaces = sorted({token.split(":", 1)[0] for token in paths if ":" in token})
    constraints = match_constraints(
        load_constraints(args.constraints),
        workspaces,
        " ".join([args.outcome, args.task, *paths]),
        [item.strip() for item in args.profiles.split(",") if item.strip()],
    )
    carry_path = args.carry_forward or f"{cwd.rstrip('/')}/.work/dispatch/carry-forward.json"
    carry = load_carry_forward(carry_path)
    packs = plan_dispatch(args.task, args.type, args.outcome, paths, cwd, args.write_set, args.read_only, args.out)
    render_packs(
        packs,
        args.task,
        args.outcome,
        paths,
        cwd,
        args.write_set,
        args.read_only,
        budget,
        cadence,
        constraints,
        carry,
        args.design_critical or classify(paths).get("designCritical", False),
    )

    print(f"task={args.task} type={args.type}")
    for p in packs:
        print(f"  [{p['tier']:16}] {p['agent']:<24} {p['reason']}")
        print(f"      pack -> {p['pack']}")
    for p in packs:
        for dependency in p.get("dependsOn") or []:
            crossing = next(
                (item for item in p["crosses"] if item), ""
            )
            print(f"  边: {dependency} -> {p['tier']}  跨过: {p['crosses'][p['dependsOn'].index(dependency)]}")
    if constraints:
        print("  注入跨任务约束: " + ", ".join(item["id"] for item in constraints))
    if carry:
        print("  携带上轮执行约束: " + ", ".join(str(item.get("code")) for item in carry))
    if args.design_critical or classify(paths).get("designCritical", False):
        print("  [design-critical] 前端 lane 走 K3 升级通道：派发前重绑 ui_impl → kimi-code/k3 并披露")
    print("\n派工顺序按上面的边执行；无边即并行。owner 只做裁决与收据。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

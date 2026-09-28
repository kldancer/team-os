# Codex + Team OS 日常工作流使用手册

> 本手册描述 Team OS 的 Codex 独立运行时工厂。它说明运行边界、日常入口、恢复方式和维护责任；不替代项目自己的 `AGENTS.md`、正式设计、机器计划、Gate 或生产合同。
>
> Team OS + OMP 是并行的成熟路线，继续由 [Pi/OMP 手册](02-Pi-OMP-Team-OS工作流原理与日常使用.md) 维护。本手册不把 Codex 规则写回 OMP，也不要求两条路线共享运行时配置。

## 1. 三层边界

Codex 工厂把 Team OS 的稳定方法投影到 Codex 用户目录，同时保留项目自己的执行事实：

| 层 | 拥有的事实 | 不拥有的事实 |
| --- | --- | --- |
| Codex Runtime | 当前任务、模型、推理档位、工具、权限、协作和交互 | 项目业务合同、生产授权、长期任务状态 |
| Team OS Core | 结果责任、单一 Owner、最小协作、上下文经济和跨项目方法 | 项目服务清单、Gate、生产事实、OMP Profile |
| 项目仓库 | 项目 AGENTS、正式设计、机器计划、Runner、Gate、代码和生产边界 | 跨项目运行时方法 |

项目 Runner 和 `.work` 是长任务事实源。Codex 适配器只负责把当前任务与项目计划关联、读取状态、选择适用工具并综合证据；它不创建第二套任务数据库，不代替项目 `close`、`apply`、`start` 或 `freeze`。

同一个项目可以分别使用 OMP 和 Codex，但两条路线不能同时接管同一个写任务。切换运行时前，先停止原写者，读取项目状态、有效收据、剩余验收和授权范围；原 task ID 保持不变。

## 2. 当前规则如何进入任务

Codex 采用逐层加载，不把完整 Team OS 或整个项目文档预先塞进每个任务：

```text
~/.codex/AGENTS.md
    ↓
项目 AGENTS.md
    ↓
命中的 Team OS / 项目 Skill
    ↓
任务需要的正式设计、配置和机器入口
    ↓
项目 .work 中的计划、状态和收据
```

| 载体 | 责任 | 维护位置 |
| --- | --- | --- |
| `~/.codex/AGENTS.md` | Team OS 的 Codex 用户级短内核 | Team OS `codex/AGENTS.md` |
| `team-os-plan` | 结果合同、复杂规划和最小拓扑 | Team OS Skill |
| `team-os-codex` | Codex 计划绑定、恢复、协作隔离、浏览器证据和模型适配 | Team OS Skill |
| 项目 `AGENTS.md` | 项目安全红线、权威路由和机器入口 | 目标项目仓库 |
| 项目流程 Skill | 设计、诊断、交付、评审、验证和提交流程 | 目标项目仓库 |
| 正式设计与配置 | 产品、架构、接口、Gate、部署和生产合同 | 目标项目权威文档 |
| `.work` | 动态计划、运行状态和脱敏收据 | 目标项目仓库 |

更新用户级投影：

```bash
cd <team-os-root>
python3 scripts/install_codex.py
python3 scripts/install_codex.py --check
```

`~/.codex` 是投影目标，不是维护源。不要直接编辑受管文件；如果校验报告 drift，应回到 Team OS 源文件修复后重新安装。安装器只管理清单内文件，发现本地手工修改时会拒绝覆盖。

## 3. 日常主链

用户只需要提供目标、取舍和授权。Owner 负责把它闭合成一个可验证结果：

1. 讨论目标和约束，确认结果、非目标和完成条件。
2. 读取项目 AGENTS、目标设计和必要机器事实。
3. 按意图选择唯一流程所有者：`design`、`diagnose`、`deliver-change`、`review` 或 `ship-changes`。
4. 小任务直接执行；复杂或跨边界任务按需使用 `team-os-plan`，并把合同落到项目 planner。
5. 以最小纵向切片实现或验证，保留真实 diff。
6. 只运行 changed paths、lane 和项目 Gate 要求的适用验证。
7. 记录未验项、失败和剩余风险；必要时使用同一 outcome 和 task ID 继续修复。
8. 运行事实闭合后按项目入口 close；需要提交时再转入 `ship-changes`。

“按结论开始推进”表示结论已经确定并授权实施，不表示跳过项目计划、验证或生产保护。生产和远端写仍然必须遵守项目授权、preflight、freeze、回退和真实入口合同。

## 4. 意图路由

| 用户说法 | Codex 行为 |
| --- | --- |
| “分析为什么会这样” | 只读诊断，输出假设、证据和根因 |
| “定位并整改” | 在同一诊断闭环内复现、修复和验证 |
| “设计/规划这个模块” | 形成正式设计或实施规划，不默认实现 |
| “先按正式设计定位 `<需求/症状>`，再分析” | 若项目提供 catalog，先返回唯一 owner、实现根、业务链和有界 context pack |
| “从 `<workspace:path>` 反查设计和影响” | 使用项目 path query；修改稳定合同时继续运行 contract impact |
| “按以上结论开始推进” | 读取项目权威后端到端交付 |
| “评审当前改动” | 固定 diff/commit，只读输出可执行 findings |
| “提交并推送” | 进入末端提交车道；仍需检查授权和门禁 |

对支持 typed design catalog 的项目，还可以说：“优先扩展已有 owner；只有独立 owner、失败责任或验证边界成立时才新增设计文档”“修复后合同不变就不要为 Bug 新建文档”。具体命令、合同 ID、预算和 Gate 仍以项目适配器与项目权威为准。

模型可以分析和提出方案，但不改变授权。缺少业务决定只阻塞依赖该决定的分支，独立工作继续进行。

## 5. 项目执行桥

当项目有机器 planner（例如 `juspctl`）时，项目原生入口拥有计划和执行权。Codex 适配器的桥接脚本只做三类事情：

- `plan`：显示或按明确参数调用项目本地 planner；
- `bind`：把已存在的计划与当前 Codex 任务、checkout 和实际模型信息关联；
- `inspect`：只读检查计划指纹和绑定是否仍然有效。

示例：

```bash
python3 <skill-dir>/scripts/project_bridge.py bind \
  --project-root <project-root> \
  --checkout-root <actual-checkout> \
  --task <task-id> \
  --owner <plan-result-owner> \
  --model gpt-6-astra

python3 <skill-dir>/scripts/project_bridge.py inspect \
  --project-root <project-root> \
  --task <task-id> \
  --checkout-root <actual-checkout> \
  --require-binding
```

计划指纹变化会使旧绑定失效；重新规划沿用原 task ID。绑定只证明计划与元数据关联，不证明命令已执行、输入未变、沙箱已启用或生产已授权。适用 Gate、preflight、freeze、执行、真实入口验证和 close 仍由项目负责。

没有项目 Runner 时，使用项目已有的构建、测试和 `.work` 入口；不要假造 `juspctl`，也不要在 Codex 中创建第二套状态机。

## 6. Astra 与 Sol

两种模型都可以端到端担任 Owner，模型名称不会自动创建角色、任务或权限。

| 模型 | 使用重点 |
| --- | --- |
| GPT-6 Astra | 高歧义、跨边界设计、复杂研究、集成和综合；提示应明确结果、约束、非目标和完成证据 |
| GPT-6 Sol | 边界清晰的复杂编码、定位修复和纵向交付；提示应给出具体接口、失败案例和可执行验收 |

保留用户选择的模型和推理档位，不静默切换 Provider 或 fallback。配置值是 configured，不等于本次 resolved model；无法观测的字段记为未知。切换模型时记录旧模型、新模型、作用域、fallback、resolved model 和恢复方式。

Astra/Sol 的选择是运行时策略，不写入项目长期事实，也不在项目 Skill 中固定“规划模型 → 执行模型 → 审批模型”的队列。实际可用的模型和推理档位以当前 Codex 主机为准。模型定位和提示设计参考 [GPT-6 模型与提示指导](https://developers.openai.com/api/docs/guides/latest-model) 与 [Astra Skills 与 Prompt 指导](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)。

## 7. 协作、任务和隔离

默认 solo。只有以下情况才增加协作：

- 子任务产出独有证据；
- 写集合互斥且可独立验收；
- 高风险候选需要独立只读审阅。

Codex 应优先使用当前任务允许的可检查协作工具。用户明确要求新的独立任务时，才创建侧栏任务；需要真实代码隔离时才创建 worktree。worktree 只隔离代码，不隔离数据库、网络、生产资源或凭据。

派工包至少包含目标、输入、写集合、排除项、接口、验收、预算和停止条件。Owner 最后检查真实 diff、项目收据和集成结果。不能用“任务已创建”“子任务已完成”代替结果证据。

Codex Goal 只在用户明确要求持续结果时使用；automation 只在用户明确要求调度、提醒或监控时使用。两者都不能替代项目 Runner 或保证 App 退出后本地命令继续运行。

## 8. 浏览器和 UI 证据

浏览器只提供事实，项目 UI Skill 和机器计划仍拥有验收边界：

- 已知、可重复步骤优先项目 Playwright 或脚本；
- 登录态、实时页面或探索使用当前运行时提供的浏览器/Computer Use；
- OMP 路线遵守 OMP Browser Eval；Codex 路线遵守 `team-os-codex/references/browser.md`；
- Network、Console 和性能只在当前运行时实际提供相应工具时采集；
- DOM、行为、业务结果和截图分别验证，截图不能替代 API 或数据事实；
- 收据写入项目 `.work/tasks/<task>/evidence/browser/<scenario>/`，只保存脱敏信息；
- 无浏览器条件时明确记录“未验”，不能用 build 或单测冒充真实入口验收。

## 9. 恢复与维护

长任务恢复顺序：

1. 查看项目 `status`、活动进程、最后阶段和 `.work` 收据；
2. 检查计划指纹和 Codex binding；
3. 核对剩余验收、授权范围和实际 checkout；
4. 按项目规则使用 `tail`、`resume` 或其他原生入口；
5. 只对当前仍然有效的阶段继续工作。

旧任务不会因为 Team OS 源文件更新而自动获得新的上下文。需要新规则时，先重新读取适用 Skill 或开启新的 Codex 任务；长期事实仍以项目 AGENTS、正式设计、机器计划和 `.work` 为准。

维护时遵守以下契约：

- Team OS 源文件是跨运行时方法的唯一维护位置；
- `codex/AGENTS.md` 和 `skills/team-os-codex` 是 Codex 投影源；
- OMP 角色、Profile 和模型目录继续由 OMP 路线维护；
- 项目 AGENTS、项目 Skill、正式设计和机器入口继续由项目维护；
- 不把某次会话的模型、token、临时 ID、密码或 pass/fail 写入长期文档；
- 修改后运行 `install_codex.py --check`、相关 Skill 校验和项目适用门禁。

如果 Team OS 与项目规则看起来冲突，优先采用项目 AGENTS、正式设计和机器入口；如果 Codex 运行能力与模型/API 文档不一致，以当前 Codex 工具实际返回的能力为准，并在结果中说明未验证项。

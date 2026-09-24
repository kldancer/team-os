# Codex 用户级投影

本目录是 Team OS 面向 Codex 的独立运行时工厂投影。模型选择留在 Codex 用户配置，不写入通用工作流；完整 Team OS 仍不进入每个任务上下文：

| 来源 | 安装目标 | 加载方式 |
| --- | --- | --- |
| `AGENTS.md` | `~/.codex/AGENTS.md` | Codex 用户级短内核，项目指令仍可覆盖 |
| `../skills/team-os-plan/` | `~/.codex/skills/team-os-plan/` | 讨论收敛、复杂实施或跨仓规划时按需加载；确有需要时再读取角色目录和模块实施规划模板投影 |
| `../skills/team-os-retrospective/` | `~/.codex/skills/team-os-retrospective/` | 明显返工、失败或用户要求复盘时按需加载 |
| `../skills/team-os-ui/` | `~/.codex/skills/team-os-ui/` | UI 新设计、按稿还原或可见变更时加载短入口，再按需读取 UI 工作流投影 |
| `../skills/team-os-codex/` | `~/.codex/skills/team-os-codex/` | Codex 专属的项目计划绑定、恢复、协作隔离、浏览器证据和 Astra/Sol 适配 |

运行 `python3 scripts/install_codex.py` 安装，运行 `python3 scripts/install_codex.py --check` 校验。安装器只管理清单中的短内核、按需 Skill 及其引用投影，保留其他个人 Skill；已管理文件若被本地修改会拒绝覆盖。UI 详细方法唯一维护在 `workflows/ui-design-frontend.md`，安装到 Skill references 的文件是可重建副本，不独立编辑。

完整的 `organization/`、`roles/`、`workflows/`、`models/` 和 `projects/` 是维护与解释资料，不会默认进入每个 Codex 任务上下文。

当前任务的 owner 默认端到端完成；先用最短可验证路径执行，不为展示认真而增加准备阶段。只有独有证据、互斥写集合或高风险独立验证才创建独立任务。Codex goal 只投影 durable outcome；模型、Router 或 Provider 变更必须按 [`Harness 运行合同`](../workflows/harness-contract.md) 留下身份和回退收据。


## Codex 独立工厂边界

Codex 适配器使用自己的任务、Goal、worktree、Skills、MCP、权限和模型选择；它不读取 OMP Profile、Agent Hub 或 OMP 模型别名。项目 planner、Task Runner、Gate 和 `.work` 仍是执行事实源，Codex 只负责绑定、调用、观察和综合。

`team-os-codex` 按需加载：项目计划/恢复读 `references/execution.md`，协作读 `references/collaboration.md`，真实页面读 `references/browser.md`，模型选择或流程停顿读 `references/models.md`。

GPT-6 Astra 适合高歧义的端到端综合；GPT-6 Sol 适合明确边界的复杂编码与修复。两者都可作为 Owner；模型名称不会自动创建角色、任务或权限，实际 resolved model 不可观测时必须记录为未知。

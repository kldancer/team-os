# Codex 用户级投影

本目录是 Team OS 唯一需要安装到 Codex 的运行投影：

| 来源 | 安装目标 | 加载方式 |
| --- | --- | --- |
| `AGENTS.md` | `~/.codex/AGENTS.md` | Codex 用户级短内核，项目指令仍可覆盖 |
| `skills/team-os-plan/` | `~/.codex/skills/team-os-plan/` | 讨论收敛、复杂实施或跨仓规划时按需加载；确有需要时再读取角色目录和模块实施规划模板投影 |
| `skills/team-os-retrospective/` | `~/.codex/skills/team-os-retrospective/` | 明显返工、失败或用户要求复盘时按需加载 |

运行 `python3 scripts/install_codex.py` 安装，运行 `python3 scripts/install_codex.py --check` 校验。安装器只管理清单中的短内核、两个 Skill、角色目录与模块实施规划模板投影，保留其他个人 Skill；已管理文件若被本地修改会拒绝覆盖。

完整的 `organization/`、`roles/`、`workflows/`、`models/` 和 `projects/` 是维护与解释资料，不会默认进入每个 Codex 任务上下文。

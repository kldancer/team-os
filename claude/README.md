# Claude 用户级投影

本目录是 Team OS 面向 Claude Code 的运行时投影。模型选择留在 Claude 会话与用户配置，不写入通用工作流；完整 Team OS 仍不进入每个任务上下文：

| 来源 | 安装目标 | 加载方式 |
| --- | --- | --- |
| `AGENTS.md` | `~/.claude/CLAUDE.md` | Claude 用户级短内核，项目 CLAUDE.md/AGENTS.md 仍可覆盖 |
| `../skills/team-os-plan/` | `~/.claude/skills/team-os-plan/` | 讨论收敛、复杂实施或跨仓规划时按需加载 |
| `../skills/team-os-retrospective/` | `~/.claude/skills/team-os-retrospective/` | 明显返工、失败或用户要求复盘时按需加载 |
| `../skills/team-os-ui/` | `~/.claude/skills/team-os-ui/` | UI 新设计、按稿还原或可见变更时加载，浏览器引用改指 Claude 适配 |
| `../skills/team-os-browser-verify/` | `~/.claude/skills/team-os-browser-verify/` | 真实入口取证，正文替换为 Claude 浏览器证据 |
| `../skills/team-os-claude/` | `~/.claude/skills/team-os-claude/` | Claude 专属的协作隔离、浏览器证据、长命令与恢复 |

运行 `python3 scripts/install_runtime.py claude` 安装，`--check` 校验；目标目录默认 `$CLAUDE_CONFIG_DIR`，未设置时为 `~/.claude`。安装器只管理清单内文件，保留其他 Skill、`settings.json` 与认证信息；已管理文件若被本地修改会拒绝覆盖。

项目侧接入由项目自己完成：根目录 `CLAUDE.md` 用 `@AGENTS.md` 导入项目内核，`.claude/skills` 指向项目唯一 Skill 源，`.claude/settings.json` 把项目安全红线写成 deny/ask 兜底。Team OS 不复制项目文档。

Claude 适配不投影 Codex 的 `project_bridge.py`：它绑定旧 `juspctl` 计划与 `runtime/codex` 收据。需要恢复旧 Runner 任务时直接使用项目原生入口。

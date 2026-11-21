# Antigravity 用户级投影

本目录是 Team OS 面向 Antigravity CLI（`agy`）的运行时投影，也覆盖经 ACP 客户端（如 Tern 的 `tern acp agy`）打开的 agy 会话。模型选择留在 agy 会话与用户配置。

agy 的全局自定义根目录是 `~/.gemini/config/`（agy 内置 `agy-customizations` 文档；2026-11-21 以 agy 1.5.14 实测）：

| 来源 | 安装目标 | 加载方式 |
| --- | --- | --- |
| `AGENTS.md` | `~/.gemini/config/GEMINI.md` | 全局规则，始终加载；项目 AGENTS.md/GEMINI.md 仍可覆盖 |
| `../skills/team-os-plan/` | `~/.gemini/config/skills/team-os-plan/` | 按需加载（只预载名称与描述） |
| `../skills/team-os-retrospective/` | `~/.gemini/config/skills/team-os-retrospective/` | 按需加载 |
| `../skills/team-os-ui/` | `~/.gemini/config/skills/team-os-ui/` | 按需加载 |
| `../skills/team-os-browser-verify/` | `~/.gemini/config/skills/team-os-browser-verify/` | 按需加载；工具名按 `AGENTS.md` 映射 |

运行 `python3 scripts/install_runtime.py agy` 安装，`--check` 校验。安装器只管理清单内文件，保留 `config.json`、`mcp_config.json`、`projects/` 等 agy 自有配置；已管理文件若被本地修改会拒绝覆盖。

实测到的加载规则（只用于判断，不在其他位置重复放置）：

- 全局规则：`~/.gemini/GEMINI.md`、`~/.gemini/AGENTS.md`、`~/.gemini/config/{GEMINI,AGENTS}.md`、`~/.gemini/config/rules/*.md` 均会加载；Team OS 只使用 `~/.gemini/config/GEMINI.md`。
- 全局 Skill：`~/.gemini/config/skills/`、`~/.gemini/skills/` 与 `~/.gemini/config/skills.json` 登记的目录生效；`~/.agents/skills/` 不生效。
- 项目：从当前目录向上到仓库根加载 `AGENTS.md`、`GEMINI.md`、`.agents/rules`、`.agents/skills`；不加载 `CLAUDE.md`、`.claude/`、`.gemini/skills/` 与子目录规则。
- 单个规则文件上限 24 KB；全局与始终生效规则共享 20,000 token 预算，超出降级为路径指针。

Team OS 不为 agy 维护单独的浏览器或协作适配 Skill；共享 Skill 中运行时专属的工具名由 `AGENTS.md` 说明如何映射。

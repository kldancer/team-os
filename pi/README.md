# Pi 用户级投影

Pi 是 Team OS 的最小兼容基线。它原生加载 `~/.pi/agent/AGENTS.md`、项目根 `AGENTS.md`、`~/.pi/agent/skills/` 和项目 `.agents/skills/`；browser、computer use、subagent 和 Goal 不是核心依赖，只有对应扩展通过 Harness Gate 后才启用。

安装 Pi 后投影 Team OS：

```bash
python3 scripts/install_runtime.py pi
python3 scripts/install_runtime.py pi --check
```

修改上下文或 Skill 后在 Pi 中运行 `/reload`。不要为了补齐 OMP 能力一次安装大量社区包；每个 package 都拥有当前用户权限，应逐个审计、固定版本并记录删除条件。

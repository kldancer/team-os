# 运行时适配器合同

本目录只描述不同 Agent harness 如何承载 Team OS 语义，不保存用户凭据、实际 Session、机器私有路径或 Provider 配置。

- [`capabilities.yaml`](capabilities.yaml) 是能力和降级方式的机器可读目录。
- `../codex/`、`../pi/`、`../omp/` 是用户级短内核与安装说明。
- `../skills/` 是所有运行时共享的 Skill 唯一源。
- 项目根 `AGENTS.md` 与 `.agents/skills/` 保持运行时中立；客户端专属设置留在用户目录或项目专属适配目录。

矩阵中的 `native` 只说明工具存在，不表示某次任务已授权。版本、模型、审批模式和实际启用能力必须由运行收据确认。

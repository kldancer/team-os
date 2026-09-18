# Pi/OMP + Team OS 日常工作流手册

本文已拆分为两篇职责清晰的文档，旧路径保留为入口，避免已有链接失效。

## 工作流原理与日常使用

稳定方法、结果合同、角色职责、solo/协作判断、派工、Session 恢复、模型临时切换和 Browser/Computer 使用，见：

[`02-Pi-OMP-Team-OS工作流原理与日常使用.md`](./02-Pi-OMP-Team-OS工作流原理与日常使用.md)

## 配置实施记录

当前 OMP Profile、模型绑定、Provider 登录、CLIProxyAPI、TeamoRouter、Context Promotion、投影和路由验证，见：

[`02-Pi-OMP-Team-OS配置实施记录.md`](./02-Pi-OMP-Team-OS配置实施记录.md)

## 权威边界

- 稳定角色与工作流原则：Team OS `AGENTS.md`、`omp/AGENTS.md`、工作流文档；
- 当前模型绑定与 fallback：[`models/catalog.yaml`](../../models/catalog.yaml)；
- OMP Profile 实际运行值：`~/.omp/profiles/team-os/agent/config.yml` 和 `models.yml`；
- 项目事实、机器计划、Gate 和动态收据：目标项目仓库及其 `.work`。

Provider、价格、用量、模型可用性和本机端口都是动态事实，不应复制到稳定工作流正文；变更后更新配置实施记录或机器事实，并运行对应检查。

# OMP + Team OS 运行时适配器

OMP 只是交互入口。长期任务状态、执行日志、构建、部署、验证和恢复由项目的执行引擎与 `.work/tasks/<task-id>/` 持有；OMP 会话关闭不应丢失任务。

## 三类角色

| 角色 | 默认职责 | 启用条件 |
| --- | --- | --- |
| `@owner` | 定界、实现、验证、最终综合 | 默认，每个结果一个 owner |
| `@worker` | 有界取证、批量机械操作或互斥写集合内实现 | 有独有证据收益时 |
| `@reviewer` | 只读挑战、风险审查和高风险候选复核 | 风险或用户明确要求时 |

UI、视觉、数据库和 SRE 是能力标签。它们不会自动创建额外角色，也不会形成固定接力队列。

## 安装

```bash
python3 scripts/install_runtime.py omp --profile team-os
python3 scripts/install_runtime.py omp --profile team-os --check
omp --profile team-os
```

运行时模型可以按 Profile 或当前会话绑定到三类角色。切换时报告 resolved model、作用域和恢复方式；模型路由检查用于发现配置漂移，不是 close Gate。

## 日常闭环

1. 在 OMP 中描述用户结果和范围。
2. owner 读取项目 `AGENTS.md`、正式设计和目标片段。
3. 小任务直接完成；需要独立证据或互斥写集合时才派 `@worker`；高风险时才派 `@reviewer`。
4. 构建、部署和长验证交给项目执行引擎，实时输出命令、阶段和日志路径。
5. 使用项目命令恢复或查看任务：

```bash
python3 .agents/scripts/juspctl.py status --task <task-id>
python3 .agents/scripts/juspctl.py tail --task <task-id> --follow
python3 .agents/scripts/juspctl.py resume --task <task-id>
```

若项目没有 `resume` 子命令，以项目现有的 state/receipt 入口为准。OMP 不保存生产任务的唯一状态。

## 边界

- 不提交、推送、生产写、删除数据或发送外部消息，除非本次任务明确授权且项目入口要求。
- 不覆盖用户未提交改动。
- 任务级计划和刷新 manifest 必须放在 `.work/tasks/<task-id>/`，不得依赖并发任务共享的可写 manifest。
- 长命令必须有实时输出、hard timeout、日志路径和可恢复状态。

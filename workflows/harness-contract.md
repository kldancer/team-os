# Harness 运行合同

Team OS 以用户结果为中心；Codex、Pi、OMP 只负责承载 Session、模型和工具。模型能力与 harness 能力分别记录，不能把“模型可调用”当成“执行链可交付”。当前能力矩阵见 [`../runtimes/capabilities.yaml`](../runtimes/capabilities.yaml)。

## 不随运行时变化的合同

- 一个 outcome 只有一个结果负责人；运行时 task、subagent、todo、goal、Gate 和重试都不是新 outcome。
- 项目 `AGENTS.md`、正式设计和机器入口拥有项目事实；用户级投影只能补跨项目习惯。
- 项目机器状态或 `.work` 保存跨 Session 恢复所需的最小 outcome、授权、变更、收据和剩余验收；Transcript 不作为唯一恢复源。
- Provider、模型、工具权限或 fallback 发生变化时必须显式披露；不能静默改变 owner。
- 未授权的提交、远端、生产、破坏性操作和数据删除必须停止。

## Goal 与协作映射

Durable outcome 是 Team OS 语义，运行时功能只是投影：

| Team OS 语义 | Codex | Pi | OMP |
| --- | --- | --- | --- |
| 连续工作 | 当前任务/Session | 当前 Session 树 | 当前 Session |
| 长期 Goal | 原生 goal 投影 | 已准入扩展或项目状态 | todo/checkpoint + 项目状态 |
| 独立执行单元 | 侧栏可见独立任务 | 已准入 subagent 扩展 | Agent Hub 可见 worker |
| 高风险验证 | 独立只读任务 | 独立进程/扩展收据 | 只读或隔离 worker |

运行时 Goal、todo 或 checkpoint 不替代覆盖型实施规划、项目机器任务或验收证据。跨 harness 恢复时先读取项目状态，再按需要绑定新的 Session；不尝试迁移完整 Transcript。

## 最小一致性 Gate

一个 harness 进入项目交付链前，必须证明：

1. 能按确定优先级读取用户级和项目级 `AGENTS.md`，并服从项目更具体的事实。
2. 能按需读取 Skill，不把未经授权的写入变成默认动作。
3. 能执行项目机器入口，并把 outcome、harness、模型、版本和工具配置写入运行收据。
4. 能恢复或明确终止中断的 Session，区分工具调用、工具执行和业务完成。
5. 独立执行单元可检查状态、Transcript、实际模型和停止动作；写任务有互斥写集合或工作区隔离。
6. browser、computer、远端和生产工具可以按 Profile 禁用或单独授权。
7. 未授权的远端、生产、提交、破坏性操作和数据删除会停止。

未通过相应能力 Gate 的 harness 或插件只能用于隔离、只读研究；能力缺失按 `native → approved-extension → unavailable` 显式降级，不用 Prompt 假装工具存在。

## 运行收据

需要跨 Session 恢复、使用非默认模型、启用独立 worker 或执行 Gate 时，收据至少记录：

- `outcome_id`、`harness_id`、`harness_version`；
- `model_id`、Provider、角色画像和是否发生 fallback；
- Session/worker 引用、工作目录、写集合和隔离方式；
- 启用的高权限工具与审批模式；
- 输入指纹、验证结果和证据引用。

密钥、Cookie、完整认证响应和 Transcript 不得写入收据。

## 安全与可删除性

Pi/OMP 的 project trust、Prompt 规则和工具审批不等于操作系统 sandbox。未信任仓库、无人值守写入或含高价值凭据的任务应使用容器、VM、受限账号和最小挂载。每个新增 Skill、插件、角色、Gate、记忆层或启动文件都要记录针对的失败、预期收益、成本和删除条件；连续相近任务没有可观察收益时删除或简化。

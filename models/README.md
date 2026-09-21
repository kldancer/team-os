# 模型组合与准入策略

## 运行原则

模型不拥有工作流。Team OS 只定义三类责任：`owner`、`worker`、`reviewer`；模型由当前 harness 绑定。项目 Task Runner 才是构建、部署、验证和恢复的执行事实源。

默认使用一个 owner 端到端完成结果。只有独有证据、互斥写集合、批量机械工作或高风险独立验证成立时才启用 worker/reviewer。UI、视觉、数据库和 SRE 是能力标签，不是模型角色。

## 当前 OMP 绑定

| 角色 | 默认模型 | 责任 |
| --- | --- | --- |
| `@owner` | `cliproxyapi/gpt-5.6-sol` | 结果、实现、验证和综合 |
| `@worker` | `teamorouter/deepseek-flash` | 有界取证和执行 |
| `@reviewer` | `kimi-code/k3` | 高风险只读挑战 |

绑定、fallback 和 resolved model 以 `catalog.yaml` 与 OMP Profile 为准。切换必须披露作用域和恢复方式；路由检查用于发现漂移和成本，不阻塞 close。

## 新模型准入

新增模型必须证明：工具调用和 Session 恢复可靠；不会增加日常步骤；在真实任务中提供独有证据；失败、停止、超时和数据边界可解释。只凭 benchmark、上下文窗口或模型名称不能晋升默认绑定。

## 删除条件

任何模型、角色、Skill 或 Gate 如果只增加等待、Token、交接或重复读取，没有独有证据收益，就从默认路径删除，保留为显式实验入口。

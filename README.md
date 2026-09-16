# Personal Team OS

这是个人跨平台、跨项目、跨 Agent harness 的工作方法源仓库。它不替代 Codex、Pi、OMP 或其他客户端，也不充当任何具体平台的总控工程：

- Team OS 维护跨项目稳定的目标合同、协作拓扑、角色能力、复盘方法和运行时适配器；
- `jusuan-installer` 等平台总控仓库维护各自的业务事实、子工程清单、机器 Gate、正式设计、生产环境和可执行 Skill；
- 选定的 Agent harness 维护 Session、工具执行、权限提示和交互体验；
- Munder 或其他可视化运行时以后可以消费 Team OS，但不是工作流生效的前置依赖。

依赖方向固定为：`Team OS 通用核心 → 运行时适配器 → 项目覆盖层`。越靠近项目，事实越具体、优先级越高；Team OS 不复制项目正文，不保存运行流水。运行时的 Goal、todo、Session 和 subagent 只是结果合同的执行投影，不是长期事实源。

## 日常使用

1. 在 Codex、Pi 或 OMP 中从目标平台总控仓库或目标子工程启动，像往常一样讨论想法。
2. 当结论满意后说“按结论开始推进”。当前会话把讨论结论收敛为一个结果合同，并读取项目 `AGENTS.md`、工作流规范、正式设计和机器入口。
3. 默认由当前会话端到端交付；只有独立证据、互斥写集合或高风险独立验证足以覆盖协调成本时才创建协作任务。
4. 实现、验证和证据遵守项目覆盖层。提交、远端、生产和破坏性操作仍须由用户明确授权。

安装到运行时的只是短内核和按需 Skill，完整 Team OS 文档不会自动塞入每个任务上下文。Codex、Pi、OMP 的入口分别见 [`codex/README.md`](codex/README.md)、[`pi/README.md`](pi/README.md) 和 [`omp/README.md`](omp/README.md)。UI 设计与前端交付的方法见 [`workflows/ui-design-frontend.md`](workflows/ui-design-frontend.md)，不替代项目的设计系统和交付流程。派工包、读取纪律与执行模型分档见 [`workflows/context-economy.md`](workflows/context-economy.md)，派工包骨架见 [`templates/worker-pack.md`](templates/worker-pack.md)；模型路由与运行绑定的核对入口是 [`scripts/check_model_routes.py`](scripts/check_model_routes.py)。

第一次使用或需要回顾整条链路时，Codex 用户见 [`Codex + Team OS 日常工作流使用手册`](docs/使用手册/01-Codex-Team-OS日常工作流使用手册.md)，Pi/OMP 用户见 [`Pi/OMP + Team OS 使用手册`](docs/使用手册/02-Pi-OMP-Team-OS日常工作流使用手册.md)。使用社区 Bridge 连接本地 Figma 画布时，见 [`OMP + Figma MCP Bridge 从 0 到 1 使用手册`](docs/使用手册/03-OMP-Figma-MCP-Bridge从0到1使用手册.md)。

## 目录

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | Team OS 自身和通用协作的短内核 |
| `docs/使用手册/` | 面向用户的日常入口、图解原理和可复制说法 |
| `organization/` | 组织原则与决策权 |
| `roles/` | 通用角色合同及编写规范 |
| `workflows/` | 跨项目通用生命周期与交接合同 |
| `models/` | 模型能力、Provider 成熟度和准入策略 |
| `tools/` | Agent harness 工具通道、配置归属和安全边界 |
| `skills/` | 跨运行时共享的 Team OS Skill 唯一源 |
| `runtimes/` | Harness 能力合同、Goal/Session 映射和准入矩阵 |
| `codex/` | 可安装到 `~/.codex` 的最小用户级投影 |
| `pi/` | 可安装到 `~/.pi/agent` 的最小用户级投影 |
| `omp/` | 可安装到 OMP 默认或命名 Profile 的最小投影 |
| `scripts/` | 安全安装与验证脚本 |
| `templates/` | 结果卡等稳定数据模板 |
| `projects/` | 项目注册表、只读适配器和权威归属/去重 Gate |
| `evals/` | 协作质量、效率与成本的评测准则 |

项目适配器只保存平台总控入口和能力，不登记平台内的每一个服务。动态日志、Session、Transcript、一次性收据和密钥不得进入本仓库。

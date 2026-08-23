# Munder Difflin Personal Team OS

这是个人本机智能体专业团队的通用制度仓库。它与 Munder 产品源码、运行态办公室和具体项目仓库相互独立：

- Munder 负责 UI、PTY、Hive、Provider 和运行控制；
- Team OS 负责跨项目稳定的组织原则、角色、工作流、模板、项目索引和评测准则；
- `office/`、`office-dev/` 负责 Session、信箱、任务、记忆和 Provider Home；
- 每个项目仓库继续拥有自己的业务事实、Gate、正式设计、生产环境和机器计划。

核心规则是：通用制度上移，项目合同留守，运行状态投影，证据只做引用。

## 当前状态

当前已完成 TOS0～TOS3：在最小目录、通用短内核和聚算平台只读适配器之上，已建立科学协作与软件交付操作模型、自适应拓扑、角色/专业能力目录、模型准入和评测合同；Munder Main Process 可有界、只读地校验项目、角色、能力和结果卡模板，并在 Michael 的 Command Center 显式编译、预览结果卡工作单。工作单只引用项目路径，不复制项目正文；默认不授权本地写，远端、生产、破坏性和 Git 写始终关闭；填入 Michael 分派框也不会自动发送。自动路由、自动选模、Hive 任务持久化和真实 workflow eval 属于后续 TOS4，不能把工作单预览误认为执行已经发生。

## 目录

| 路径 | 用途 |
| --- | --- |
| `AGENTS.md` | Team OS 自身和通用协作的短内核 |
| `organization/` | 组织原则与决策权 |
| `roles/` | 通用角色合同及编写规范 |
| `workflows/` | 跨项目通用生命周期与交接合同 |
| `models/` | 模型能力、Provider 成熟度和准入策略 |
| `templates/` | 结果卡等稳定数据模板 |
| `projects/` | 项目注册表、只读适配器和权威归属/去重 Gate |
| `evals/` | 协作质量、效率与成本的评测准则 |

项目适配器只保存地址和能力，不复制项目原文。动态日志、Session、Transcript、一次性收据和密钥不得进入本仓库。

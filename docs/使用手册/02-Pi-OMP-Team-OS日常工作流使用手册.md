# Pi/OMP + Team OS 日常工作流使用手册

> 面向把 OMP 作为长期主驾驶舱、把原生 Pi 作为最小兼容基线的日常使用。它解释“从哪里启动、怎样说、什么功能归谁、怎样恢复”，不替代目标项目的 `AGENTS.md`、正式设计、机器 Gate 或生产合同。

## 1. 先用一句话理解整套系统

OMP 是驾驶舱，Team OS 是不随模型变化的工作方法，项目仓库才是业务事实与验收的所有者。模型可以更换，Session 可以恢复，worker 可以增减；同一个用户结果、授权边界、项目事实和有效收据不能因此重建。

```mermaid
flowchart LR
    U(["🧑 你<br/>提出目标 · 做取舍 · 给授权"])

    subgraph COCKPIT["🛩️ 驾驶舱：OMP"]
        O["💬 Owner Session<br/>讨论 · 综合 · 实现 · 交付"]
        AH["🛰️ Agent Hub<br/>观察 · 引导 · 停止 worker"]
        T["🧰 原生工具<br/>文件 · Shell · LSP · Browser · Computer"]
        M["🧠 模型角色<br/>owner · fast · review · vision · slow"]
    end

    subgraph COMPASS["🧭 航海规则：Team OS"]
        K["📜 用户级短内核<br/>结果 · 安全 · 授权 · 最小协作"]
        SK["🧩 按需 Skill<br/>规划 · 复盘 · UI"]
        HC["🔌 Harness 合同<br/>能力 · 降级 · 恢复 · 证据"]
    end

    subgraph FACTORY["🏗️ 项目工厂：目标仓库"]
        A["🗺️ 项目 AGENTS / 正式设计<br/>真实业务与边界"]
        P["⚙️ 机器计划与 Gate<br/>决定该做和该验什么"]
        C["🛠️ 代码与配置<br/>纵向实现"]
        W[("🧾 .work<br/>动态状态 · 收据 · 恢复锚点")]
    end

    U -->|"自然语言交流"| O
    K -.->|"Profile 自动加载"| O
    SK -.->|"任务命中时加载"| O
    HC -.->|"约束工具与协作"| O
    O --- M
    O --> T
    O -->|"必要时分派有界任务"| AH
    AH -->|"证据和产物返回"| O
    O -->|"读取更具体的项目权威"| A
    A --> P --> C --> W
    W -->|"恢复与验收证据"| O
    O -->|"结果、风险、跳过项"| U

    classDef human fill:#fff4cc,stroke:#9a6b00,color:#3d2b00,stroke-width:2px;
    classDef omp fill:#dcecff,stroke:#2b6cb0,color:#17365d,stroke-width:2px;
    classDef team fill:#efe4ff,stroke:#7b3fc6,color:#36205a,stroke-width:2px;
    classDef project fill:#dcf7e8,stroke:#21865a,color:#123f2e,stroke-width:2px;
    classDef receipt fill:#fff0e3,stroke:#bf6b21,color:#5a2f0d,stroke-width:2px;
    class U human;
    class O,AH,T,M omp;
    class K,SK,HC team;
    class A,P,C project;
    class W receipt;
```

这不是“让 OMP 模仿 Codex 的所有名词”。正确做法是把同一语义映射到各自原生能力：

| 稳定语义 | OMP 中的载体 | 谁拥有长期事实 |
| --- | --- | --- |
| 用户可验证结果 | durable outcome | 项目机器状态或 `.work` |
| 当前工作上下文 | Session | OMP |
| 当前执行清单 | `todo` / checkpoint | OMP；只作为短期投影 |
| 并行协作 | `task` + Agent Hub | OMP；Owner 负责综合 |
| 项目规则 | 项目 `AGENTS.md`、Skill、正式设计 | 项目仓库 |
| 验收证据 | Gate receipt | 项目 `.work` |
| 模型选择 | 模型角色与本地 Profile | OMP 本机配置，不写入 Team OS |

## 2. 四层文件怎样进入当前 Session

```mermaid
flowchart TB
    Q["🎯 当前目标与本次授权"]
    U["🌍 用户级投影<br/>~/.omp/profiles/team-os/agent/AGENTS.md + RULES.md"]
    S["🧩 共享 Skill<br/>~/.omp/profiles/team-os/agent/skills"]
    P["🏢 项目覆盖层<br/>项目 AGENTS.md + .agents/skills"]
    D["📚 目标片段<br/>正式设计 · 配置 · 代码"]
    M["⚙️ 机器事实<br/>计划 · Gate · workspace · .work"]
    X["💬 当前 Owner Session 的最小上下文"]
    N["🚫 不默认装入<br/>全部 Team OS · 全项目文档 · 历史 Transcript"]

    Q --> X
    U -->|"跨项目稳定习惯"| X
    S -->|"任务命中时按需读取"| X
    P -->|"更具体，优先级更高"| X
    D -->|"会改变执行路径时读取"| X
    M -->|"执行与恢复前解析"| X
    N -.->|"控制上下文噪声"| X

    classDef input fill:#fff4cc,stroke:#9a6b00,color:#3d2b00;
    classDef team fill:#e9e4ff,stroke:#7357c2,color:#2f2850;
    classDef project fill:#dcf7e8,stroke:#21865a,color:#123f2e;
    classDef current fill:#dcecff,stroke:#2b6cb0,color:#17365d,stroke-width:3px;
    classDef no fill:#ffe0e0,stroke:#c23b3b,color:#641f1f;
    class Q input;
    class U,S team;
    class P,D,M project;
    class X current;
    class N no;
```

Team OS 仓库是源，Profile 是可重建投影。不要直接把长期规则手改在 `~/.omp/profiles/team-os/agent`；应修改 Team OS 源文件后重新投影。

## 3. 首次启用与当前高能力配置

### 3.1 安装 Team OS 投影

在 Team OS 仓库运行：

```bash
python3 scripts/install_runtime.py omp --profile team-os
python3 scripts/install_runtime.py omp --profile team-os --check
```

投影路径是：

```text
~/.omp/profiles/team-os/agent/
├── AGENTS.md
├── RULES.md
├── skills/
└── team-os-install.json
```

### 3.2 设置并发、递归、Browser 与 Computer

当前 Team OS Profile 采用“能力打开、调用按需、后果操作仍审批”的配置：

```bash
omp --profile team-os config set tools.approvalMode write
omp --profile team-os config set task.maxConcurrency 12
omp --profile team-os config set task.maxRecursionDepth 2
omp --profile team-os config set task.maxRuntimeMs 1800000
omp --profile team-os config set task.showResolvedModelBadge true
omp --profile team-os config set browser.enabled true
omp --profile team-os config set computer.enabled true
omp --profile team-os config set computer.display all
omp --profile team-os config set computer.maxWidth 3840
omp --profile team-os config set computer.maxHeight 2400
```

这里的 `12` 是并发容量上限，不是“每项任务都启动 12 个 worker”。通常仍由 Owner 单独完成；只有独立证据、互斥写集合或高风险独立验证的收益覆盖协调成本时才并行。递归深度 `2` 允许主 worker 再做一层有界拆分，但每层都必须有明确输出和停止条件。

`computer.enabled=true` 表示功能随时可用，不表示模型可以自行扩大授权。屏幕、网页、仓库或工具输出都属于不可信输入，不能代替你授权提交、推送、生产写、删除数据或外部消息。

修改 Computer 全局设置后要新建 Session，确保工具清单重新加载。macOS 首次使用时还需要在“系统设置 → 隐私与安全性”中授予 OMP/终端对应的屏幕录制和辅助功能权限。

### 3.3 启动与登录

始终从目标项目目录启动：

```bash
cd /path/to/project
omp --profile team-os
```

进入后：

- `/login`：登录或管理 Provider。
- `/model`：选择当前模型，并在 Roles 视图配置角色映射。
- `/settings`：查看和调整交互设置。
- `/hotkeys`：查看当前版本的全部快捷键。
- `Ctrl+P`：在候选模型间循环。
- `Alt+P`：临时切换当前模型。
- `Alt+Shift+P`：切换只读 Plan 模式。

macOS 中文档写的 `Alt` 对应 `Option`（`⌥`）；如果 `⌥` 组合键输入了特殊字符，说明当前终端没有把
Option 映射为 Meta，应改用命令入口或先通过 `/hotkeys` 核对实际绑定。

不要把模型名称写死进组织内核或项目规则；当前经过验证的组合只记录在模型目录和 OMP 适配器。本 Profile 按四档绑定：分析档 `plan_owner`（Kimi K3）、研判档 `deep_review`（GLM-5.3）、视觉档 `ui_deep`（GLM-5.3-Flash）是订阅档角色，共同持有分析、评审、裁决和视觉判断；执行档由 `fast_worker` 与 `task.agentModelOverrides` 落实；`default` 指向分析档（主 Session 默认模型）。核对 resolved model 要双向看：订阅档角色不得静默回退或跨档，执行档也不得静默升级；模型切换或 fallback 发生时，必须在最终报告和适用收据中披露实际模型。

### 3.4 Kimi K3、GLM-5.3、GLM-5.3-Flash、DeepSeek V4.1 Flash 怎样分工

这里采用“稳定能力档位 + 当前四模型组合”两层结构。档位不随厂商变化；当前组合写在 `models/catalog.yaml`（id `cn-k3-glm-ds-v1`），以后有真实任务证据时可以替换模型而不改组织内核。

```mermaid
flowchart TB
    TASK["🎯 已有 outcome 与明确任务"]
    KIND{"需要哪一档能力？"}
    K3["🧭 Kimi K3（分析档）<br/>Owner · 规划 · 跨边界设计 · 裁决 · 最终综合"]
    GLM["🔬 GLM-5.3（研判档）<br/>异厂红队 · 只读深度评审 · 失败面审计"]
    VLM["🎨 GLM-5.3-Flash（视觉档）<br/>UI/UX · 视觉判断 · 前端实现循环"]
    FAST["⚡ DeepSeek V4.1 Flash（执行档）<br/>压缩证据包 · 批量事实"]
    WRITE["🛠️ DeepSeek V4.1 Flash<br/>派工包内的有界实现"]
    LEAF["⚙️ 执行档<br/>guard/smoke/refresh/prod-env 叶子执行 · 机械文档 · 提交准备"]
    MERGE["🧩 Kimi K3<br/>裁决评审发现 · 复核真实 diff · 集成 · Gate"]

    TASK --> KIND
    KIND -->|"定界、规划、跨边界设计、最终综合"| K3
    KIND -->|"冻结候选的异厂挑战与深度评审"| GLM
    KIND -->|"新 UI、视觉基线、交互状态"| VLM
    KIND -->|"需要独立事实或压缩证据包"| FAST
    KIND -->|"路径互斥且验收明确"| WRITE
    KIND -->|"门禁/刷新/冒烟执行或机械文档"| LEAF
    GLM -->|"只返回 findings 与证据，不改稿"| MERGE
    VLM --> MERGE
    FAST --> MERGE
    WRITE --> MERGE
    LEAF --> MERGE
    K3 --> MERGE

    classDef input fill:#fff4cc,stroke:#9a6b00,color:#3d2b00;
    classDef analysis fill:#dcecff,stroke:#2b6cb0,color:#17365d,stroke-width:3px;
    classDef judge fill:#efe4ff,stroke:#7b3fc6,color:#36205a;
    classDef vision fill:#ffe6f2,stroke:#b5399a,color:#5c1d4d;
    classDef exec fill:#dcf7e8,stroke:#21865a,color:#123f2e;
    classDef merge fill:#fff0e3,stroke:#bf6b21,color:#5a2f0d,stroke-width:2px;
    class TASK,KIND input;
    class K3 analysis;
    class GLM judge;
    class VLM vision;
    class FAST,WRITE,LEAF exec;
    class MERGE merge;
```

| 档位/模型 | 默认拥有 | 最适合 | 默认不做 | 何时升级权限 |
| --- | --- | --- | --- | --- |
| 分析档：Kimi K3 | outcome、规划、跨边界设计与状态冻结、对评审发现的裁决、最终综合 | 需要连续理解范围、合同、集成和验证的主链；整仓与长文档阅读 | 已能写成派工包的常规实施；批量执行与批量读取 | 生产写仍需用户授权 |
| 研判档：GLM-5.3 | 异厂红队、只读深度评审、失败面审计、诊断第二假设 | 冻结候选的反例搜索、跨厂独立判断、1M 纯文本全仓分析 | 最终综合；评审中改稿；无图像输入的视觉判断 | 高风险设计或用户显式要求独立挑战时启用；结论仍由分析档裁决 |
| 视觉档：GLM-5.3-Flash | UI/UX 与视觉判断、前端交互状态、前端实现循环、多模态证据 | 需要看图、比对渲染结果、产出视觉验收结论的任务 | 跨仓架构与合同决策；最终综合；高风险独立评审 | 结论必须附 Browser/Computer 原始证据；设计定稿由分析档确认 |
| 执行档：DeepSeek V4.1 Flash | 侦察与压缩证据包、批量事实、独立模型族挑战、派工包内的有界实现、`guard`/`smoke`/`refresh`/`prod-env` 叶子执行、机械文档与提交准备 | 大量独立读取、低延迟反馈、路径互斥且验收明确的工作；上下文窗口足以吞下派工包与目标文件 | 最终综合、跨边界设计与状态冻结、migration 或生产写 Owner | Provider/工具/恢复通过验证；派工包给出互斥写集合、内联合同和目标验证；Owner 复核真实 diff |

分工按四档：订阅档（K3、GLM-5.3、GLM-5.3-Flash）只做只有它能做的事——裁决、红队与评审、视觉判断；其余工作默认走执行档（DeepSeek），末端机械车道（提交、推送、查收据、机械校准）不要求额外角色绑定。这样订阅窗口额度只花在无法替代的判断上。

两个结构性约束与一个额度纪律：

- **异议与裁决分离。** 研判档只返回 findings 与证据，不改稿；裁决权在分析档。评审者与被评审对象必须是不同厂：K3（月之暗面）与 GLM（智谱）天然异厂。
- **视觉两级流水线。** 截图/DOM 的事实抽取交执行档（按量、带缓存、便宜），判断与修正交视觉档；不要把整页图像在订阅窗口里反复比对。
- **订阅档不做批量执行。** Kimi 会员池与智谱积分都是 5 小时/周窗口；GLM-5.3 在高峰（工作日 14:00–18:00）要按 3 倍系数扣减，而 GLM-5.3-Flash 非高峰只要 0.4 倍，执行负载或高峰评审都会把窗口额度耗光。窗口与峰谷排程的完整规则见 `workflows/context-economy.md` 第 5 节；窗口数值的机器事实见 `catalog.yaml` 的 `quotaWindows`。

这里不是按排行榜排职位。GLM-5.3 在开放模型里的 agentic coding 与终端任务表现最强，但套餐积分系数也最高，所以只承接必须由它做的红队与评审；GLM-5.3-Flash 是套餐内唯一多模态模型，因此视觉判断归它。Kimi K3 官方定位是长程编码与端到端知识工作，适合作为规划、跨边界设计与裁决 Owner。官方文档明确 `k3-256k` 在 256K 上下文内质量与 `k3` 相同、而 `k3`（1M）消耗约为其两倍，所以**子代理规划用 `k3-256k`**；但本机实测主会话上下文中位数 430K、73.8% 的请求超过 256K，因此**主 Session 默认留在 1M `k3`**，靠第 5 节纪律把主线占用压下来，而不是靠压缩窗口换额度。DeepSeek V4.1 Flash 官方强调速度、吞吐、Agent 和多模态能力，且按量计费、无窗口，适合承担执行带宽，但最终责任仍留给分析档。

在 `/model` 的 Roles 视图配置六个自定义别名（分析/研判/视觉/执行四档，加套餐内高速备选和决定未绑定工作落点的 `default`）：

| OMP 角色别名 | 指向 | 用途 |
| --- | --- | --- |
| `plan_owner` | Kimi K3（`k3-256k`，子代理规划） | 分析档：规划、跨边界设计、裁决与派工包 |
| `deep_review` | GLM-5.3 | 研判档：异厂红队与深度只读评审 |
| `ui_deep` | GLM-5.3-Flash | 视觉档：UI/前端深度设计与视觉判断 |
| `fast_worker` | DeepSeek V4.1 Flash | 执行档：侦察与派工包内的有界实现 |
| `fast_alt` | `kimi-for-coding-highspeed` | 套餐内高速备选：只在显式选择时使用 |
| `default` | Kimi K3（`k3:high`，1M） | 分析档：主 Session 默认模型与未绑定回退 |

在配置文件中的持久化形状如下（当前实际值；换 Provider 时从 `/model` 的实际可用模型中选择，不能照抄）：

```yaml
modelRoles:
  plan_owner: kimi-code/k3-256k
  deep_review: zhipu-coding-plan/glm-5.3
  ui_deep: zhipu-coding-plan/glm-5.3-flash
  fast_worker: teamorouter/deepseek-flash
  fast_alt: kimi-code/kimi-for-coding-highspeed
  default: kimi-code/k3:high
```

执行档不靠 `default` 落实：`default` 指向分析档，决定主 Session 默认模型；执行工作由 `@fast_worker` 和 Profile 的 `task.agentModelOverrides`（泛型 `task`/`scout`/`sonic`）绑定，因为**未绑定的子角色会继承父 Session 模型**。selector、覆盖项和 agent 回退链的声明位置是 `models/catalog.yaml` 的 `ompResolvedSelectors`、`ompTaskAgentModelOverrides`、`ompAgentFallbacks`（回退链只在同一计费档内），可用 `python3 scripts/check_model_routes.py` 一次性核对配置漂移、混档回退、agent 链一致性和运行时按档位/峰谷的真实用量。

安装器会投影五个可直接被 `task` 调用的 OMP Agent：

- `team-os-planner`：K3，只读有界规划。
- `team-os-ui-designer`：GLM-5.3-Flash，只读 UI/UX 和视觉设计。
- `team-os-deep-reviewer`：GLM-5.3，只读深度评审。
- `team-os-fast-scout`：DeepSeek，只读高速证据。
- `team-os-bounded-worker`：DeepSeek，只按派工包修改互斥路径，越界或合同不全时停止回报。

每个需要动手或取证的派工先写自足派工包：仓库绝对路径与工作目录、写集合、禁止读取、按顺序的变更步骤、内联合同、验收命令、停止条件和输出格式（骨架见 Team OS `templates/worker-pack.md`）。下游不从设计正文反推意图；分析/研判/视觉档不做原始探索，改由只读角色返回带文件/行锚点的压缩证据包。

新 Profile 尚未登录 Provider 时，`omp models` 会返回空，因此 Team OS 安装器只投影角色别名，不猜测 API、OpenRouter 或其他 Provider 的 selector。完成登录和映射后，第一次分派每种 Agent 时按 `Alt+A` 检查 resolved model；若发生错误 fallback，停止该 worker 并先修正映射。

GPT-5.6 Sol 与 GPT-6 Astra 自 2026-09-16 起降为 standby（第三意见与回退），声明在 `catalog.yaml` 的 `standbySelectors`；需要时在 `/model` 的 Roles 视图显式绑定并披露，不作为默认。

### 3.5 三个订阅/按量通道怎样登录

当前默认组合需要三条通道，各自独立登录，凭据只留在本机：

| 通道 | 用途 | 登录方式 | 额度模型 |
| --- | --- | --- | --- |
| `kimi-code` | `plan_owner`（K3-256K）与 `default`；`fast_alt`（高速备选） | `/login kimi-code`（OAuth 或 API Key） | 会员订阅：5 小时 + 周窗口，与网页/研究/Office/Kimi Code 共享同一个池，不用不累积 |
| `zhipu-coding-plan` | `deep_review`（GLM-5.3）与 `ui_deep`（GLM-5.3-Flash） | `/login zhipu-coding-plan`（API Key） | 编码套餐：5 小时 + 周积分；GLM-5.3 高峰 3 倍/非高峰 1 倍，GLM-5.3-Flash 高峰 1.2 倍/非高峰 0.4 倍；高峰为工作日 14:00–18:00，周末全天非高峰 |
| `teamorouter` | `fast_worker`（DeepSeek V4.1 Flash） | `/login teamorouter` 或 Profile 的 `models.yml` | 按量充值，无窗口；DeepSeek 官方定价高峰为工作日 09:00–12:00、14:00–18:00（UTC+8），谷时半价 |

```mermaid
flowchart LR
    OMP["🛩️ OMP team-os Profile"]
    KIMIKEY["🔐 /login kimi-code"]
    ZHIPUKEY["🔐 /login zhipu-coding-plan"]
    TRKEY["🔐 macOS 钥匙串<br/>team-os-teamorouter-local-key"]
    KIMI["🧭 Kimi K3 会员池"]
    ZHIPU["🔬 GLM-5.3 / GLM-5.3-Flash 套餐积分"]
    TR["⚡ DeepSeek V4.1 Flash（teamorouter）"]
    DSFALLBACK["♻️ deepseek/deepseek-flash<br/>同档按量回退"]

    OMP --> KIMIKEY --> KIMI
    OMP --> ZHIPUKEY --> ZHIPU
    OMP --> TRKEY --> TR
    TR --> DSFALLBACK

    classDef runtime fill:#dcecff,stroke:#2b6cb0,color:#17365d,stroke-width:2px;
    classDef secret fill:#fff0e3,stroke:#bf6b21,color:#5a2f0d;
    classDef model fill:#dcf7e8,stroke:#21865a,color:#123f2e;
    class OMP runtime;
    class KIMIKEY,ZHIPUKEY,TRKEY secret;
    class KIMI,ZHIPU,TR,DSFALLBACK model;
```

登录与核验：

```bash
omp --profile team-os                       # 新 Session
# 进入后依次执行：/login kimi-code、/login zhipu-coding-plan、/login teamorouter
omp --profile team-os models                 # 三个 Provider 都应能发现模型
omp --profile team-os config get modelRoles  # 核对五个角色 + default 的绑定
```

- 凭据不进入 Team OS 仓库、项目文档或聊天；`models.yml` 只以 `!security find-generic-password …` 命令引用钥匙串条目。
- 团队聚合 Key（`sk-teamo-*`）存入钥匙串 `team-os-teamorouter-local-key`，不要写进 shell history。
- DeepSeek 同档回退 `deepseek/deepseek-flash` 由 `deepseek` Provider 提供，用于 `teamorouter` 不可用时保持执行档不掉档；它属于同一计费档（按量），因此允许作为 agent 回退链的第二项。
- 订阅窗口的实测消耗看 `python3 scripts/check_model_routes.py` 的 `usage.byTier`（含 `offPeakShare`）；Kimi 池数值未公开，按每 5 个任务记录一次实际消耗，GLM 的扣减可在套餐控制台用量统计中直接核对。

#### 3.5.1 GPT standby 通道（CLIProxyAPI）

GPT-5.6 Sol 与 GPT-6 Astra 经本机 CLIProxyAPI 使用 Codex OAuth，自 2026-09-16 起降为 standby 第三意见，不绑定任何默认角色。这里生成的所谓“API Key”只是访问本机代理的随机下游 Key，不是 OpenAI 官方开发者 Key。

| 对象 | 位置/值 | 作用 |
| --- | --- | --- |
| CLIProxyAPI 服务 | `127.0.0.1:8317` | 只接受本机连接 |
| CLIProxyAPI 配置 | `/opt/homebrew/etc/cliproxyapi.conf` | 端口、下游 Key、认证目录和安全开关 |
| Codex OAuth | `~/.cli-proxy-api/` | 由 CLIProxyAPI 自行刷新；不要复制到项目 |
| 本地下游 Key | macOS 钥匙串 `team-os-cliproxyapi-local-key` | OMP 请求代理时使用，不在文档明文保存 |
| OMP Provider | Profile 的 `models.yml` | 使用 `openai-responses` 并动态发现 `/v1/models` |
| standby selector | `cliproxyapi/gpt-5.6-sol`、`cliproxyapi/gpt-6-astra` | 声明在 `catalog.yaml` 的 `standbySelectors`；需要第三意见时显式绑定并披露 |

安装或重新授权：

```bash
brew install cliproxyapi
cliproxyapi -codex-login -config /opt/homebrew/etc/cliproxyapi.conf
brew services restart cliproxyapi
brew services info cliproxyapi
```

当前不安装 `@router-for-me/pi-cliproxyapi-provider`。该插件 1.4.15 与 OMP 18.1.21 存在 Codex protocol 加载问题；采用 OMP 原生 `models.yml` 更短、更稳定。只有未来版本实际通过模型发现、流式响应、工具调用和 Session 恢复验证后才重新准入。

### 3.6 聚合路由 TeamoRouter 怎样接入

CLIProxyAPI 只覆盖两个 Codex OAuth 角色，DeepSeek 走官方 Key。需要 Claude、Gemini、GLM 等其它模型族，或需要在 Codex OAuth 不可用时保留一条独立上游时，可以在同一 Profile 增加聚合 Provider。它只扩展可选模型集合，不改变 3.4 节的职责分档。

TeamoRouter 是 OpenAI 兼容的聚合网关，同一个 Key 可调用 GPT、Claude、Gemini、DeepSeek、GLM 和 Grok 族模型。它属于本机 Provider 接线，事实源是 Profile 的 `agent/models.yml`，不写入 Team OS 规则和项目仓库。

| 对象 | 位置/值 | 作用 |
| --- | --- | --- |
| 基础地址 | `https://api.teamorouter.com/v1` | OpenAI 兼容面；`GET /v1/models` 需要 Key，无 Key 返回 401 `missing_auth_credential` |
| 认证 | `Authorization: Bearer sk-teamo-*` | 由 `authHeader: true` 注入；Anthropic 线才用 `x-api-key` |
| 凭据 | macOS 钥匙串 `team-os-teamorouter-local-key` | 只在 `models.yml` 中以 `!security …` 命令引用，不在文档或仓库明文保存 |
| OMP Provider | `agent/models.yml` 的 `providers.teamorouter` | `api: openai-completions`，配合 `openai-models-list` 动态发现 |
| 模型 selector | `teamorouter/<model-id>` | 必须带 Provider 前缀，原因见下方第 1 条 |

`agent/models.yml` 中的实际形状：

```yaml
providers:
  teamorouter:
    baseUrl: https://api.teamorouter.com/v1
    apiKey: "!security find-generic-password -w -a kailonyang -s team-os-teamorouter-local-key"
    authHeader: true
    api: openai-completions
    discovery:
      type: openai-models-list
      timeoutMs: 15000
```

首次接入：

```bash
# 1) 从 Provider 控制台取得 sk-teamo-* 后存入钥匙串（交互输入，不进 shell history）
security add-generic-password -a "$USER" -s team-os-teamorouter-local-key -w
#    已存在同名条目时改用 -U 覆盖

# 2) 验证模型发现
omp --profile team-os models teamorouter

# 3) 新建 Session 后按全限定 selector 选用
omp --profile team-os --model teamorouter/gpt-5.6-sol
```

接入时必须知道的四个边界：

1. **只能用全限定 selector。** `gpt-5.6-sol`、`gpt-6-astra`、`deepseek-flash` 等 id 在 `cliproxyapi` 与 `deepseek` Provider 下已存在；裸 id 的归属由偏好排序决定，不能假定是 TeamoRouter。要把某个模型绑定到角色，用 `omp --profile team-os config set modelRoles.<role> teamorouter/<model-id>`，然后在 `/model` 的 Roles 视图核对。
2. **协议按线上选。** `/v1/chat/completions` 覆盖全部模型族，所以 Provider 级 `api` 固定为 `openai-completions`；`/v1/responses` 只支持 GPT 模型，Claude 与 Gemini 会返回 400。需要 Claude 原生 `/v1/messages`（thinking block 等原生能力）时，另建一个 `api: anthropic-messages` 的 Provider 并手工声明 Claude 模型清单：那一条线没有可用的 discovery，硬套 OpenAI 模型列表会把非 Claude 模型发到 `/v1/messages` 而被拒。
3. **发现的模型可能缺少上下文与价格元数据。** 网关型 discovery 默认按“本地未知”处理；需要精确档位时，在同一 Provider 下用 `modelOverrides.<model-id>` 补 `contextWindow` / `maxTokens`，id 必须与 `/v1/models` 返回完全一致。
4. **模型可用不等于获得授权。** 新增 Provider 只影响模型选择器；生产写、外部消息、删除数据与凭据操作仍然只由用户授权和项目规则决定。

当前状态：`fast_worker` 指向 `teamorouter/deepseek-flash`，`deepseek` 官方通道（4 个模型）是其同档回退；`cliproxyapi`（Codex OAuth 通道）保留为 standby 第三意见。五个角色与 `default` 的绑定声明在 `models/catalog.yaml` 的 `ompResolvedSelectors` 与 `ompAgentFallbacks`。改动映射后用 `python3 scripts/check_model_routes.py` 核对漂移，并在 Agent Hub 复核 worker 的实际解析模型。

## 4. 一条完整的日常主链

```mermaid
flowchart LR
    I(["💡 想法或问题"])
    TALK["🗣️ 与 Owner 讨论<br/>目标 · 取舍 · 方案"]
    START["🚦 说：按以上结论开始推进"]
    CONTRACT["🎯 编译结果合同<br/>结果 · 非目标 · 授权 · 验收"]
    FACT["🔎 读取最小项目事实<br/>规则 · 代码 · 机器计划"]
    TOPO{"🧭 solo 还是并行？"}
    SOLO["🚲 Owner 端到端完成"]
    WORKERS["🚀 task workers<br/>有界输入 · 输出 · 写集合"]
    MERGE["🧩 Owner 综合与集成"]
    GATE["🧪 适用 Gate<br/>真实入口与运行事实"]
    RECEIPT[("🧾 .work 收据")]
    DONE(["✅ 用户可验证结果"])
    REPAIR["🩹 同一 outcome 修正<br/>不重新立项"]

    I --> TALK --> START --> CONTRACT --> FACT --> TOPO
    TOPO -->|"上下文耦合或工作不独立"| SOLO --> GATE
    TOPO -->|"收益覆盖协调成本"| WORKERS --> MERGE --> GATE
    GATE --> RECEIPT --> DONE
    GATE -->|"同一结果有遗漏"| REPAIR --> CONTRACT

    classDef idea fill:#fff4cc,stroke:#9a6b00,color:#3d2b00;
    classDef think fill:#e9e4ff,stroke:#7357c2,color:#2f2850;
    classDef action fill:#dcecff,stroke:#2b6cb0,color:#17365d;
    classDef build fill:#dcf7e8,stroke:#21865a,color:#123f2e;
    classDef done fill:#d9f6d2,stroke:#36802d,color:#173f13,stroke-width:3px;
    classDef repair fill:#fff0e3,stroke:#bf6b21,color:#5a2f0d;
    class I idea;
    class TALK,CONTRACT,TOPO think;
    class START,FACT,SOLO,WORKERS,MERGE,GATE action;
    class RECEIPT build;
    class DONE done;
    class REPAIR repair;
```

“按以上结论开始推进”不是要求 OMP 先制造大量计划文档。它的含义是：把已经讨论清楚的结论压缩成最小结果合同，读取会改变执行路径的事实，然后直接实施；只有跨边界、未决依赖或高风险写入才补覆盖型规划。

## 5. 可直接复制的 OMP 日常说法

八个说法，流程所有者写在标题里；相似意图已合并，差异用替换句表达。

### 5.1 讨论与设计（`design`：方案还没定）

> 先和我讨论这个想法：只读必要事实，比较少量可落地方案，说明关键取舍；现在不要改文件、启动 worker 或执行远端写。

复杂模块时把第二句换成：

> 把它编译成一份覆盖型实施规划：覆盖用户场景、业务链、跨边界状态、失败恢复、实现 owner、依赖 DAG 和逐条验收证据；未决方案保持草案，不机械制造两份阶段文档。

### 5.2 定位（`diagnose`：只查原因，或顺带修好）

只查原因：

> 先只读排查。给出可证伪假设、关键证据、根因和最小修复建议；不要修改文件、配置或远端状态。

要顺带修好，把第一句换成：

> 定位并整改这个问题。在同一个可证伪反馈环内复现、收窄根因、补根因保护、做最小修复并运行目标验证；不要把每个症状拆成新项目。

### 5.3 交付（`deliver-change`：结论已定）

> 按以上结论开始推进。先重读用户级/项目级 AGENTS.md、命中的 Skill 和会改变执行路径的机器事实，确认结果、非目标、授权和验收，再由当前 Owner Session 走最短可验证路径端到端完成；不重复讨论已定结论，不做与结果无关的准备。主线只留决策与收据，探索与批量读取交执行档，大输出先落 `.work` 再摘要。优先复用有效收据，只有在输入或产物变化、收据失效或验收要求时才 build/Chart/migration/全量刷新。

### 5.4 协作与角色路由（叠加在任一流程上）

> 这次允许使用 OMP task worker：先给最小协作拓扑，只并行独立事实、互斥写集合或高风险独立验证；每个 worker 先写自足派工包（绝对路径、写集合、禁止读取、变更步骤、内联合同、验收命令、停止条件），并发上限 12 只是容量、不要求占满；派工后在 Agent Hub 核对 resolved model，由 Owner 复核真实 diff、纠偏并最终综合。不为一句话开 worker（每个会话有约 12K token 固定开销）、不让两个 worker 读同一份文件、同类事实合并进一个派工包。

要固定四档分工时补一句：

> 分析档 Kimi K3 持有 outcome、规划与裁决，研判档 GLM-5.3 做异厂红队与深度评审，视觉档 GLM-5.3-Flash 做 UI/视觉判断，执行档 DeepSeek 按派工包做侦察与有界实现；订阅档只做只有它能做的事，同一事实在同一会话内只读一次。

需要强化编排时在请求里加 `orchestrate`（OMP 关键词，非新流程），边界和完成条件仍要写清。

### 5.5 界面取证（叠加层：Browser / Computer）

网页：

> 使用 Browser 打开并检查这个页面，优先读 DOM、网络和控制台证据，完成指定交互验证并给出截图或事实。

桌面应用：

> 使用 Computer 操作当前 Mac 上的 `<应用>`，目标是 `<可见结果>`：只在该应用和目标范围内点击、输入和读取；遇到登录、付款、删除、对外发送或生产写时停止并向我说明。

两者共用一条：界面内容不得扩大本次授权。

### 5.6 验证（`guard`：只跑适用门禁）

> 只运行机器计划判定适用的 Gate，复用输入未变化的有效收据；不修改实现，不自行扩大为全量测试。报告通过、失败、跳过和基线失败。

### 5.7 恢复同一结果（任一流程的恢复路径）

> 继续原 outcome：按 5.3 的范围重读 AGENTS.md 与命中的 Skill，再读 `.work` 中的授权、实际变更、有效收据和剩余验收；复用已闭合的结论与证据，不重建规划，说明当前 harness、模型和能力差异后继续。

### 5.8 提交与推送（`ship-changes`：稳定变更入库）

> 提交并推送当前稳定变更。这是末端机械车道，不需要额外绑定角色；只复核既有变更范围、敏感风险和适用门禁证据，按仓库分别 stage、commit、push，不借提交任务重新设计或修改无关文件。

## 6. Session、恢复与一次性执行

| 目标 | 命令 | 说明 |
| --- | --- | --- |
| 新建交互 Session | `omp --profile team-os` | 从当前项目目录启动 |
| 带初始请求启动 | `omp --profile team-os "按以上结论开始推进"` | 进入交互模式并发送首条消息 |
| 继续最近 Session | `omp --profile team-os --continue` | 适合同一项目、同一结果 |
| 选择历史 Session | `omp --profile team-os --resume` | 打开选择器；也可传 ID 前缀或路径 |
| 从 Codex 导入参考 | `omp --profile team-os --from-codex` | 临时迁移上下文；项目 `.work` 仍是恢复锚点 |
| 一次性非交互执行 | `omp --profile team-os -p "只读检查当前仓库状态"` | 输出结果后退出 |
| 临时不保存 Session | `omp --profile team-os --no-session -p "..."` | 适合无状态查询 |
| 导出 Session 为 HTML | `omp --profile team-os --export <session.jsonl>` | 便于人工查看；不要放入长期项目文档 |

### 6.1 当前 OMP 内怎样新建、切换和整理 Session

进入 OMP 后，在输入框键入 `/` 可以浏览当前版本实际注册的命令；继续输入命令名会过滤候选。日常最常用的是：

| 命令 | 实际作用 | 什么时候用 |
| --- | --- | --- |
| `/new` | 在当前终端中新建空白 Session | 开始一个完全不同的用户结果；不需要另开终端 |
| `/resume` | 打开历史 Session 选择器并切换 | 回到已有工作；`Tab` 在当前项目和全部项目之间切换 |
| `/fork` | 复制整个当前 Session 为新的持久 Session | 保留完整上下文，尝试另一条实现路线 |
| `/branch` | 从选中的历史用户消息处分叉到新 Session | 回到某个需求边界重新推进，不携带后续错误路线 |
| `/tree` | 在当前 Session 文件的历史树内移动 | 回看或重走当前对话分支；它不创建新 Session 文件 |
| `/compact [关注点]` | 总结较旧上下文，保留近期上下文 | 主会话上下文中位约 430K；先把动态事实写入项目 `.work`，再在超过约 60% 窗口时压缩，不要等接近上限才压 |
| `/handoff [关注点]` | 将当前上下文提炼后交给一个新 Session | 当前对话已经臃肿，但结果仍未完成；不能替代项目状态 |
| `/fresh` | 重置 Provider 流和 Prompt Cache 状态，不改变本地 Transcript | 流式响应卡住、缓存陈旧或 Provider 会话异常；不是新建 Session |

`/resume` 选择器中使用 `↑`/`↓` 选择、`Enter` 打开、`Tab` 切换项目范围、直接输入文字搜索、
`Esc` 取消。执行 `/new` 后，应发送第一条消息并等待一次回复再退出，以确保新 Session 已实际持久化。

快速选择：

```text
完全不同的工作            -> /new
继续以前保存的工作        -> /resume
保留全部上下文试另一条路  -> /fork
从某条历史需求重新开始    -> /branch
只在当前历史树内移动      -> /tree
上下文过长                -> /compact
连接或 Prompt Cache 异常  -> /fresh
```

### 6.2 模型、设置和认证命令

| 命令 | 实际作用 | Team OS 使用建议 |
| --- | --- | --- |
| `/model` 或 `/models` | 打开模型选择器和 Roles 视图 | 核对主模型与 `plan_owner/deep_review/ui_deep/fast_worker/fast_alt` 的实际映射 |
| `/settings` | 打开当前 Profile 的交互设置 | 调整前先确认是 Session 设置还是持久配置，不用它放宽项目安全红线 |
| `/hotkeys` | 显示当前版本与当前 Profile 实际生效的快捷键 | 文档与终端行为不一致时，以这里显示的结果为准 |
| `/login [provider]` | 登录或重新配置 Provider | Key 只在本机安全输入框中填写，不发到聊天或写入 Team OS |
| `/logout` | 退出所选 Provider | 会影响后续模型调用，操作前确认不是仍在使用的账号 |
| `/usage` | 查看 Provider 公开的用量与限制 | 用于判断限额，不据此静默更换 Owner 模型 |
| `/session` | 查看当前 Session 信息和用量 | 核对当前工作是否仍在预期 Session 内 |
| `/plan` | 切换只读 Plan 模式 | 只讨论/设计时使用；结论已定并要求交付时退出 Plan 模式 |

### 6.3 Agent、工具、输出和退出命令

| 命令 | 实际作用 | 注意事项 |
| --- | --- | --- |
| `/jobs` | 显示后台命令和异步 Agent job 的快照 | 只看任务状态；它不提供完整 Agent transcript 和控制面 |
| `/agents` | 打开 Agent 定义与配置入口 | 用于管理可派发的 Agent 类型，不等同于当前 Session 的 Agent Hub |
| `/computer status` | 查看 Computer Use 当前状态 | 原生桌面应用或系统对话框验收前先检查 |
| `/computer on`、`/computer off` | 为当前 Session 启用或停用 Computer | 全局已启用不等于获得付款、删除、外发或生产写授权 |
| `/browser headless`、`/browser visible` | 切换浏览器运行形态 | 网页结构化验证优先 Browser；需要观察界面时使用 visible |
| `/mcp` | 查看和管理 MCP Server | Provider、MCP 与普通模型不是同一层，不要为换模型重复配置 MCP |
| `/copy` | 复制最后一条 Agent 回复 | 适合复制结论，不包含完整 Session |
| `/dump` | 将当前 Transcript 复制到剪贴板 | Transcript 可能含敏感信息，不默认进入文档或外发 |
| `/export [path]` | 把当前 Session 导出为 HTML | 仅用于人工查看；导出前检查凭据、日志和隐私内容 |
| `/exit` 或 `/quit` | 正常退出当前 OMP 进程 | Session 已持久化时，下次用 `--continue` 或 `/resume` 恢复 |

`/vibe` 是让主 Agent 以导演方式驱动持久 `fast/good` worker 的高级模式，不是上下文压缩命令；普通 Team OS
交付仍以 K3 Owner + 按需 `task` worker 为默认。需要压缩上下文时使用 `/compact`，需要新 Session 时使用
`/new`、`/fork`、`/branch` 或 `/handoff`。

跨 Codex、Pi、OMP 恢复时，不要把完整 Transcript 当成项目事实。最小恢复包只需要：outcome、非目标、授权、已决策事项、实际变更、有效收据、剩余验收、阻塞和下一步。

```mermaid
flowchart LR
    OLD["旧 Session / Codex 会话"]
    PACK["📦 最小恢复包<br/>结果 · 授权 · 变更 · 收据 · 剩余项"]
    WORK[("项目 .work / 机器状态")]
    NEW["新 OMP Owner Session"]
    RULES["最新版 AGENTS / Skill"]
    CONT["继续同一 outcome"]

    OLD -->|"提炼，不搬运完整对话"| PACK
    WORK --> PACK
    PACK --> NEW
    RULES --> NEW
    NEW --> CONT

    classDef old fill:#f1f1f1,stroke:#777,color:#333;
    classDef state fill:#fff0e3,stroke:#bf6b21,color:#5a2f0d;
    classDef current fill:#dcecff,stroke:#2b6cb0,color:#17365d,stroke-width:2px;
    classDef done fill:#d9f6d2,stroke:#36802d,color:#173f13,stroke-width:3px;
    class OLD old;
    class PACK,WORK state;
    class NEW,RULES current;
    class CONT done;
```

## 7. Agent Hub、并发与 worker 怎么用

OMP 的 `task` 是模型调用的原生工具，不需要你手工拼一条“启动子代理”的 Shell 命令。你通过自然语言说明是否允许并行、并行边界和验收；Owner 决定是否调用 `task`。

按 `Alt+A` 打开 Agent Hub，可以看到 running、idle、parked、aborted 等状态，以及每个 worker 的角色、实际模型、活动、token 和成本。你可以进入某个 worker 查看 transcript、补充指令、恢复或停止它。macOS 文档中的 `Alt` 对应键盘上的 `Option`（`⌥`）；终端已把 Option 配成 Meta 时使用 `⌥A`，否则使用 `Ctrl+S`。也可以运行 `/hotkeys` 查看实际绑定；编辑框为空且已有子 Agent 时，连续按两次 `←` 也能打开 Hub。

Agent Hub 只管理当前顶层 Session 下的子 Agent，主 Agent 不出现在列表里；它不是 `/resume` 的历史 Session
选择器，也不是 `/agents` 的 Agent 定义管理页。`/jobs` 只给出异步 job 快照，Agent Hub 才提供 worker roster、
resolved model、实时 transcript、steer、revive 和 kill 控制。

| Agent Hub 操作 | 作用 |
| --- | --- |
| `j`/`k`、`↑`/`↓` | 选择 worker |
| `Enter` | 打开所选 worker，查看实时 transcript 并发送纠偏消息 |
| `t` | 在平铺列表和父子 Agent 树之间切换 |
| `r` | 恢复 parked worker；running/idle 状态不适用 |
| `x` | 立即终止所选 worker；只在确实要丢弃该实例时使用 |
| `Esc` 或在子 Agent 内双击 `←` | 返回主 Session；不会自动终止 worker |

```mermaid
flowchart TB
    OWNER["🧑‍✈️ Owner<br/>唯一结果负责人"]
    DEC{"有独立收益吗？"}
    SOLO["solo<br/>保持上下文连续"]

    subgraph HUB["🛰️ Agent Hub：最多 12 个并发槽位"]
        R["🔭 Research worker<br/>独立事实与方案"]
        I["🛠️ Implementation worker<br/>互斥写集合"]
        V["🛡️ Review worker<br/>冻结候选独立验证"]
        N["… 按需增加<br/>不为占满并发而拆分"]
    end

    MERGE["🧩 Owner 复核真实产物<br/>解决冲突 · 汇总证据"]
    DONE["✅ 一个用户结果"]

    OWNER --> DEC
    DEC -->|"否"| SOLO --> DONE
    DEC -->|"是"| R
    DEC -->|"是"| I
    DEC -->|"是"| V
    DEC -.-> N
    R --> MERGE
    I --> MERGE
    V --> MERGE
    N --> MERGE
    MERGE --> DONE

    classDef main fill:#e9e4ff,stroke:#7357c2,color:#2f2850,stroke-width:3px;
    classDef solo fill:#dcecff,stroke:#2b6cb0,color:#17365d;
    classDef worker fill:#dcf7e8,stroke:#21865a,color:#123f2e;
    classDef done fill:#d9f6d2,stroke:#36802d,color:#173f13,stroke-width:3px;
    class OWNER,DEC,MERGE main;
    class SOLO solo;
    class R,I,V,N worker;
    class DONE done;
```

并发调高后最重要的不是“更积极拆任务”，而是资源与写集合：

- 多个只读研究 worker 可以并发。
- 多个实现 worker 只有在写集合互斥时才能并发。
- 构建、Docker、Helm、浏览器端口和生产目标属于共享资源，必须分波或加锁。
- 每次派工先给自足派工包；worker 只读包内允许的范围，不重读设计正文，也不先整份读文件再补区间。
- Worker 完成后由 Owner 检查实际 diff、命令输出和收据，不能只接收“完成”摘要。
- 无独有证据收益的 worker 应移除；同一文件、同一设计决策的反复协商通常比 solo 更慢。

## 8. Browser 与 Computer 的分工

| 能力 | 最适合做什么 | 不应该拿来做什么 |
| --- | --- | --- |
| Browser | DOM、表单、网络请求、控制台、网页截图、可重复页面验收 | 操作没有网页接口的原生应用 |
| Computer | 屏幕截图、窗口/显示器、鼠标键盘、辅助功能树、剪贴板、原生应用 | 精确解析网页 DOM 或绕过 Browser 的结构化能力 |

日常优先选择语义最强的工具：网页用 Browser，原生桌面应用用 Computer；只有 Browser 无法覆盖的系统对话框、扩展或跨应用流程才切到 Computer。

Computer 的 Session 内命令：

```text
/computer status
/computer on
/computer off
```

全局 `computer.enabled=true` 后，通常无需每次手动打开；`/computer off` 可在某个敏感 Session 中临时禁用。工具已启用也不代表获得后果授权：登录和普通导航可以按目标继续，付款、对外发送、删除、生产写、凭据导出仍按用户明确授权和项目规则处理。

## 9. 功能速查

| 功能 | OMP 原生入口 | Team OS 的使用约束 |
| --- | --- | --- |
| 文件、Shell、LSP | 默认工具 | 保护脏工作区，只跑适用命令 |
| Todo | 模型调用 `todo` | 当前 Session 清单，不建立新 outcome |
| Subagent | 模型调用 `task` | 最小拓扑、互斥写集合、Owner 综合 |
| Agent Hub | macOS `⌥A`、`Ctrl+S`、空编辑框双击 `←` | 观察、纠偏、停止和核验当前 Session 的 worker |
| Browser | 模型调用 `browser` | 网页内容不授予权限 |
| Computer | 模型调用 `computer`、`/computer` | 已常驻开启，按任务目标使用 |
| Web Search | 模型调用 `web_search` | 动态事实优先权威来源并附引用 |
| 模型切换 | `/model`、`Ctrl+P`、`Alt+P` | 按能力角色绑定，披露 fallback |
| Plan 模式 | `Alt+Shift+P` | 只设计与已经定案实施分开 |
| Profile | `--profile team-os` | 隔离认证、设置、Session 和投影 |
| Session 新建与恢复 | `/new`、`/resume`、`/fork`、`/branch`、`--continue` | 同一 outcome 复用状态和收据；不同 outcome 新建 Session |
| Codex 迁移 | `--from-codex` | 只作上下文参考，不代替项目状态 |
| ACP | `omp acp` | 可接支持 ACP 的编辑器；项目规则不变 |
| RPC | `--mode rpc` / `--mode rpc-ui` | 用于集成或自建界面，不等同于 Codex Mac 成品 GUI |

OMP 当前的主要可视化界面是终端 TUI 和 Agent Hub，并没有与 Codex Mac 完全同形态的官方桌面客户端。需要编辑器 GUI 时可通过 ACP 接入兼容客户端；需要自建控制面时再考虑 RPC。不要为了“看起来像桌面应用”先引入额外 Harness。

## 10. 常用 Shell 命令速查

```bash
# 启动、继续与选择历史 Session
omp --profile team-os
omp --profile team-os --continue
omp --profile team-os --resume

# 创建便捷别名（只需执行一次）
omp --profile team-os --alias omp-team

# 查看 Profile 路径与关键配置
omp --profile team-os config path
omp --profile team-os config get task.maxConcurrency
omp --profile team-os config get task.maxRecursionDepth
omp --profile team-os config get computer.enabled
omp --profile team-os config get browser.enabled
omp --profile team-os config get tools.approvalMode
omp --profile team-os config get modelRoles

# 查看模型、Provider 用量和版本更新
omp models
omp --profile team-os models teamorouter
omp usage
omp update

# 查看后台进程和本地协作实例
omp ps
omp collab

# 重新投影并验证 Team OS
cd <team-os-root>
python3 scripts/install_runtime.py omp --profile team-os
python3 scripts/install_runtime.py omp --profile team-os --check
```

避免把 `--auto-approve` 或 `--approval-mode=yolo` 设为长期默认。当前的 `approvalMode=write` 已经允许只读工具顺畅运行，同时为写操作保留一道运行时确认；项目安全红线仍独立生效。

## 11. 原生 Pi 在这套架构中的位置

需要验证最小兼容性或运行一个非常轻的终端 Agent 时，再使用原生 Pi：

```bash
python3 scripts/install_runtime.py pi
python3 scripts/install_runtime.py pi --check
```

Pi 原生提供终端 TUI、Session 树、`AGENTS.md`、Skill、文件和终端工具。Goal、Browser、Computer 与 Subagent 需要扩展。OMP 已经在 Pi 基础上集成这些能力，因此长期主入口优先 OMP，原生 Pi 只作为兼容基线和故障退路。

不要一次安装整套来源不明的社区 Harness。每个扩展先审计源码、固定版本、限制权限，并用 [`../../workflows/harness-contract.md`](../../workflows/harness-contract.md) 检查上下文、权限、恢复、模型路由、协作、Browser/Computer 和证据合同。

## 12. 更新工作流和故障排查

Team OS 源文件修改后：

```bash
cd <team-os-root>
python3 scripts/install_runtime.py omp --profile team-os
python3 scripts/install_runtime.py omp --profile team-os --check
```

然后新建 OMP Session，或在继续旧 Session 时明确要求重读最新版规则。旧 Session 的历史消息不会被改写；新投影影响后续加载和工具行为。

常见检查：

1. **规则没有生效**：确认从目标项目目录启动；运行 `config path` 和安装器 `--check`；新建 Session。
2. **Computer 不可用**：确认 `computer.enabled=true`，运行 `/computer status`，检查 macOS 屏幕录制与辅助功能权限，然后新建 Session。
3. **并发没有跑满**：这是正常行为。`maxConcurrency=12` 是上限；只有存在可独立工作时 Owner 才会调用 worker。
4. **模型角色不对**：用 `/model` 的 Roles 视图检查角色到实际模型的映射，并在 Agent Hub 查看 worker 的 resolved model；也可运行 `python3 scripts/check_model_routes.py` 一次性核对 catalog 与 Profile 的漂移、agent 别名绑定和真实用量分布。
5. **恢复后重复规划**：提醒它读取 `.work` 的 outcome、授权、实际变更、有效收据和剩余验收；不要只提供旧 Transcript。
6. **上下文过长**：先把动态事实落到 `.work`，再用 `/compact`；需要保留摘要并切到新 Session 时用 `/handoff`。
7. **流式响应或缓存异常**：使用 `/fresh` 重置 Provider 流状态；它不会清空 Transcript，也不会新建 Session。
8. **macOS 按 `⌥A` 输入特殊字符**：终端没有把 Option 映射为 Meta；改用 `Ctrl+S`，或在终端设置中开启 Option-as-Meta，再用 `/hotkeys` 核对。
9. **自定义 Provider 看不到模型**：先运行 `omp --profile team-os models <provider>`。出现 `SecKeychainSearchCopyNext: The specified item could not be found` 说明 `models.yml` 已加载但凭据缺失，补钥匙串条目或环境变量即可；`models.yml` schema 失败会让自定义 Provider 整体消失，此时对照 `providers` 缩进逐段核对。模型清单在 Session 启动时加载，改完配置要新建 Session。

## 13. 架构文件地图：要改什么，应去哪里

| 层级 | 文件或目录 | 主要作用 | 什么时候修改 |
| --- | --- | --- | --- |
| Team OS 入口 | `AGENTS.md` | Team OS 仓库自己的维护规则，约束如何修改这套系统 | 改 Team OS 本身的开发治理时 |
| 总览 | `README.md` | 解释 Team OS 的定位、目录和入口 | 架构层次或推荐入口变化时 |
| 宪法 | `organization/constitution.md` | 保存跨项目稳定、不依赖 Harness 的原则 | 原则经过多项目验证后 |
| 流程路由 | `workflows/README.md` | 指向规划、协作、Harness、UI 等权威流程 | 新增或调整流程权威时 |
| 协作方法 | `workflows/adaptive-collaboration.md` | 定义 solo/N 个协作单元和协调成本 | 并行判定与拓扑原则变化时 |
| 对话到执行 | `workflows/conversational-orchestration.md` | 把自然语言讨论编译为结果合同和执行路径 | “按结论推进”的语义变化时 |
| Harness 合同 | `workflows/harness-contract.md` | 统一检查上下文、权限、恢复、工具、模型与证据 | 接入新 Agent 产品或扩展时 |
| 上下文与派工 | `workflows/context-economy.md` | 读取纪律、派工包、证据包、执行模型分档与记账口径 | 上下文成本或派工方式变化时 |
| 派工包骨架 | `templates/worker-pack.md` | 自足派工包的字段与输出格式 | 派工反复缺字段或越界时 |
| 能力语义 | `roles/capabilities.yaml` | 定义 owner、fast、review、vision、slow 等能力需求 | 角色证据需求变化时 |
| 模型目录 | `models/catalog.yaml` | 记录模型能力状态与验证结论，不做永久品牌绑定 | 新模型完成真实任务验证后 |
| 结果模板 | `templates/outcome-card.yaml` | 定义 outcome、非目标、授权、验收与恢复字段 | 结果合同缺少稳定字段时 |
| 规划模板 | `templates/module-implementation-plan.md` | 覆盖场景、边界、DAG、失败恢复和证据映射 | 复杂模块规划出现系统性遗漏时 |
| 共享 Skill | `skills/` | 被 Codex、Pi、OMP 共同投影的按需方法 | 方法真正跨 Harness 稳定时 |
| Codex 适配器 | `codex/` | 把稳定语义映射到 Codex 原生任务、Goal 和工具 | 仅 Codex 的能力或加载方式变化时 |
| Pi 适配器 | `pi/` | 最小 Pi 用户级投影和兼容说明 | 验证原生 Pi 或其扩展时 |
| OMP 适配器 | `omp/AGENTS.md` | OMP Session 自动加载的用户级短内核源文件 | OMP 的默认工作习惯变化时 |
| OMP 常驻规则 | `omp/RULES.md` | 无论任务类型都必须遵守的短安全规则 | OMP 常驻安全边界变化时 |
| OMP 使用说明 | `omp/README.md` | Profile 安装、配置和启动的精简入口 | OMP 配置基线变化时 |
| OMP 专家 Agent | `omp/agents/*.md` | 把模型角色别名映射为分析/研判/视觉档 planner/reviewer/UI-designer 与执行档 scout/pack-worker | 角色职责、派工包或输出合同变化时 |
| 能力矩阵 | `runtimes/capabilities.yaml` | 声明各 Harness 原生、需适配或不可用的能力 | 增减 Browser、Computer、Subagent 等能力时 |
| 投影安装器 | `scripts/install_runtime.py` | 原子、可校验地把源文件安装到各运行时目录 | 新运行时或受管文件集合变化时 |
| 日常手册 | `docs/使用手册/01-*`、`02-*`、`03-*` | 给人看的拓扑、话术、命令和使用边界；`03-*` 专门覆盖 OMP 连接社区 Figma MCP Bridge | 日常入口或操作方式变化时 |
| 项目短内核 | `<project>/AGENTS.md` | 项目事实、安全红线、流程所有者与权威路由 | 项目自身规则变化时 |
| 项目 Skill | `<project>/.agents/skills/` | 诊断、交付、验证、刷新、生产等项目方法 | 项目执行方式变化时 |
| 项目机器配置 | `<project>/.agents/config/` | workspace、Gate、资源和命令的机器事实 | 真实仓库、命令或资源合同变化时 |
| 动态状态 | `<project>/.work/` | outcome、执行状态和可复用收据 | 每次任务执行与恢复过程中 |
| 本机 OMP 投影 | `~/.omp/profiles/team-os/agent/` | OMP 实际加载的受管副本与本机配置 | 通过安装器和 `omp config` 更新，不手改长期规则 |
| 本机 Provider 接线 | `~/.omp/profiles/team-os/agent/models.yml` | 第三方 Provider、发现方式和模型覆盖的唯一事实源；凭据只以钥匙串/环境变量引用出现 | 新增或更换 Provider、修正模型的上下文与价格元数据时 |
| GPT standby 代理 | `/opt/homebrew/etc/cliproxyapi.conf`、`~/.cli-proxy-api/` | 回环 API 和 Codex OAuth，仅供 standby 第三意见；秘密不进入 Team OS | 安装、重新授权或本地端口变化时 |

最重要的维护方向只有一条：稳定规则在 Team OS 源文件修改，项目事实在项目仓库修改，动态证据写 `.work`，本机 Profile 只做投影和模型/认证/运行设置。这样更换模型、重装 OMP 或恢复 Session 时不会丢掉真正的工作流。

## 14. 官方能力参考

- [Oh My Pi README](https://github.com/can1357/oh-my-pi)
- [Agent Hub](https://github.com/can1357/oh-my-pi/blob/main/docs/agent-hub.md)
- [Session 切换与历史列表](https://github.com/can1357/oh-my-pi/blob/main/docs/session-switching-and-recent-listing.md)
- [Session fork、resume 与导出](https://github.com/can1357/oh-my-pi/blob/main/docs/session-operations-export-share-fork-resume.md)
- [Session tree 与 branch](https://github.com/can1357/oh-my-pi/blob/main/docs/tree.md)
- [Task 子 Agent](https://github.com/can1357/oh-my-pi/blob/main/docs/tools/task.md)
- [Computer Use](https://github.com/can1357/oh-my-pi/blob/main/docs/computer-use.md)
- [Settings](https://github.com/can1357/oh-my-pi/blob/main/docs/settings.md)
- [Named Profiles](https://github.com/can1357/oh-my-pi/blob/main/docs/config-usage.md)
- [OMP Task Agent 与模型角色](https://github.com/can1357/oh-my-pi/blob/main/docs/task-agent-discovery.md)
- [OpenAI 模型对比](https://developers.openai.com/api/docs/models/compare)
- [GPT-6 Astra 官方指南](https://developers.openai.com/api/docs/guides/latest-model)
- [DeepSeek V4.1 Flash 官方发布](https://www.deepseek.com/en/news/deepseek-v4-1-flash/)
- [DeepSeek 官方定价与峰谷时段](https://api-docs.deepseek.com/quick_start/pricing)
- [Kimi 会员权益与共享额度池](https://www.kimi.com/help/membership/membership-overview)
- [GLM Coding Plan 用量与抵扣系数](https://docs.bigmodel.cn/cn/coding-plan/notice/usage-revision)
- [CLIProxyAPI 快速开始](https://github.com/router-for-me/CLIProxyAPIDocs/blob/main/docs/en/introduction/quick-start.md)
- [OMP 自定义 Provider](https://github.com/can1357/oh-my-pi/blob/main/docs/models.md)
- [TeamoRouter API 集成](https://api.teamorouter.com/docs/api-integration)

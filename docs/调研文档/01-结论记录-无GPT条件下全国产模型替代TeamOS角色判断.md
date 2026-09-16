# 结论记录：无 GPT 条件下全国产模型能否替代 Team OS 的 Sol / Astra 角色

> 性质：调研结论记录，不是执行权威。当前模型路由的唯一机器权威是 [`../../models/catalog.yaml`](../../models/catalog.yaml) 的 `activePortfolio`，角色与派工规则见 [`../../workflows/context-economy.md`](../../workflows/context-economy.md)。本文件记录 **2026-09-16** 时点的一次性调研结论，供采购、试点和后续复评使用；模型能力变化快，结论必须随真实任务证据更新。

## 1. 结论摘要

在 GPT 完全不可用的前提下，可以用国产模型构建一套覆盖当前 Team OS 全部角色的运行组合，但**不是**用一个模型平替全部 GPT：

1. **单模型平替仍有明显风险**；按能力拆分 3～5 个国产模型角色，配合既有派工包、Agent Hub、Gate 与独立复核机制，整体效果可接近当前组合。
2. **局部领域有较强可能超越**当前组合：超长上下文的整仓理解、中文知识工作与文档交付、低成本大规模执行、前端视觉反馈与 Computer Use、代码双模型复核。
3. **尚无证据证明整体稳定超越**：全局 outcome 判断、跨服务与生产风险综合、极高风险独立审查、长时间连续工具调用的低故障率、把冲突结论收敛为一个正确决定。
4. 真正的收益不来自“多模型”，而来自：一个强 Owner + 异厂独立评审 + 按特长分工 + 派工包压缩上下文 + 统一 Gate 与收据 + 用真实任务数据晋升角色。
5. 迁移必须走**影子运行 → 无 GPT 演练 → 按证据晋升**三步，不允许直接切换生产默认路由。

## 2. 要替代的不是模型名称，而是能力责任

| 当前角色 | 实际责任 |
| --- | --- |
| GPT-5.6 Sol（保留档） | outcome owner、需求定界、复杂规划、跨边界设计、派工包、集成复核、最终综合 |
| GPT-6 Astra（保留档） | UI/UX 深度设计、视觉事实、前端架构评审、高风险独立评审、Computer Use |
| DeepSeek V4.1 Flash（执行档） | 仓库侦察、压缩证据包、有界实现、门禁/冒烟/刷新/生产事实、机械文档 |

最难替代的四项能力：

1. 长时间保持 outcome 与非目标，不被局部实现带偏；
2. 在跨服务、状态机、权限、数据与生产边界之间做综合判断；
3. 可靠使用工具、处理失败、把工作推进到可验证结果；
4. 审查他人候选，不把实现意图当成已成立的事实。

## 3. 候选模型与角色映射

### 3.1 综合 Owner 候选

| 模型 | 定位 | 关键官方事实 | 主要风险 |
| --- | --- | --- | --- |
| **Kimi K3** | Sol 替代首选 | 2.8T 总参、1M 上下文、原生视觉、长程编程与端到端知识工作；Chat Completions / Responses / Anthropic Messages 三协议；函数调用、动态工具加载、严格 JSON Schema、联网搜索；官方提供 Codex / Claude Code / OpenCode / Hermes 接入文档 | thinking 恒开，延迟与 token 放大；证据以厂商自评为主；无本项目本地闭环证据 |
| **GLM-5.3** | Sol 替代并列首选 / 深评强项 | 文本、1M 上下文、128K 输出；thinking 恒开（low/high/max）；三协议；Terminal-Bench 3.0 由 4.6→28.3、DeepSWE v1.1 由 46.2→66.9、Agents' Last Exam 23.8→28.5；内部 Z.ai Code Bench 的 High 档 31.4%（厂商所列对比中优于 Opus 4.8 的 29.5%，低于 Fable 5 的 39.5%） | 纯文本，不能单独承担视觉角色；reasoning 恒开需控成本；深安全利用类任务仍明显落后前沿闭源 |
| **MiniMax-M3** | 研究型 Owner / 综合备选 | 约 428B 总参 / 23B 激活、1M 上下文、原生文本+图像+视频；interleaved thinking；服务端联网搜索；官方自报 SWE-Bench Pro 59.0、Terminal-Bench 2.1 为 66.0、MCP Atlas 74.2、BrowseComp 83.5、OSWorld-Verified 70.06% | 关键结果多为厂商自建评测；OMP 侧运行证据不足；权重规模大不利自托管 |

### 3.2 视觉 / UI / Computer Use 候选

| 模型 | 定位 | 关键官方事实 | 主要风险 |
| --- | --- | --- | --- |
| **Seed2.1 Pro** | Astra 替代首选 | 面向通用 Agent、跨工具跨环境交付、Coding 端到端交付、多模态与视频理解；面向 CUA 优化；官方众测中对其所列 Claude Opus 4.6 获 59.1% 胜率；Code Arena Frontend 1539 分排名第 8、7 个子类 5 个进前十；OSWorld / MobileWorld / CreativeWork 表现突出 | 大量结果为厂商内部或自建基准；需在 OMP 实测截图输入、工具 schema、长程状态与失败关闭 |
| **GLM-5.3-Flash** | 低成本视觉与前端复核 | 320B/18B；原生图像+视频+文本+文件输入；1M 上下文、128K 输出；视觉融入 Coding 循环（看图改代码）；官方称其编码表现与其所列 Opus 4.8 相当，价格显著更低 | 视觉结论多来自自研基准与案例；不能用模型自报视觉通过替代 Browser/Computer 证据 |
| **ERNIE 5.0 / 4.5-VL** | 中文视觉补位 | ERNIE 5.0 为原生统一多模态（千帆视觉理解列表内）；ERNIE 4.5 Turbo VL 为低成本视觉补位 | 上下文仅 128K；无公开 GUI 操作类评测；ERNIE 5.1 本身**无图片输入通道** |

### 3.3 代码 / 执行候选

| 模型 | 定位 | 关键官方事实 | 主要风险 |
| --- | --- | --- | --- |
| **DeepSeek V4.1 Flash** | 执行档主力，并具备局部 Owner 潜力 | 552B MoE、1M 上下文、原生图像；8B prefill / 16B decode 激活；reasoning effort 连续可调 1–100；API id `deepseek-flash`；MIT 权重；官方模型卡给出 DeepSeek Harness / Claude Code / Codex / OpenCode / Pi 多脚手架结果 | 官方自评对照中，Terminal-Bench 3.0/4.0、ProgramBench、深安全利用仍弱于 GPT-5.6 Sol；不建议直接升为全平台唯一 Owner |
| **Qwen3-Coder** | 代码专项执行与第二意见 | 480B/35B 激活；原生 256K、可扩 1M；70% 代码语料；长程 Agent RL 与 20,000 并行环境；官方称其 Agentic Coding / Browser-Use / Tool-Use 达到开源 SOTA，接近其所列 Claude Sonnet 4；提供 Qwen Code CLI 与 Claude Code / Cline 接入 | 不适合承担 outcome、跨域综合与 UI 评审；仅作代码专项 |

官方模型卡中 DeepSeek V4.1 Flash 与 GPT-5.6 Sol 的对照（**厂商自评，非本地结论**）：

| 基准 | DeepSeek V4.1 Flash | GPT-5.6 Sol |
| --- | ---: | ---: |
| Terminal-Bench 2.1 | 90.6 | 88.8 |
| Terminal-Bench 3.0 | 30.0 | 34.4 |
| Terminal-Bench 4.0 | 31.2 | 39.9 |
| DeepSWE v1.1 | 74.2 | 73.0 |
| ProgramBench | 20.3 | 23.0 |
| NL2Repo-Bench | 64.0 | 56.8 |
| CyberGym | 88.1 | 84.5 |
| AutomationBench | 54.8 | 45.8 |
| Agent's Last Exam | 31.8 | 26.7 |
| Chartography（带工具） | 78.9 | 79.9 |
| BabyVision（带工具） | 89.6 | 88.9 |
| ZeroBench（带工具） | 49.0 | 53.0 |

### 3.4 暂不列入首批替代的模型

| 模型 | 原因 |
| --- | --- |
| ERNIE 5.1 | 文本 only（千帆视觉理解列表不含 5.1）、128K 上下文、无公开 SWE/长程工程评测；适合中文文本研究与企业知识补位 |
| 腾讯混元 | 本轮官方可核验的模型、API 契约、Agent 工具稳定性证据不足（文档站反爬/登录限制），作为后续候选 |

## 4. 推荐的国产组合

### 4.1 方案 A：最稳妥的无 GPT 组合

| Team OS 角色 | 模型 | 责任 |
| --- | --- | --- |
| `default` / outcome owner | Kimi K3 | outcome、规划、跨仓合同、最终综合 |
| `plan_owner` | Kimi K3 | 实施规划、DAG、派工包 |
| 架构/代码深评 | GLM-5.3 | 软件架构、终端任务、安全反证、独立评审 |
| `ui_deep` | Seed2.1 Pro | UI/UX、视觉、Computer Use、前端交互 |
| 视觉复核 | GLM-5.3-Flash | 截图/视频/UI 实现后的独立复核 |
| `fast_worker` | DeepSeek V4.1 Flash | 侦察、有界实现、叶子执行 |
| 代码第二意见 | Qwen3-Coder | 代码专项异厂复核 |
| 研究（按需） | MiniMax-M3 | 长文档、联网研究、证据汇总 |

### 4.2 方案 B：三模型精简组合（推荐第一阶段）

| 角色 | 模型 |
| --- | --- |
| 主 Owner / 规划 / 最终综合 | Kimi K3 |
| 深度代码与架构评审 | GLM-5.3 |
| UI / 视觉 / Computer Use | Seed2.1 Pro 或 GLM-5.3-Flash |
| 执行 worker | DeepSeek V4.1 Flash |

只有一个常驻 Owner，其余按需调用。

### 4.3 方案 C：偏开放权重与自主可控

Kimi K3 开源权重 + DeepSeek V4.1 Flash（MIT）+ Qwen3-Coder + GLM-5.3-Flash 开源权重 + MiniMax-M3。
前提：旗舰模型规模大，“开源”不等于易自托管；若必须单机自托管，需退到更小模型并接受质量下降。

### 4.4 若 Kimi K3 在真实任务中不稳定

将 Owner 换成 GLM-5.3，Kimi K3 降为长文研究与最终第二意见。

## 5. 能否超越当前 GPT 工作流

| 领域 | 更可能更优的国产组合 |
| --- | --- |
| 超长上下文（整仓 + 文档同窗） | Kimi K3、GLM-5.3、MiniMax-M3 |
| 中文知识工作与文档交付 | Kimi K3、Seed2.1、ERNIE |
| 低成本大规模 Agent 执行 | DeepSeek V4.1 Flash |
| 前端视觉反馈与 Computer Use | Seed2.1 Pro、GLM-5.3-Flash |
| 代码双模型复核 | DeepSeek + Qwen3-Coder |
| 长文联网研究 | MiniMax-M3 + Kimi K3 |
| 国产芯片推理路径 | GLM-5.3 / 5.3-Flash 官方公开的 Ascend 与国产芯片部署路径 |

目前无法证明超越的部分：全局 outcome 判断；跨服务/权限/账务/数据生命周期/生产风险的最终综合；模糊的新模块设计；极高风险独立审查；长时间连续工具调用的低故障率；深层安全利用链推理；多模型冲突结论的稳定收敛。

多模型不会自动带来超越。角色过多会带来 token 消耗上升、冲突意见增多、Owner 综合负担加重、结果责任模糊、延迟与失败面扩大。

## 6. 推荐迁移路径

1. **影子运行**：不改默认路由。Kimi K3 作为 Sol 影子 Owner、GLM-5.3 做冻结候选的独立代码/架构评审、Seed2.1 Pro 或 GLM-5.3-Flash 替代 Astra 做 UI/视觉评审，DeepSeek 保持执行档。记录 outcome 遗漏、首次判别事实、返工、用户纠偏、逃逸缺陷、token、时长、工具失败与交接等待。
2. **无 GPT 演练**：建立独立 profile（例如 `cn-only`），覆盖 6～10 个代表性任务：局部快修、跨仓功能、诊断并修复、前端/UI、长文研究、状态机、只读代码评审、生产前计划（只到本地 Gate）。
3. **按证据晋升**：只有完成率不低于基线、P0/P1 遗漏不增加、返工与纠偏不增加、耗时与 token 可接受、工具/停止/恢复/fallback 可查、视觉与真实入口验收完整时，才把无 GPT profile 提升为正式回退。

全程复用现有 [`context-economy.md`](../../workflows/context-economy.md) 的派工包与读取纪律；晋升结论写入 `models/catalog.yaml` 的 `activePortfolio`，并用 `scripts/check_model_routes.py` 核对运行时绑定漂移。

## 7. 证据基础与限制

**官方一手来源（读取日期 2026-09-16）**

- DeepSeek：[V4.1-Flash 发布](https://www.deepseek.com/en/news/deepseek-v4-1-flash/)、[官方模型卡](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash)
- Kimi：[K3 快速开始](https://platform.kimi.com/docs/guide/kimi-k3-quickstart)、[文档索引](https://platform.kimi.com/docs/llms.txt)
- 智谱：[GLM-5.3](https://docs.bigmodel.cn/cn/guide/models/text/glm-5.3)、[GLM-5.3-Flash](https://docs.bigmodel.cn/cn/guide/models/vlm/glm-5.3-flash)、[模型概览](https://docs.bigmodel.cn/cn/guide/start/model-overview)
- 字节 Seed：[Seed2.1 发布](https://seed.bytedance.com/zh/blog/seed2-1-officially-released-advancing-ai-productivity)、[模型主页](https://seed.bytedance.com/zh/models)
- 阿里 Qwen：[Qwen3-Coder 发布](https://qwenlm.github.io/blog/qwen3-coder/)
- 百度千帆：[平台文档](https://cloud.baidu.com/doc/qianfan/index.html)
- MiniMax：[平台文档与模型清单](https://platform.minimax.io/docs/guides/text-generation)、[模型发布记录](https://platform.minimax.io/docs/release-notes/models.md)

**限制**

- 本轮通用搜索后端全部不可用（startpage / duckduckgo / ecosia / google / mojeek 被拦或超时），因此没有第三方交叉验证；上述 benchmark 均为**厂商自报**。
- 部分官方 benchmark 为图片（ERNIE、MiniMax 部分）或超出工具体积上限（Seed2.1 Model Card PDF 约 69MB），未能读取；这些位置的能力结论以正文可读断言为限。
- 腾讯云部分文档站需登录或强反爬，混元结论不完整。
- 未做任何本地推理或 API 实测：本轮没有运行真实任务，因此**没有一条本地真实任务证据**；所有角色映射都是候选假设，必须经第 6 节迁移路径验证。

## 8. 复评条件

出现以下任一情况时重开本结论：

1. Kimi K3、GLM-5.3、Seed2.1、MiniMax-M3 任一发布新主版本或上下文/定价重大变化；
2. 无 GPT 演练累计 ≥ 6 个代表性任务，且出现逃逸缺陷或稳定质量差距；
3. 出现具备可验证长程 Agent 能力的国产新模型（尤其是带完整工具调用与恢复合同的开放权重模型）；
4. 采购结构变化导致主力模型不可持续（额度、限速、区域可用性）。

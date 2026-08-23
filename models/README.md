# 模型组合与准入策略

## 1. 基线不是模型动物园

GPT-5.6 Sol 保持复杂结果负责人和最终综合基线；Terra、Luna 是同一家族的成本/吞吐分层，不视为真正独立的认知通道。OpenAI 官方当前将 Sol 定位为复杂推理与编码旗舰、Terra 定位为质量/成本平衡、Luna 定位为高吞吐低成本：<https://developers.openai.com/api/docs/models>。

新增模型只为获得 GPT-5.6 基线缺少的证据通道，不为角色外观或厂商数量。所有模型必须分别通过：

1. **能力 Gate**：在目标角色冻结案例上贡献被采用的独有证据；
2. **运行 Gate**：CLI、初始 Prompt、独立 Home、Session、Hook/空闲、Inbox、停止和失败语义真实闭合；
3. **治理 Gate**：密钥只在运行时注入，数据边界、价格、模型漂移和降级可解释。

厂商排名与自报 benchmark 只用于选择试点，不能替代本地 eval。

## 2. 当前推荐组合

| 优先级 | 厂商/模型 | 最有价值的角色 | 价值来源 | 当前结论 |
| --- | --- | --- | --- | --- |
| 基线 | OpenAI GPT-5.6 Sol | 复杂结果负责人、架构与最终综合 | 当前最强主链、工具和编码闭环 | 保持主力；提示词继续瘦身 |
| 已有互补 | Google Gemini CLI Auto / `gemini-3.7-flash` | 多模态与超长材料侦察员 | 官方 CLI 有 Hook/Session；Gemini 提供百万级上下文与多模态 | 保留第二证据通道；固定模型与 Auto 分开评测 |
| 已有互补 | DeepSeek V4 Pro / Flash | 独立推理审查、低成本批处理 | 独立模型家族、百万上下文、OpenCode 官方接入 | 不做最终 owner；适合反证与成本对照 |
| 新增首选 | xAI Grok 4.6 | 时效研究、开放世界挑战者、交互原型评审 | 原生 Web/X 搜索、引用、代码执行；Munder 已有 Grok Hook 桥 | 先做只读研究与挑战者真实运行试点 |
| 新增第二 | Moonshot Kimi K3 | 中文知识工作、长文档、办公产物与多模态分析 | 原生中文、1M 上下文、图像/视频、官方 CLI 已有 Session 与 Hook | 值得接入；先补 Munder Kimi Hook/恢复合同 |
| 条件候选 | Alibaba Qwen3-Coder-Plus / Qwen3-Coder 开放权重版 | 中文代码、阿里生态、开放模型/本地备选 | Agentic coding；Qwen Code 已有 Hook/Session/预算控制 | 云端 Plus 与开放权重部署分开评测；后置到隐私或生态需求出现时 |

Claude 系列按用户要求排除，不作为候选或隐藏回退。

## 3. 事实依据与接入差异

### Gemini

Google 官方模型页将 `gemini-3.7-flash` 定位为当前最强 Flash，面向复杂编码、Agent 工作流和可靠多步执行；Gemini CLI 已提供结构化 Hook、项目级 Session 和 `--resume`。适合读取图片、视频、超长文档或大代码库并形成证据摘要，但不应因此把完整仓库无差别塞入 Prompt。型号会漂移，CLI Auto 与冻结模型 ID 必须分开评测。

- 模型：<https://ai.google.dev/gemini-api/docs/models>
- CLI Hook：<https://geminicli.com/docs/hooks/reference/>
- Session：<https://geminicli.com/docs/cli/session-management/>

### DeepSeek

DeepSeek V4 Pro/Flash 提供 1M 上下文、思考/非思考与工具调用，并官方支持 OpenCode。它与 GPT-5.6 属不同模型家族，适合作为独立反证者；但思考模式的多轮工具协议要求正确保留 `reasoning_content`，运行 Gate 必须覆盖该差异。

- V4：<https://api-docs.deepseek.com/news/news260424/>
- OpenCode 接入：<https://api-docs.deepseek.com/guides/coding_agents>
- 思考模式：<https://api-docs.deepseek.com/guides/thinking_mode/>

### Grok

Grok 4.6 提供 500K 上下文、图像输入、可配置推理和 Web/X 搜索；实时信息只有启用搜索工具时成立。它最独特的角色不是重复写代码，而是对时效性、舆情、市场和开放网络事实提供第二证据源。

- 模型与工具：<https://docs.x.ai/developers/grok-4-6>
- 引用：<https://docs.x.ai/developers/tools/citations>
- Grok Build/CLI：<https://x.ai/news/grok-build-open-source>

### Kimi

Kimi K3 是原生多模态、百万上下文的中文强模型；官方 Kimi Code CLI 已提供独立 Home、Session 恢复和生命周期 Hook。Munder 当前 Kimi Provider 仍按“无 Hook、不能收 Inbox”处理，已经落后于厂商能力，必须先补桥并真实验证再进入协作路由。

- K3：<https://moonshotai.github.io/>
- Session：<https://moonshotai.github.io/kimi-code/en/guides/sessions.html>
- Hook：<https://moonshotai.github.io/kimi-code/en/customization/hooks>

### Qwen

Qwen3-Coder-Plus 面向 Agentic coding、工具与环境交互，Qwen Code 已提供 Hook、Session 恢复、工具/时长预算和 Worktree 隔离。`qwen3-coder-plus` 是阿里云托管型号；本地私有路线应另行评测公开权重的 Qwen3-Coder 变体，不能把二者当成同一运行合同。当前 Munder 的 Qwen 注释仍标记 Hook 缺失和多个 `TODO-verify`，因此应更新 Provider 事实后再评估；除非中文代码、阿里云生态或本地模型成为明确需求，否则不优先扩大主链。

- 模型：<https://help.aliyun.com/en/model-studio/qwen3-coder-plus>
- Hook：<https://qwenlm.github.io/qwen-code-docs/en/users/features/hooks/>
- Session 与预算：<https://qwenlm.github.io/qwen-code-docs/en/users/features/headless/>

## 4. 路由原则

- Michael/参谋长默认使用 GPT-5.6 Sol，但只维护结果卡、拓扑和综合，不重做专家分析。
- 关键结论至少由项目权威或工具证据支持，不能用“另一模型也同意”代替验证。
- 新 Provider 在运行 Gate 未闭合前只能承担隔离、只读、可丢弃的侦察任务，不能作为 Michael、单写者或生产负责人。
- 跨模型首轮互相不可见；综合时比较独有证据、错误相关性、Token、延迟和人工纠偏。
- 不静默切换模型。模型不可用时显式降级到 GPT-5.6 基线，并记录失去的证据通道。
- `catalog.yaml` 是人工审查的候选清单，不是 Munder 当前自动路由配置。

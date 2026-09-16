# 结论记录：国产模型 Coding 套餐组合采购方案

> 性质：调研结论记录 + 采购建议，不是执行权威。角色分档与派工规则见 [`../../workflows/context-economy.md`](../../workflows/context-economy.md)；模型组合结论见 [`01-结论记录-无GPT条件下全国产模型替代TeamOS角色判断.md`](01-结论记录-无GPT条件下全国产模型替代TeamOS角色判断.md)。所有价格与额度为 **2026-09-16** 官方页面快照，购买前必须回官网复核（本文件不含凭据，也不构成任何账号共享建议）。

## 0. 一句话结论

**一个套餐不够，但"两条低价聚合订阅 + 一个按量 API + 一个 Owner 订阅"就够。** 骨架：

| 层 | 采购项 | 价格 | 作用 | 依据 |
| --- | --- | --- | --- | --- |
| 广度层 | **opencode Go** | \$10/月 | 一个 key 覆盖 20+ 国产模型（Kimi K3、GLM-5.3/5.3-Flash、DeepSeek V4.1 Flash、MiniMax M3、Qwen3.7/3.8、MiMo、LongCat、Hy3/Hy4、Grok、GPT-5.6 Luna）；明确允许非 OpenCode 的编程 Agent | [Go 文档](https://opencode.ai/docs/zh-cn/go/) |
| Credits 池 | **Command Code GOAT** | \$10/月（\$70 credits） | 附加 credits **不过期且不受窗口限制**；含 OpenAI/Anthropic 双协议与 GPT-5.6 Luna、Grok、Qwen Max | [计划文档](https://commandcode.ai/docs/plans/goat) |
| Owner 层 | **Kimi 会员 Moderato/Allegretto** | ¥99 / ¥199 每月 | K3 作为主 Owner（1M 上下文、长程编码）；官方提供 Claude Code / OpenCode / Codex 接入 | [Kimi Code 概览](https://www.kimi.com/code/docs/) |
| 评审/视觉层 | **智谱按量 API** 或 **Charm Hyper Prepaid** | 按量 / \$20=400 credits | GLM-5.3 异厂深评 + GLM-5.3-Flash 视觉复核；Hyper 只含开源模型、credits 永不过期 | [智谱定价](https://docs.bigmodel.cn/cn/guide/start/pricing) / [Hyper](https://hyper.charm.land/) |
| 执行层 | **DeepSeek 官方按量** | 按量（谷时 \$0.15/\$0.6 每百万 tokens） | 侦察、有界实现、叶子执行、机械文档；并发 2500、无工具限制 | [Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing) |
| 大陆候选（待验证端点） | **火山方舟 Ark Coding Plan** | 限时 **¥9.9 起**/月（刊例价未公布） | 一个订阅覆盖 DeepSeek-V4 / GLM-5.3 / Kimi-K3 / Doubao-Seed，约 18,000 次请求/月，人民币结算；官方称"工具不限" | [活动页](https://www.volcengine.com/activity/codingplan) |

**关键判据不是价格，而是"官方是否允许第三方 harness"**：opencode Go/Zen、Command Code、Charm Hyper、Kilo Pass、NanoGPT 明确允许；智谱 GLM Coding Plan 与阿里 Coding Plan 是白名单/禁 API 调用，**不能接 OMP**；小米 MiMo 与 ZenMux 属灰区或不推荐。详见 §2 与"合规置信度排序"。

推荐档位：**方案 A（\$20–40/月）先验证链路 → 方案 B（≈\$60–100/月 + ¥99–199）全职使用 → 方案 C（\$200–300/月）多项目并行**。

## 1. 选套餐的四个硬约束

采购必须先过这四关，否则再便宜也不可用：

1. **能否接入自建 harness（OMP）**：多数国产 Coding 套餐明文「仅限官方指定工具，禁止 API 调用」。OMP 不在列表里 → 直接用套餐 key 属于灰区甚至违规封号风险。**要么买按量 API，要么选明确允许第三方 Agent 的套餐。**
2. **额度模型**：按「请求次数」（阿里）、「积分」（智谱）、「美元额度」（opencode Go）、「credits」（MiniMax）四种口径完全不同，不能直接比价，必须换算成「每月可用 token/任务数」。
3. **窗口结构**：5 小时滚动 + 周/月上限是主流；这意味着**单套餐无法支撑全天候高强度使用**，必须靠多套餐 + 按量兜底叠加。
4. **异厂多样性**：Owner 与深度评审必须不同厂商，否则失去独立复核价值（见结论记录 01 第 4 节）。

## 2. 各套餐官方事实（2026-09-16）

### 2.1 opencode Go — 广度层，\~\$10/月

| 项 | 事实 |
| --- | --- |
| 价格 | 每月 10 美元订阅，获得 API Key |
| 覆盖模型 | Grok 4.6、GPT 5.6 Luna、GLM-5.3/5.3-Flash/5.2/5.1、Kimi K3/K2.7 Code/K2.6、LongCat-2.0、MiMo-V2.5/Pro、MiniMax M3/M2.7/M2.5、Qwen3.8 Max/Flash、Qwen3.7 Max/Plus、Qwen3.6 Plus、DeepSeek V4.1 Flash/V4 Pro/V4 Flash/V4 Flash Vision Exp、Hy4 preview、Hy3、Muse Spark |
| 额度结构 | 每个模型有独立「每月美元额度」：5 小时 = 20%、每周 = 50%、每月 = 100% |
| 关键额度 | GLM-5.3-Flash \$60、Kimi K2.7 Code \$60、MiniMax M3 \$60、DeepSeek V4.1 Flash \$60（活动 4x，9/20 结束）、Qwen3.7 Plus \$60、GLM-5.3 \$15、Kimi K3 \$15、Qwen3.8 Max \$15、DeepSeek V4 Pro \$15 |
| 预估请求数 | GLM-5.3-Flash 约 31,580/月；MiniMax M3 约 16,000/月；DeepSeek V4.1 Flash 约 130,000/月（活动期）；Kimi K3 约 490/月 |
| 端点 | OpenAI 兼容 `https://opencode.ai/zen/go/v1/chat/completions`；另有 `/v1/responses`、`/v1/messages` |
| 接入限制 | 明确「适用于 OpenCode 以及其他会产生类似请求的编程 Agent」；要求客户端发送自身 user agent 与 `x-opencode-session` 会话头；列出已验证客户端（Claude Code、Codex、Pi、Hermes、ZCode、jcode、Kilo CLI）与已知问题客户端（DeepSeek Harness、Kimi Code、MiMo Code、GitHub Copilot Chat） |
| 超额 | 可开启「用 Zen 余额继续」，或直接用 Zen 按量 |
| 隐私 | 绝大多数模型 ZDR 0 天留存、不用于训练（Grok / GPT Luna 为 30 天） |

**判断**：这是目前**性价比最高的"一 key 覆盖多国产模型"入口**，也是唯一明确欢迎非官方客户端的订阅制套餐。缺点是顶级模型额度小（Kimi K3、GLM-5.3 各 \$15/月），**不足以承担全职 Owner**。

### 2.2 opencode Zen（按量）— GPT 角色的备用通道

| 项 | 事实 |
| --- | --- |
| 计费 | 纯按量付费 |
| 与 Team OS 相关 | 提供 **GPT 5.6 Sol**（\$2/\$10，含 50% 折扣至 9/18）、**GPT 6 Astra**（\$10/\$50）、以及 GLM/Kimi/Qwen/DeepSeek/MiniMax 全系 |
| 端点 | `https://opencode.ai/zen/v1/responses`（GPT/Grok）、`/v1/chat/completions`（国产模型） |
| 免费档 | MiMo-V2.5 Free、Big Pickle、Nemotron 3 Ultra/3.5 Lightning Free、Ling 3.0 Flash Fin Free、Muse Spark Contributor Free |

**判断**：既是国产模型的按量兜底，也是**「GPT 有条件使用」场景下的合规替代通道**（无需 Codex OAuth）。免费档适合低价值批量任务（如日志扫描、机械分类）。

### 2.3 智谱 GLM Coding Plan — 评审层

| 项 | 事实 |
| --- | --- |
| 模型 | 全部套餐支持 GLM-5.3、GLM-5.3-Flash（含视觉理解 MCP） |
| 额度 | Lite：2,000 积分/5h、10,000/周；Pro：12,000/5h、60,000/周；Max：28,000/5h、140,000/周 |
| 积分折算 | 积分 =（输入 Token × 系数 + 缓存命中 × 系数 + 输出 × 系数）/ 10000；GLM-5.3 系数 6.9/1.7/24，GLM-5.3-Flash 系数 2.3/0.56/8 |
| 可用量参考 | 95% 缓存命中时，Pro 每周约 2.90～5.80 亿 GLM-5.3 tokens、8.77～17.55 亿 GLM-5.3-Flash tokens；Max 约 6.76～13.52 亿 / 20.47～40.95 亿 |
| 非高峰 | 非高峰按基础积分 50% 抵扣；高峰为周一至周五 14:00–18:00（UTC+8） |
| 并发 | 官方不公布数值，只按档位给「建议项目数」：Lite 单项目、Pro 1–2 个、Max 2+ |
| 附加能力 | 视觉理解、联网搜索、网页读取、开源仓库 MCP 与模型共享额度 |
| **使用限制** | 白名单制，Coding Agent 侧含 ZCode、Claude Code、Claude for IDE、Codex、OpenCode、**Pi**、TRAE、CodeBuddy、Lingma、Qoder、Kilo、MonkeyCode、Cline、Droid、Roo、Crush、Goose、Cursor、Cherry Studio；通用 Agent 侧含 AutoClaw、OpenClaw、Hermes（次级调度）。**OMP 不在白名单**；非规定工具调用不享受套餐额度，自建应用/网站/机器人需改用标准 API 按量计费 |
| 端点 | 套餐三协议并存：Anthropic `https://open.bigmodel.cn/api/anthropic`、OpenAI Chat `https://open.bigmodel.cn/api/coding/paas/v4`、OpenAI Responses `https://open.bigmodel.cn/api/v1`；**选错端点不吃套餐额度** |
| 1M 上下文 | GLM-5.3 需在模型名加 `[1m]` 后缀并配置 `CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000` |
| 活动 | 2026-09-03～09-20 每日 23:00～次日 09:00：ZCode 端 GLM-5.3-Flash 额度免费、其它受支持 Agent 额度 ×2（仅 5.3-Flash） |
| 退款 | 不支持退款；取消需在扣费日前 ≥3 天 |
| 价格（V2 版，官方公告） | Lite 包月 ¥49（季 ¥44.1／年 ¥39.2）、Pro 包月 ¥149（季 ¥134.1／年 ¥119.2）、Max 包月 ¥469（季 ¥422.1／年 ¥375.2） |
| 计费系数（V2 版） | GLM-5.3 非高峰 1 倍／高峰 3 倍；GLM-5.3-Flash 非高峰 0.4 倍／高峰 1.2 倍（高峰 = 周一至周五 14:00–18:00 UTC+8） |
| 注意 | 2026-07-30 起新版为积分制，**新购与首次订阅以订阅页价格为准**（上表为老用户可按 V2 价格续订的口径，原文："请以套餐订阅页…为准"） |

**OMP 侧事实（本机二进制证据，2026-09-16）**：OMP 内置两个专门的套餐 provider——

- `zhipu-coding-plan`：baseUrl `https://open.bigmodel.cn/api/coding/paas/v4`，env `ZHIPU_API_KEY`，默认模型 glm-5.1（即智谱给 Claude Code 之外的第三方工具用的 coding 端点）；
- `zai-coding-plan`：Z.AI（国际站）GLM Coding Plan，OAuth 登录或粘贴 `sk-` key，baseUrl `https://api.z.ai/api/coding/paas/v4`；
- 另有按量通道 `zai`（`https://api.z.ai/api/anthropic`，glm-5.3 / glm-5.2 等），以及 `glm-5.3-flash` 走 coding 端点。

**判断**：技术上 **OMP 原生支持 GLM Coding Plan**（不是只能走按量 API）；但智谱条款把可用范围限定在"指定工具白名单"，**OMP 不在该名单**，属需自担的灰区。零条款风险的替代是 `zai` 按量（GLM-5.3 ¥8/¥28/¥2 每百万 tokens）。

### 2.4 Kimi Code（Kimi 会员权益）— Owner 层

| 项 | 事实 |
| --- | --- |
| 形态 | Kimi Code 是 Kimi 会员权益中的开发者编程服务，额度与 Kimi 会员共享 |
| 模型 ID | `k3`（1M 上下文，Moderato+；Allegretto+ 解锁 100 万上下文）、`k3-256k`、`kimi-for-coding`（K2.8 Preview，所有会员）、`kimi-for-coding-highspeed`（K2.7 Code 高速，Allegretto+） |
| 端点 | OpenAI 兼容 `https://api.kimi.com/coding/v1`；Anthropic 兼容 `https://api.kimi.com/coding/` |
| 额度 | 以订阅日为起点**每 7 天刷新**，不累积；另有**每 5 小时滚动频率窗口**；所有设备与 API Key 共享同一配额 |
| 加油包 | 额度耗尽可用加油包继续；与 Kimi 网页端共享钱包；余额不过期、可叠加；单次最低 ¥25；费率近似开放平台 API |
| 第三方工具 | 官方提供 Claude Code / OpenCode / Codex 接入文档；**要求保持工具真实身份标识，篡改 User-Agent 视为违规** |
| 价格（官方帮助中心） | Andante ¥49/月、Moderato ¥99/月、Allegretto ¥199/月、Allegro ¥699/月；连续包年最高省 ¥1,680 |
| 档位差异（对本组合关键） | `k3`（1M 上下文）需 **Allegretto 及以上**；`k3-256k` 与 `kimi-for-coding`（K2.8 Preview）Moderato 及以上；`kimi-for-coding-highspeed`（K2.7 Code 高速）Allegretto 及以上 |
| 并行 | Agent 任务并行：Moderato/Allegretto 2 个、Allegro 4 个 |
| 对照 | Kimi 开放平台 API：`kimi-k3` ¥2（缓存命中）/¥20（未命中）/¥100 输出 每百万 tokens；`kimi-k2.7-code` ¥1.3/¥6.5/¥27 |

**判断**：K3 若作为主 Owner，**订阅会员比按量 API 划算得多**，且官方允许第三方工具接入 —— 这是无 GPT 组合里最关键的 Owner 通道。风险是周额度 + 5 小时窗口，需要 opencode Go 或按量 API 兜底。

### 2.5 MiniMax Token Plan — 研究 / 多模态层

| 项 | 事实 |
| --- | --- |
| 价格 | Plus \$22/月、Max \$55/月、Ultra \$132/月 |
| 覆盖 | 完整 MiniMax 产品线（M3 / M2.7 / 图像 / 语音）共享同一额度；不含 H3、音色设计等少数特殊模型 |
| 窗口 | 5 小时滚动 + 每周窗口 |
| Agent 规模 | Plus 3–4 agents、Max 4–5、Ultra 6–7 |
| 接入 | 官方文档列出 Claude Code、Codex、Cursor、TRAE、Hermes、OpenClaw、Pi，以及 **Other Tools：任何支持自定义 OpenAI/Anthropic 兼容端点的编程工具** |
| 附加 | Credits 充值包（1,000 credits = \$1，365 天有效）可作溢出；Token Plan MCP 提供 web_search 与图像理解 |

**判断**：**唯一一家文档中明确欢迎"自定义 OpenAI 兼容端点"的国产订阅套餐**，对 OMP 最友好。M3 的 1M 上下文与联网研究能力可替代 Sol 的研究分支。

### 2.6 阿里云百炼 Coding Plan — 聚合最全但限制最严

大陆站与国际站是**两套独立凭证、端点与价格**：

| 项 | 大陆站 | 国际站 |
| --- | --- | --- |
| 价格 | **¥200/月**（新客首月 ¥39.90；仅月付、不可退款；每日 09:30 UTC+8 限量补货） | **\$50/月**（每日 00:00 UTC+8 补货；仅月付、不可退款） |
| 额度 | 每 5 小时 6,000 次请求 / 每周 45,000 / 每月 90,000（**按"模型调用次数"计量，与 token 无关**，官方明示无法查看 token 消耗） | 同左 |
| 恢复 | 5 小时额度滚动恢复（每分钟释放 5 小时前用量）、周额度周一 00:00 重置、月额度在订阅日重置；耗尽即报错，**不自动转按量** | 同左 |
| 端点 | OpenAI 兼容 `https://coding.dashscope.aliyuncs.com/v1`；Anthropic 兼容 `.../apps/anthropic`；Key 前缀 `sk-sp-` | `https://coding-intl.dashscope.aliyuncs.com/v1` 与 `.../apps/anthropic` |
| 协议 | 仅 OpenAI Chat Completions + Anthropic Messages；**不支持 Responses API**；不支持 Claude Code 的 Agent Teams | 同左 |

支持的模型（精确版本，官方称满血未量化）：qwen3.7-plus（1M 上下文、图片理解）、qwen3.6-plus（1M、图片）、qwen3.5-plus（1M、图片）、qwen3-coder-plus（1M）、qwen3-max-2026-01-23（262K）、qwen3-coder-next（262K，无思考模式）、kimi-k2.5（262K、图片）、glm-5（202K）、glm-4.7（202K）、MiniMax-M2.5（196K）。

**限制（最关键）**：

- 官方白名单工具：Claude Code、OpenCode、Codex、Cursor、Cline、Qwen Code、QwenPaw、Qoder/Qoder CN、OpenClaw、Kilo CLI、Cherry Studio、Chatbox、Lingma、Hermes Agent。
- **明令禁止非交互式调用**：禁止自动化脚本、自定义应用后端、批量调用；curl / Postman / Dify 明确不支持，服务端报错文案为 `Coding Plan is currently only available for Coding Agents` —— 说明**服务端会做 Coding-Agent 判定**。
- 单账号只能订阅一份、仅 1 个 API Key、不支持 IP 白名单、禁止共享（检测到公开泄露可自动禁用 Key）。

**判断**：技术上可直连（OpenAI 兼容 + `sk-sp-` Key），但**合同风险高**：OMP 不在白名单且属非官方客户端，被判违规可能导致订阅暂停或 Key 封禁。**不推荐作为 OMP 主通道**；正确用法是在官方列出的 IDE/CLI 内使用，或在 OMP 改用百炼**按量 API**。

### 2.7 DeepSeek 官方按量 — 执行层（无订阅）

| 项 | 事实 |
| --- | --- |
| 模型 | `deepseek-flash`（DeepSeek-V4.1-Flash）、`deepseek-v4-pro` |
| 价格（每百万 tokens，官方双币种） | flash：缓存命中 \$0.003（谷）/\$0.006（峰）、未命中 \$0.15/\$0.30、输出 \$0.6/\$1.2；人民币口径 空闲 ¥0.02/¥1/¥4、高峰 ¥0.04/¥2/¥8。pro：0.022/0.044、0.66/1.32、1.98/3.96；人民币 空闲 ¥0.15/¥4.5/¥13.5、高峰 ¥0.30/¥9/¥27 |
| 峰谷时段（官方中文页） | 高峰 = 北京时间周一至周五 9:00–12:00、14:00–18:00（= UTC 01:00–04:00、06:00–10:00）；其余（含周末）为空闲，价格为高峰的一半 |
| 官方 harness 支持原文 | "The DeepSeek API is supported by many popular AI agent and coding assistant tools… you can use DeepSeek as the backend model directly — no code required."（附 Agent Integrations Guide） |
| 并发（账号级，与 Key 无关） | flash 2500、pro 500；超限 HTTP 429；**可申请扩容且官方称扩容不额外收费**；10 分钟未开始推理服务端关闭连接 |
| 峰谷 | 高峰为周一至周五 01:00–04:00、06:00–10:00 UTC；其余（含周末）为谷时，价格减半 |
| 并发 | flash 2500、pro 500 |
| 端点 | OpenAI 格式 `https://api.deepseek.com`；Anthropic 格式 `https://api.deepseek.com/anthropic` |
| 限制 | 无订阅、无工具限制，纯按量 |

**判断**：执行档不需要订阅。谷时价格极低 + 并发 2500，是**唯一可以无限量跑机械任务**的通道。

### 2.8 字节 TRAE（IDE/工具型，非 API 通道）

| 项 | 事实 |
| --- | --- |
| 价格 | Free；Lite \$3/月（含 \$5 basic usage）；Pro \$10/月（含 \$20，7 天免费试用）；Pro+ \$30/月（3.5× Pro）；Ultra \$100/月（20× Pro）；年付省 25% |
| 并发 | TraeWork 云任务并发：Lite 2、Pro 10、Pro+ 15、Ultra 20 |
| 形态 | 官方定价页面向 IDE/云端任务，未见"对外提供 API Key 给第三方 harness"的说明 → **视为工具型套餐，不作为 OMP 通道** |

### 2.9 聚合与低门槛订阅（本轮新发现，性价比最高的一类）

共同特征：**单账号覆盖多家模型 + 官方明确允许第三方 harness + 按量或 credits 计价**，是"一个套餐不够、又不想买五家"的最优解。

| 平台 | 套餐与价格 | 额度口径 | 模型范围 | 端点 | 对 OMP |
| --- | --- | --- | --- | --- | --- |
| **Command Code** | Go \$1、**GOAT \$10**、Pro \$20、Max 10× \$100、Max 20× \$200、Provider 按量 \$15 起 | 月度 credit 池 + 5h/周窗口；GOAT \$70 credits/月、Pro \$80、Max 10× \$150、Max 20× \$300；**额外购买的 credits 不过期且不受窗口限制** | Go 44 个模型（开源全系 + GPT-5.6 Luna + Grok 4.5 + Qwen Max/Plus）；Pro 63 个（+Claude/GPT/Gemini）；Max 含全部 71 个 | `https://api.commandcode.ai/provider/v1`（OpenAI + Anthropic） | **可接**，但官方写明"除 Go 外每个计划都有 API 访问"→ 用 **GOAT 及以上** |
| **Charm Hyper** | Free \$0、**Subscription \$20/月**、Prepaid \$5=100 / \$10=200 / \$20=400 credits | 1 Hypercredit = \$0.05；订阅口径官方未给月池换算（记 unknown）；Prepaid 永不过期 | **只含开源权重模型**：DeepSeek V4.1 Flash/V4 Pro、GLM-5～5.3、Kimi K3/K2.7 Code/K2.6、MiniMax M3/M2.7、Qwen3.6/3.7/3.8 全系、Qwen3-Coder 480B 等 35 个 | `https://hyper.charm.land/v1`（OpenAI + Anthropic） | **可接**；官方提供 Claude Code / Codex / OpenCode / Pi / Crush / Zed 接入文档 |
| **Kilo Code（Kilo Pass）** | Starter \$19/月（\$26.60 credits）、Pro \$49（\$68.60）、Expert \$199（\$278.60）；年付 +50% bonus | 订阅额 1:1 转 paid credits + 每月免费 bonus（月付最高 +40%） | "500+ models / 60+ providers" | `https://api.kilo.ai/api/gateway`（OpenAI 兼容，baseUrl 不带 `/v1`） | **可接**；需同时持有 Kilo Pass |
| **NanoGPT** | 按量（原价、无加价、起充 \$0.10–1）+ 可选订阅 \$12/月 | 订阅按"日/周输入 token + 日图像配额"；订阅页需登录 → 额度与模型清单 unknown | 公开数千条（含社区微调） | `https://nano-gpt.com/api/v1`（OpenAI + Anthropic） | **可接**（按量侧） |
| **小米 MiMo Token Plan** | Lite \$6/¥39、Standard \$16/¥99、Pro \$50/¥329、Max \$100/¥659 | Monthly Credits：4.1B/11B/38B/82B；夜间 0.8×；超额即停服 | **仅 6 个 MiMo V2.5 模型** | `https://token-plan-cn.xiaomimimo.com/v1`（另有 -sgp-/-ams-） | **灰区**：官方规定套餐额度只能用于编程工具，禁止自动化脚本/自建应用后端 |
| **ZenMux Builder Plan** | Free \$0（无 API）、Starter \$20、Max \$100、Ultra \$200 | Flow 计量（50/300/800 Flows per 5h），10–15 RPM | "100+ models" | `https://zenmux.ai/api/v1` | **不推荐**：禁止生产/自动化滥用、RPM 极低 |
| **OpenCode Zen（按量）** | 无月费；余额 <\$5 自动充 \$20 | USD 余额，可设工作区/成员月上限 | GPT 6 Astra、GPT 5.6 Sol/Terra/Luna、Claude Fable 5.1/Opus 5、Gemini 3.x、Grok 4.6 + 国产全系 + 6 个免费模型 | `https://opencode.ai/zen/v1` | **可接**；官方"无锁定，可与任何其它编码代理一起使用"，模型托管 US |

### 2.10 火山方舟 Ark Coding Plan（字节，中国大陆）— 最便宜的大陆候选

| 项 | 事实 |
| --- | --- |
| 档位 | Lite / Pro（个人版与企业版均分两档；Pro 标"最受欢迎"） |
| 价格 | 官方活动页价格区为客户端渲染（抓取日显示"价格查询中…"）→ **刊例价 unknown**；仅确认"**限时 9.9 元起**"与连续包月 2.5 折 / 包季 4.9 折 / 包年 8.7 折。第三方称刊例 ¥40/月，**无官方出处，不作依据** |
| 额度 | **按请求次数**（非 token）：约 1,200 次/5 小时、9,000 次/周、18,000 次/月；额度全工具共享 |
| 模型 | 官方活动页列 DeepSeek-V4 系列、GLM-5.3 系列、Doubao-Seed-Evolving、Kimi-K3，支持 Auto 模式调度；卡片另列模型池 Doubao / GLM / DeepSeek / Kimi / MiniMax |
| 工具 | 官方文案"模型自由，工具不限"，列名 Claude Code、Codex CLI、TRAE、OpenCode，并称最新支持 OpenClaw、Hermes Agent、Cursor |
| 端点/协议 | **unknown**：官方文档页被 WAF 拦截（HTTP 302 + JS 工作量证明）。火山开发者社区用户投稿给出 Anthropic 兼容 `https://ark.cn-beijing.volces.com/api/coding`，**属非官方来源，不可作为采购依据** |
| 区域 | 中国大陆，人民币结算 |

**判断**：如果官方端点与协议确认可用，这将是**大陆最低价的国产主力聚合通道**（DeepSeek + GLM + Kimi + Doubao 一个订阅全包，且有人民币支付）。采购前必须先拿到官方 base_url 与协议支持清单，并确认"工具不限"是否含 OMP 类自研客户端。

### 2.11 百度千帆 Token Plan（中国大陆）

| 项 | 事实 |
| --- | --- |
| 档位与价格 | Mini **首购 ¥4.9/月**（刊例 ¥9.9）、Lite **¥19.9**（¥40）、Pro **¥99.9**（¥200）、Max **¥299.9**（¥600）；首购五折限量 |
| 额度 | 按月 **token 包**：Mini 1,000 万 / Lite 4,200 万 / Pro 2.3 亿 / Max 7 亿 tokens |
| 模型 | 官方文案"支持使用文心大模型、GLM、Kimi、DeepSeek 等顶尖模型"（未逐档列出模型与上下文） |
| 端点/协议/harness 政策 | **全部 unknown**：官方页面未给 base_url，未列 harness 名单，未声明是否允许第三方客户端 |
| 其他 | 官方文档中心侧边栏存在「Token Plan 个人版 / 企业版 / Coding Plan」三个分类，但正文为 Gatsby 客户端渲染、slug 未公开 → 企业版与 Coding Plan 全 unknown |
| 区域 | 中国大陆，人民币 |

**判断**：价格与额度口径清晰（按 token，最大 7 亿 tokens/月），但**缺端点与 harness 政策**，采购前必须登录控制台确认；否则只能视为"待验证候选"。

### 2.12 尚未取到的官方细节（汇总）

| 厂商 | 已取得 | 仍缺（影响采购） | 原因 |
| --- | --- | --- | --- |
| 字节 / 火山方舟 | 档位（Lite/Pro）、"¥9.9 起"、折扣（2.5/4.9/8.7 折）、请求数额度（1,200/9,000/18,000）、模型池、工具清单 | **官方 base_url、协议、刊例价、并发/TPM、Key 是否与按量通用** | 官方文档页 WAF 拦截；活动页价格区客户端渲染 |
| 百度千帆 | Token Plan 个人版四档价格与 token 额度、模型范围文案 | **端点、协议、harness 政策**；企业版与 Coding Plan 全部字段 | 文档正文为 Gatsby 客户端渲染，章节 slug 未公开 |
| 智谱 | V2 价格（49/149/469）、积分系数、白名单、端点 | **新版积分制实际售价**；非白名单工具的处置口径 | 订阅页为 Vue SPA，无账号不可读 |
| Kimi | 会员四档价格（49/99/199/699）、Kimi Code 模型 ID 与端点、额度机制（周刷新 + 5h 窗口） | **各档周额度数值** | 未在文档页给出数值 |
| 小米 MiMo | 四档价格与 credits、三集群端点、6 个模型 | Key 是否可跨集群；OMP 是否被判定为合规"编程工具" | 官方仅规定"仅限编程工具" |
| NanoGPT | 按量无加价、\$12/月订阅存在 | **订阅额度、包含模型、harness 限制** | 订阅页需登录 |
| Charm Hyper | 价格、credits 汇率（1 credit = \$0.05）、35 个开源模型、双协议端点 | **订阅档"250 credits refreshing daily"的月池换算** | 官方未给换算口径 |
| TRAE | 四档价格、并发云任务数 | **是否提供可导出 API Key** | 定价页只描述 IDE 内权益 |

### 2.13 Kimi 与 GLM 套餐额度对照（OMP 内置通道）

**Kimi 会员**（官方帮助中心；OMP 通道 `kimi-code`）

| 档位 | 价格 | 官方额度口径 | Kimi Code 模型权限 | 其他关键权益 |
| --- | --- | --- | --- | --- |
| Andante | ¥49/月 | 共享额度池；**Agent 用量约 30 个** | `kimi-for-coding`（K2.8 Preview）可用 | 20 项目 / 20GB；数据库 1,000 次 |
| Moderato | ¥99/月 | 约 60 个 | + `k3`、`k3-256k` | Agent 并行 2；集群 25 次；梦境记忆 |
| Allegretto | ¥199/月 | 约 150 个 | + `kimi-for-coding-highspeed`（K2.7 Code 高速） | 目标模式；Kimi Claw；集群 50 次 |
| Allegro | ¥699/月 | 约 360 个 | 同上 | Agent 并行 4；**百万 tokens 超长对话容量**；集群 120 次 |

- **官方未公布 token 额度**：Kimi 以"共享额度池 + 未用不累积"计量，公布的是"Agent 用量约 N 个"和数据库调用次数；Kimi Code 另有 **5 小时 + 每周限额（数值未公布）**。
- 额度池为全功能共享（网页、深度研究、Office、Kimi Code、Kimi Work、Claw 共用），任一功能耗尽会影响其它功能。
- 溢出：可购"加油包"（费率≈开放平台 API 价），余额不过期、可与订阅叠加。
- 性价比参考：K3 按量 API 为 ¥2（缓存命中）/¥20（未命中）/¥100（输出）每百万 tokens；订阅档把"每个编码任务的等效成本"压到 ¥1–2 量级。
- 一处**表述冲突需实测**：Kimi Code 文档称 `k3`（1M 上下文）"Allegretto 及以上解锁"，帮助中心则把"百万 Tokens 超长对话容量"列在 Allegro；建议先在目标档位实测 `k3` 的可用上下文。

**GLM Coding Plan**（官方文档；OMP 通道 `zhipu-coding-plan` 或 `zai-coding-plan`）

| 档位 | 价格（V2 口径，元/月） | 积分/5h | 积分/周 | GLM-5.3 tokens/周（95% 缓存） | GLM-5.3-Flash tokens/周 | 折算 tokens/月（×4.3） |
| --- | --- | --- | --- | --- | --- | --- |
| Lite | 49（年付 39.2） | 2,000 | 10,000 | 0.48–0.97 亿 | 1.46–2.92 亿 | GLM-5.3 约 2.1–4.2 亿 / Flash 约 6.3–12.6 亿 |
| Pro | 149（年付 119.2） | 12,000 | 60,000 | 2.90–5.80 亿 | 8.77–17.55 亿 | 约 12.5–24.9 亿 / 约 37.7–75.5 亿 |
| Max | 469（年付 375.2） | 28,000 | 140,000 | 6.76–13.52 亿 | 20.47–40.95 亿 | 约 29–58 亿 / 约 88–176 亿 |

- 积分公式：（输入 ×6.9 + 缓存命中 ×1.7 + 输出 ×24）/10000（GLM-5.3）；Flash 为 2.3/0.56/8；MCP 按调用次数 ×输出系数。
- 5 小时额度 = 周额度 ×20%，故 5h 可用 tokens ≈ 周值 ×20%。
- 非高峰按 50% 抵扣（高峰 = 工作日 14:00–18:00 UTC+8），周末全天算非高峰。
- 区间为"全高峰（低值）～全非高峰（高值）"，实际取决于缓存命中率与峰谷分布。
- 额度耗尽必须等下一个 5 小时周期，**不会自动消耗余额**。

### 2.14 只买 2～3 个套餐如何覆盖 doc-01 组合

doc-01 的组合是：Owner（Kimi K3）+ 深评（GLM-5.3）+ UI/视觉（GLM-5.3-Flash 或 Seed2.1 Pro）+ 执行（DeepSeek V4.1 Flash）。按"订阅数最少"重排：

| 角色 | 覆盖通道 | 是否需要新订阅 |
| --- | --- | --- |
| Owner / 规划 / 跨仓综合 | Kimi 会员 Allegretto（¥199，`k3`） | 订阅 1 |
| 深度只读评审（GLM-5.3） | GLM Coding Plan Pro（¥149） | 订阅 2 |
| UI / 视觉 / 前端复核（GLM-5.3-Flash，含视觉理解 MCP） | 同上 GLM 套餐额度内 | 复用订阅 2 |
| 研究 / 长文（1M 上下文） | Kimi K3（共享额度池）或 GLM-5.3 | 复用订阅 1/2 |
| **执行档（侦察、有界实现、门禁/叶子执行、机械文档）** | **DeepSeek 官方按量**（¥1/百万 input 谷时，并发 2500） | **不需要订阅**（按量账号） |

**结论：2 个订阅 + 1 个按量账号即可闭环**，月固定成本 ≈ ¥348（约 \$48）+ DeepSeek 按量（通常几十元）。

若坚持"不想有按量账单 / 执行也要订阅"，第三个套餐按贴合度排序：

1. **opencode Go（\$10/月）**——最贴合：明确允许第三方 Agent，且额度池含 DeepSeek V4.1 Flash（\$60/月）、GLM-5.3-Flash（\$60）、MiniMax M3（\$60），正好覆盖执行与研究；
2. **火山方舟 Ark Coding Plan（¥9.9 起）**——最便宜，含 DeepSeek-V4 / GLM-5.3 / Kimi-K3 / Doubao-Seed，但**官方端点与协议未确认**；
3. **Command Code GOAT（\$10/月 = \$70 credits，不过期）**——适合当"额度池"，含 GPT-5.6 Luna 与 Grok 作第二意见。

**两个仍需你决策的缺口**：

1. **GLM 套餐的条款灰区**：OMP 内置支持 coding 端点，但智谱白名单未含 OMP。接受灰区，或 GLM 改用 `zai` 按量（OMP 内置、零条款风险、按 token 付费）。
2. **视觉/UI 的独立性**：用 GLM-5.3-Flash 意味着 Owner=Kimi、评审+视觉=GLM 同厂（异厂要求仍满足，但视觉与评审同厂）。若要 doc-01 方案 A 的"字节系视觉"，需要第 3 个订阅（火山/TRAE）。

## 3. 推荐采购组合

### 方案 A：最小可用（约 \$20–40/月，先验证链路）

| 角色 | 通道 | 月成本 |
| --- | --- | --- |
| 全部国产模型试跑 + 广度兜底 | **opencode Go** | \$10 |
| Credits 池（含 GPT-5.6 Luna / Grok / Qwen Max，附加 credits 不过期） | **Command Code GOAT** | \$10 |
| 执行档 | DeepSeek 官方按量 | 按用量（谷时极低） |
| Owner / 评审 | 先用上面两个订阅内的 Kimi K3、GLM-5.3 额度验证 | \$0（含在订阅内） |

适用：验证 OMP 接入并度量真实 token 消耗，再决定升档。缺点是 Go 内 Kimi K3 / GLM-5.3 各仅 \$15/月额度，Owner 与评审很快耗尽。

### 方案 B：推荐组合（最优性价比，约 \$60–100/月 + ¥99–199）

| 层 | 采购 | 月成本（官方价） | 承担角色 |
| --- | --- | --- | --- |
| 广度 + 免费档机械任务 | **opencode Go** | \$10 | GLM-5.3-Flash（视觉/前端复核，\$60 额度）、MiniMax M3（研究，\$60）、DeepSeek V4.1 Flash（执行兜底，\$60 促销）、Qwen3.7 Plus、MiMo、LongCat、Hy3 |
| Credits 池 + 闭源兜底 | **Command Code GOAT**（升 Pro \$20 可加 Claude/GPT/Gemini） | \$10 | credits 不过期、不受窗口限制；含 GPT-5.6 Luna、Grok 4.5、Qwen Max/Plus |
| Owner（K3 1M 上下文） | **Kimi 会员 Moderato ¥99 / Allegretto ¥199** | ¥99–199 | outcome、规划、跨仓合同、最终综合 |
| 评审 + 视觉（GLM-5.3） | **智谱按量 API**，或 **Charm Hyper Prepaid \$20=400 credits**（仅开源模型、永不过期） | 按量 / \$20 | GLM-5.3 异厂深评、GLM-5.3-Flash 视觉复核 |
| 执行档 | **DeepSeek 官方按量**（谷时排程） | 估 \$20–60 | 侦察、有界实现、叶子执行、机械文档 |
| **合计** | | **≈ \$60–100 + ¥99–199（约 ¥530–920/月）** | 覆盖结论记录 01 的全部角色 |

### 方案 C：高吞吐（约 \$200–300/月）

在方案 B 基础上：Kimi 会员升 **Allegro ¥699/月**（4 路 Agent 并行 + K3 百万上下文）、Command Code 升 **Max 10× \$100**（\$150 credits/月）、MiniMax Token Plan **Max \$55/月**、Kilo Pass **Pro \$49/月**作为跨 IDE/CLI/云 Agent 的统一 credits 池、opencode Zen 按量作为 GPT 角色与额度溢出备份。

### 选购优先级（能接 + 便宜 + 覆盖广）

1. **opencode Go \$10/月** — 一个 key 覆盖 20+ 国产模型，官方允许第三方 Agent（需自定义 UA + 会话头）。
2. **Command Code GOAT \$10/月** — \$70 credits/月，附加 credits 不过期，含 GPT-5.6 Luna 与 Grok，双协议。
3. **Kimi 会员（¥99/¥199）** — K3 Owner 的唯一经济通道。
4. **Charm Hyper Prepaid \$20** — 只含开源模型、低于原厂、credits 永不过期（GLM/Kimi/DeepSeek/Qwen 全在）。
5. **MiniMax Token Plan Plus \$22** — M3 研究 + 图像/语音共享额度，官方明确支持自定义端点。
6. **智谱按量 API** — 要 GLM 又不进白名单工具时的正解。
7. **DeepSeek 官方按量** — 执行档必备，谷时最便宜、并发 2500。
8. 备选：Kilo Pass（bonus credits 与多 IDE/云 Agent）、NanoGPT（按量无加价）、opencode Zen（GPT 角色备份）。

### 合规置信度排序（接 OMP 的关键判据）

| 通道 | 官方是否允许第三方 harness | 结论 |
| --- | --- | --- |
| opencode Go / Zen | 明确："适用于 OpenCode 以及其他会产生类似请求的编程 Agent"，并给出已验证客户端清单 | **可接**（保持真实 UA 与会话头） |
| MiniMax Token Plan | 明确列出 "Other Tools：任何支持自定义 OpenAI/Anthropic 兼容端点的编程工具" | **可接** |
| Kimi Code（会员） | **OMP 内置 `kimi-code` provider**（OAuth device-code + `KIMI_API_KEY`，baseUrl `https://api.kimi.com/coding/v1`，模型 k3/k3-256k/kimi-for-coding/kimi-for-coding-highspeed）；官方提供 Claude Code / OpenCode / Codex 接入，要求保持工具真实身份 | **可接**（`k3`/`k3-256k` 不伪装 UA；`kimi-for-coding`/`kimi-k2` 在 OMP 内会带 `User-Agent: KimiCLI/1.0`，属灰区，建议 Owner 用 `k3`/`k3-256k`） |
| 智谱 GLM Coding Plan | **OMP 内置 `zhipu-coding-plan` / `zai-coding-plan`**（含 coding 端点）；但条款白名单为 ZCode、Claude Code、Codex、OpenCode、Pi、TRAE、Cursor、Cline、Kilo、Qoder、Cherry Studio、OpenClaw、Hermes 等，协议禁止"自建应用/机器人/网站/SaaS 直接调用模型接口" | **技术可接、条款灰区**：OMP 是编码 Agent 而非自建应用，但不在白名单；零风险方案改用 `zai` 按量 |
| 阿里云百炼 Coding Plan | 明文"严禁 API 调用"，仅限编程工具内交互式使用 | **不可接**（只买给 IDE/CLI 用） |
| 字节 TRAE | 面向 IDE/云任务，未见对外 API 说明 | 工具型，不进 OMP |
| Command Code | Provider API 官方支持任意 OpenAI/Anthropic 兼容客户端；但 Go 套餐不含该通道 | **可接**（用 GOAT/Pro/Max/Provider） |
| Charm Hyper | 官方提供 Claude Code / Codex / OpenCode / Pi / Zed 等第三方接入文档 | **可接** |
| Kilo Code | Kilo Pass 权益写明可在 IDE、CLI、Cloud 与直接 API 访问中使用 | **可接**（需 Pass + Gateway） |
| 小米 MiMo Token Plan | 官方规定套餐额度只能用于编程工具，禁止自动化脚本、自定义应用后端 | **灰区**（OMP 类自研 Agent 官方未表态） |
| ZenMux Builder Plan | 订阅禁止生产/自动化滥用、多账号池化，且 10–15 RPM | **不推荐** |
| DeepSeek / 各家按量 API | 无工具限制 | **可接** |

### 明确不建议

- **只买一个套餐**：单套餐的 5 小时 + 周窗口一定会在密集开发日打满（见第 1 节约束 3）。
- **把「仅限指定工具」的套餐接进 OMP**：阿里 Coding Plan 明文禁止 API 调用；智谱限指定工具列表。要用就在官方支持的工具里用，或者在 OMP 改用对应厂商的**按量 API**。
- **账号共享或多人共用一个套餐**：三家都在协议里写明禁止，风险是限流、冻结、封号。
- **把 GPT 角色全部押在单一第三方通道**：GPT 5.6 Sol / Astra 在 opencode Zen 有按量与折扣，但仍属外部依赖，需保留第二通道。

## 4. 接入 OMP 的落地方式

全部按量通道与允许第三方 Agent 的订阅通道，都走同一套 OMP provider 机制：

1. 在 Profile 的 `models.yml` 增加 provider（示例形状，凭据只放钥匙串，不写入仓库）：
   - `opencode-go` → `baseUrl: https://opencode.ai/zen/go/v1`，`api: openai-completions`
   - `kimi-code` → `baseUrl: https://api.kimi.com/coding/v1`，`api: openai-completions`（保持真实 UA）
   - `deepseek` → `baseUrl: https://api.deepseek.com`（已存在）
   - `minimax` → `baseUrl: https://api.minimaxi.com/v1` 或 `.../anthropic`（本机已发现）
2. 在 `modelRoles` 绑定角色，并同步 `models/catalog.yaml` 的 `ompResolvedSelectors`；用 `python3 scripts/check_model_routes.py` 核对漂移。
3. 用 `task.agentModelOverrides` 保证泛型 `task`/`scout`/`sonic` 落在执行档（现有机制，见 [`context-economy.md`](../../workflows/context-economy.md) 第 4 节）。
4. 前 10 个任务用 `.agents/scripts/workflow_eval.py` 记录 token、成本与保留档占比，作为是否升档的依据。

**注意**：接入前先确认该套餐条款是否允许第三方 harness；不允许的，改为按量 API 采购。OMP 本身不在任何厂商的「已验证客户端」白名单里，属于需要自测的路径。

## 5. 待复核清单（购买前在控制台完成）

**已取得**：opencode Go/Zen、Command Code、Charm Hyper、Kilo Pass、NanoGPT、小米 MiMo、ZenMux 的价格与额度；智谱 V2 价格（49/149/469 元）与积分系数；Kimi 会员四档价格（49/99/199/699 元）；阿里 Coding Plan 大陆 ¥200 / 国际 \$50；MiniMax Token Plan（\$22/\$55/\$132）；DeepSeek 双币种价目与并发；TRAE 四档价格；百度千帆 Token Plan 个人版四档价格与 token 额度。

**仍需人工确认（影响能否采购）**：

1. **火山方舟 Ark Coding Plan 的官方 base_url 与协议**（官方文档被 WAF 拦截；社区文章不可作依据），以及 Pro 档刊例价、并发/TPM、订阅 Key 是否与按量 Key 通用；
2. **百度千帆 Token Plan 的端点、协议与第三方 harness 政策**（官方给的是 token 额度但无 base_url），以及 Token Plan 企业版 / Coding Plan 详情；
3. **智谱新版积分制套餐的实际售价**（V2 价 49/149/469 已确认，新版以订阅页为准）与是否允许非列表工具；
4. **Kimi Code 周额度的数值口径**；
5. **小米 MiMo 套餐 Key 是否可跨集群使用**、OMP 是否被判定为合规"编程工具"；
6. **NanoGPT \$12/月订阅**的额度、包含模型与是否限制第三方 harness（订阅页需登录）；
7. **Charm Hyper 订阅档"250 credits refreshing daily"的月池换算**；
8. **TRAE 是否提供可导出 API Key**（决定能否进 OMP）；
9. 各家的**并发/TPM 硬限制数值**（多数未公布）。

## 6. 来源

- opencode：[Go](https://opencode.ai/docs/zh-cn/go/)、[Zen](https://opencode.ai/docs/zh-cn/zen/)
- 智谱：[套餐概览](https://docs.bigmodel.cn/cn/coding-plan/overview)、[使用须知](https://docs.bigmodel.cn/cn/coding-plan/usage-notes)、[常见问题](https://docs.bigmodel.cn/cn/coding-plan/faq)、[API 定价](https://docs.bigmodel.cn/cn/guide/start/pricing)
- Kimi：[Kimi Code 概览](https://www.kimi.com/code/docs/)、[会员权益](https://www.kimi.com/code/docs/kimi-code/membership.html)、[产品对比](https://platform.kimi.com/docs/guide/product-plans)、[模型定价](https://platform.kimi.com/docs/pricing/chat)
- MiniMax：[Token Plan 定价](https://platform.minimax.io/docs/guides/pricing-token-plan)、[文档索引](https://platform.minimax.io/docs/llms.txt)
- 阿里云：[Coding Plan 概述](https://www.alibabacloud.com/help/zh/model-studio/coding-plan)
- 字节：[TRAE 定价](https://www.trae.ai/pricing)
- Kimi 帮助中心：[会员订阅服务权益介绍](https://www.kimi.com/help/membership/membership-overview)
- 智谱：[老用户权益说明（含 V2 价格）](https://docs.bigmodel.cn/cn/coding-plan/notice/usage-revision)
- DeepSeek：[Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing)
- 本机事实：`~/.omp/profiles/team-os/agent/models.db` 已发现 `alibaba-coding-plan`、`minimax-code`、`minimax-code-cn`、`xiaomi-token-plan-{cn,ams,sgp}`、`commandcode`、`charm-hyper`、`kilo`、`zenmux` 等套餐/聚合端点（2026-09-16 快照）

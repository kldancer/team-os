# 04-结论记录-jev-System-One模型引入Team-OS工作流工厂调研

> 调研日期：2026-09-21。基于 TypeSafe 官方文档（docs.typesafe.ai：System One、Primitives、Patterns、Cookbooks、Agent Skill）与 Team OS 工作流工厂现状（team-os `AGENTS.md`、`docs/使用手册/02-Pi-OMP-Team-OS工作流原理与日常使用.md`）的分析结论。
>
> 注：调研输入中含三条 X 帖子链接，因 X 反爬拦截无法读取；官方文档已覆盖完整技术实质，不影响结论。

> 问：
```
快速了解当前的team-os omp工作流“工厂”架构 /Users/kailonyang/go/src/team-os/AGENTS.md、docs/使用手册/02-Pi-OMP-Team-OS工作流原理与日常使用.md，然后这里有一系列关于模型jev的官方文档、博客、文章，你详细阅读掌握
    jev核心思想、工作原理和使用场景：https://docs.typesafe.ai/primitives 、 https://x.com/_avichawla/status/2101563610644496464?s=46&t=38_Wzc7TsG02T6arN8Xd2A
 、https://x.com/layton_gott/status/210145012046617435
    1?s=46&t=38_Wzc7TsG02T6arN8Xd2A 、 https://x.com/ai_xiaomu/status/2101135680168771979?s=46&t=38_Wzc7TsG02T6arN8Xd2A 。
 然后你分析一下，当前的team-os工作流工厂中是否值得引入jev，如果值得，能给工厂的哪些方面带
 来实质性提升？分析好后不要篇大论，形象详细明了的给我讲解清楚你的结论。
```

# 结论先行

**值得引入，但定位必须收窄：jev 不进工厂的角色档位表，而是进脚本层——作为"判断引擎"服务 `juspctl`、request compiler、Gate 这些今天靠启发式规则或昂贵 LLM 调用做分类的地方。**

# jev 是什么（一句话）

jev 是 TypeSafe 的 System One 模型：**不生成文字，只做判断**。你给它一段 state + 若干带类型的"问题"（Choice 选一项 / Score 打等级 / Noul 判是非），它返回类型化答案 + **校准过的概率和置信度**，~100ms 一次调用，13 个问题打包一问便宜 12 倍、快 10 倍。

和普通 LLM 的分工：

```
LLM（现在用的）:  开放式生成 → 写代码、写计划、综合、解释
jev（System One）:  封闭式判断 → "这条输入属于 A/B/C 哪一类？概率多少？"
```

# 为什么和工厂架构天然契合

工厂现状存在一个结构性错配：**很多环节本质是"判断"，却由"生成型"模型在做，或者干脆退化成脆弱的 if/else。**

| 工厂环节 | 现在怎么做 | 本质是什么 |
|---|---|---|
| 意图分类（diagnose / design / deliver-change / review / guard / ship 六选一） | Owner LLM 读全句判断 | 一个 Choice 问题 |
| Skill 命中（十几个 Skill 按需加载） | Owner 凭上下文判断 | jev 官方 cookbook 的原型场景：一次请求排序 182 个 skill |
| solo vs 派 worker、派哪一档 | Owner 判断 + `route_work.py` 启发式 | Choice + Score |
| Gate 前置筛查、收据核对 | 规则脚本 / Owner 读收据 | Noul："这份证据是否满足验收？" |
| 授权边界识别（生产写？删除？破坏性？） | Owner 红线判断 | 高价值 Noul，带置信度可 fail-closed |

jev 文档里的 intent routing 和 guardrails 两个 pattern，几乎就是工厂第 3 节"意图分类"和第 1 节"安全红线"的机器化版本。

# 引入后的五个实质性提升

**1. 意图分类从"LLM 手感"变成"可测的机器路由"**
现在 request compiler 的分类质量随 Owner 模型和上下文长度漂移。换成 jev：state = 用户原话 + 项目 task 摘要，一个 Choice 六选一 + 一个 Noul"是否涉及生产/远端写"。~100ms、可离线回放测试、误判可量化。置信度低时自动升级给 Owner 判断——这正是 confidence-gated routing pattern。

**2. Skill 命中从"全部加载"或"凭感觉"变成一次排序调用**
Team OS 明确要求"Skill 按需加载、控制上下文噪声"，但命中判断本身就在烧 Owner 上下文。jev 的 skill suggestion cookbook 做的就是这事：一次请求对全部 Skill 描述打分，只把 top-K 正文装进上下文。工厂 Skill 越多收益越大。

**3. 红线判断 fail-closed 化**
"这条请求是否授权生产写 / 删除数据 / 外部发送"是工厂最不能错的判断。jev 的 Noul 返回校准概率，规则可以写成：`P(生产写) > 0.3 且无明确授权 → 强制停下询问`。比正则关键词（漏）和 LLM 自由判断（漂移）都稳，且每次判断留有概率收据，进 `.work` 可审计。

**4. 脚本层获得"可编程常识"**
`check_role_routing.py`、`route_work.py`、`juspctl close` 今天只能做机械核对（档位分布、收据存在性）。接上 jev 后能做语义核对：close 前问一句"收据摘要是否真的支撑验收结论"——Guard 从"文件在不在"升级为"证据成不成立"，而不必唤醒一个完整 LLM。

**5. 成本和延迟**
判断类调用从"一次 Owner LLM 回合（秒级、烧上下文窗口）"降到 ~100ms API 调用，13 问打包近免费。对批量场景（一次审几十个文件、几十条收据）是数量级差距。

# 不该用 jev 的地方（同样重要）

- **Owner 综合、规划裁决、最终报告**——这是生成和推理，jev 根本不输出文字；
- **任何角色档位**——`plan_owner`/`deep_review`/`fast_worker` 的职责是产出工件，不是做单点判断；
- **低频、一次性的判断**——jev 的价值在"同一判断高频重复 + 需要一致性"，一次会话里只做一两次的判断让 Owner 顺手做掉更省。

# 边界条件

- jev 是**外部 SaaS API**，state 会出网。判路由/Skill 命中的 state 只是用户原话和任务摘要，风险低；但**绝不能把代码 diff、收据全文、项目机密送进 jev**——这与"凭据不出域"的红线一致，需要在引入时写死 state 白名单；
- 文本-only，不能看截图，UI 视觉验收仍归 `@ui_qa`；
- 需要一个轻量 fallback：jev 不可用时路由退回现有启发式 + Owner 判断，不允许成为硬依赖。

# 建议的最小试点

选**一个**环节先验证：意图分类。在 request compiler 里加一条 jev Choice（六类流程所有者）+ Noul（生产写检测），与现有 Owner 判断并行跑一段时间，用 `.work` 记录两边分歧率。分歧率低且置信度分布合理 → 推广到 Skill 命中和 Gate 预筛；分歧率高 → 只保留生产写检测这一个高价值 Noul，其余撤回。投入是一个 SDK 封装 + 两条脚本改造，不触碰任何角色合同。

一句话总结：**工厂今天的瓶颈不在"没人会想"，而在"想"和"判"混在一台昂贵的生成引擎里；jev 把"判"拆出去，让脚本层第一次拥有便宜、快、带置信度、可审计的判断力。**

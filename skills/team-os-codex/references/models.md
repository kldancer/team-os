# GPT‑6 Astra 与 GPT‑6 Sol 的 Codex 适配

## 已核实的能力与本地策略

官方将 Astra 定位为复杂端到端工作的模型；Sol 支持复杂编码和 Agent 工作流。两者都能作为唯一 Owner，不建立 Astra 规划 → Sol 执行 → Astra 审批的固定队列。

| 模型 | 本地使用建议（不是效果保证） | 指令重点 |
| --- | --- | --- |
| GPT‑6 Astra | 高歧义、跨边界设计与集成、复杂研究或综合 | 给结果、约束与完成证据；省掉强制全图扫描、角色接力和重复验证；已有授权内继续到闭环 |
| GPT‑6 Sol | 常规及复杂编码、定位修复、有明确边界的纵向交付 | 给具体目标、相关接口、失败案例和可执行验收；需要时分小批次反馈，不降级验收标准 |

以上分配是可调整的工作假设。官方没有证明本项目上两者的速度、成本或成功率差异；按实际遗漏、返工、用户纠偏和有效证据评估，不以模型名字推断质量。

## 同一合同，不同提示粒度

Astra：说明“完成后什么成立”，允许模型选择路径。官方指出它可能因澄清和严格遵从 Skill 而提前停止，也可能扩大测试；因此边界写清“普通本地失败由原 Owner 修复”，并只跑项目判定适用的验证。

Sol：保持同一结果和自主权；接口或验收不清时提供一个具体输入/输出或失败场景，不把每个 shell 动作写成流程。不能根据旧版 GPT‑5.6 Sol 的经验推断 GPT‑6 Sol 的行为。

保留当前模型和 reasoning，用户要求切换时使用实际 Codex 界面或受支持配置并确认生效。只修改 Prompt 不算切换。配置值是 configured，不等于本次实际 resolved；无法观测的字段记 null。模型不可用时报告阻塞，继续不依赖该模型的工作，不静默替换 Provider。

不要把 API 的参数全集复制为 Codex 支持矩阵。Astra 的 API 不支持 `none`，Sol 的 API 支持它；Codex App、CLI 和某一主机提供哪些档位，以当次可选能力为准。本适配不改用户 config.toml，不自动提高推理档位。

## 依据

- [GPT‑6 模型与提示指导](https://developers.openai.com/api/docs/guides/latest-model)：Astra 的持续推进、指令敏感性、验证与协作行为。
- [Astra Skills 与 Prompt 指导](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)：短描述、按需展开与授权边界。
- [GPT‑6 Sol 模型说明](https://developers.openai.com/api/docs/models/gpt-6-sol)：复杂编码、Agent 工作流和 API 能力。

模型/API 的能力不等于某次 Codex 会话工具可用或已授权。升级时核对当前官方文档与实际运行时，不在长期合同中固化价格、额度或性能排名。

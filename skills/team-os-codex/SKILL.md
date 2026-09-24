---
name: team-os-codex
description: 在 Codex 中绑定项目机器计划、恢复 Team OS 任务、选择协作与浏览器通道；不替代项目交付流程。
---

# Codex 运行适配

共享 Team OS 的 outcome、单一 Owner、按需协作与收据语义。项目流程 Skill 仍是唯一流程所有者；这里仅把结果映射到 Codex，不调用 OMP 配置或服务。

- 日常实现：读取项目事实和当前结果后直接工作；项目要求计划时使用项目 planner。不要为一个小修改先运行适配器体检。
- 计划绑定或跨会话恢复：读 [项目执行桥](references/execution.md)。`scripts/project_bridge.py` 提供本地计划入口、计划指纹绑定和只读恢复检查；它不授予远端权限、不执行部署、不代替项目 close。
- 独立取证、并行实现或高风险审阅：读 [协作与隔离](references/collaboration.md)。默认继续当前模型；能力、状态和停止通道不可检查时保持 solo。
- 真实页面或 UI 验收：读 [Codex 浏览器证据](references/browser.md)。遵守当前浏览器工具返回的 API 文档，不能复制 OMP Eval 调用。
- 用户选择 Astra/Sol、迁移模型或出现流程性停顿：读 [模型适配](references/models.md)。两者均可当 Owner；这里的工作分配建议不自动切换模型。

已授权的可逆本地工作持续到适用验收闭合。机器计划说要冻结才冻结；普通失败返回原 Owner 修复。工具或生产入口未验时明确写“未验”，不能用脚本单测冒充完整交付。项目没有 Runner 时使用项目本身的构建/测试与 `.work` 紧凑交接；不要假造 `juspctl` 或创建第二套任务数据库。

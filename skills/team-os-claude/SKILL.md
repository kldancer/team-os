---
name: team-os-claude
description: 在 Claude Code 中选择协作与隔离方式、浏览器取证通道、长命令与跨会话恢复；不替代项目交付流程。
---

# Claude 运行适配

共享 Team OS 的 outcome、单一 Owner、按需协作与收据语义。项目流程 Skill 仍是唯一流程所有者；这里仅把结果映射到 Claude Code，不调用 OMP 或 Codex 的配置与服务。

- 日常实现：读取项目事实和当前结果后直接工作；不要为一个小修改先做适配体检。
- 独立取证、并行实现或高风险审阅：读 [协作与隔离](references/collaboration.md)。默认继续当前模型；状态和停止通道不可检查时保持 solo。
- 真实页面或 UI 验收：读 [Claude 浏览器证据](references/browser.md)。
- 长命令、构建刷新、换会话或恢复：读 [执行与恢复](references/execution.md)。

已授权的可逆本地工作持续到适用验收闭合。普通失败返回原 Owner 修复。工具或生产入口未验时明确写“未验”，不能用脚本单测冒充完整交付。项目没有 Runner 时使用项目本身的构建/测试与 `.work` 紧凑交接；不要假造 `juspctl` 或创建第二套任务数据库。

---
name: team-os-browser-verify
description: 为真实网页入口提供高效浏览器取证；按确定性流程、OMP Eval、Chrome DevTools 和探索性工具选择最小通道，输出脱敏浏览器收据。不拥有业务交付或生产授权。
---

# 真实浏览器取证叠加层

本 Skill 只补浏览器工具路由和证据纪律，不重建交付流程、UI 设计或项目 Gate。完整方法见 [`real-browser-verification.md`](references/real-browser-verification.md)。

## 最小规则

- 已知入口和断言优先 `playwright-cli` named session；已登录或需要探索时用 OMP `browser` Eval 的 named tab；Network、Console、Trace 和性能交给 Chrome DevTools CLI/MCP。
- OMP Relay 必须显式 `app.target`；不要接管可见前台 tab。每个任务只使用一个语义化 Session/Tab。
- 已知 selector 直接动作；未知结构才观察。把动作、等待和断言批量放进一次 CLI 命令链或 `tab.run`，页面改变后再定向观察。
- DOM/ARIA、URL、Network 和 Console 是主证据；截图只用于视觉节点、失败定位或明确要求的场景。
- 收据写入项目 `.work/tasks/<task>/evidence/browser/<scenario>/`，只保存脱敏摘要、截图路径、结果和未验项；不得写入凭据、Cookie、真实 Session ID 或完整 Transcript。
- `agent-browser`、Stagehand、Browser Use 仅作探索性 fallback；成功流程应固化为确定性 CLI、项目 E2E 或 `tab.run`。

# Claude 浏览器证据

项目流程和 UI 设计基线保持权威，浏览器只提供事实。共享文档里的 OMP Eval、Relay、`tab.run` 与 Codex 浏览器工具不适用于 Claude。

优先复用项目已有可重复浏览器验证（Playwright 脚本、CLI）；需要实时页面、登录态或探索时使用当前会话实际提供的通道：桌面端内置浏览器、用户明确要求时的 Claude in Chrome，或已配置的 Playwright MCP。先读对应工具的 Skill 或返回的文档，使用真实观察到的入口、元素和状态；站点未获批准或访问受限时如实记录，不用其他路径绕过。登录由用户完成，不代填真实凭据。

Network/Console 只在工具实际提供时采集，不承诺工具没有的能力。读取页面优先用文本/可访问性树，截图用于视觉、失败定位与目标对照；DOM、行为和业务结果分别验证。明确目标 tab 与视口，避免两套工具同时操作一个页面；可预见的连续动作批量执行。

收据放项目 `.work/tasks/<task>/evidence/browser/<scenario>/`：scenario、route、脱敏 target、候选身份、viewport、pass/fail/blocked、断言、截图引用和 unverified。登录态、Cookie、凭据、完整响应和真实 Session ID 不进入收据。没有浏览器条件就记录未验，不能用 build 成功替代真实入口。

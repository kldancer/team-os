# Codex 浏览器证据

项目流程和 UI 设计基线保持权威，浏览器只提供事实。共享文档里的 OMP Eval、Relay 与 `tab.run` 不适用于 Codex。

优先复用项目已有可重复浏览器验证；需要登录态、实时页面或探索时使用当前已连接的 Codex 浏览器/Computer Use 工具。先读工具技能或工具返回的文档，使用真实观察到的入口、元素和状态；专属浏览器工具有访问限制时不得用其他路径绕过。Network/Console/性能只在已提供诊断工具时采集，不承诺工具没有的能力。

明确目标 tab 与视口，避免同时由两套工具操作一个页面。已知元素可直接操作，导航或重渲染后再定向观察；批量只做相互依赖已明确的步骤。截图用于视觉、失败定位与目标对照，DOM、行为和业务结果分别验证。

收据放项目 `.work/tasks/<task>/evidence/browser/<scenario>/`：scenario、route、脱敏 target、候选身份、viewport、pass/fail/blocked、断言、截图引用和 unverified。登录态、Cookie、凭据、完整响应和真实 Session ID 不进入收据。没有浏览器条件就记录未验，不能用 build 成功替代真实入口。

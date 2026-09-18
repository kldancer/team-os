# 真实浏览器验证工作流

本文只定义浏览器取证的工具路由、Session 生命周期和证据收据，不替代项目业务合同、UI 设计、机器 Gate 或生产授权。一个结果仍由原 owner 持有；浏览器只是取证执行器。

## 1. 按任务选择通道

| 场景 | 首选通道 | 结果 |
| --- | --- | --- |
| 已知入口、步骤和断言 | `playwright-cli` + named session | 可重复动作、短输出、结构化收据 |
| 已登录 Chrome、未知页面或需交互探索 | OMP `browser` Eval + named tab | 复用登录态、批量 JS 操作、定向观察 |
| Network、Console、性能或 Trace 证据 | Chrome DevTools CLI/MCP | 请求、错误和性能原始事实 |
| 页面未知且无法快速固化步骤 | OMP `observe`/`ariaSnapshot`；必要时临时使用 `agent-browser`/Stagehand | 探索结果，不升级为默认主链 |

不要让多套工具同时负责同一动作。CLI 负责确定性流程，OMP Browser 负责实时页面，DevTools 负责诊断证据。

## 2. 最短闭环

1. 为每个任务创建一个语义化 Session/Tab；Relay 必须提供 `app.target`，不接管当前可见 tab。
2. 已知 selector、role 或 testid 时直接操作；只有未知结构、导航或重新渲染后才重新观察。
3. 把导航、动作、等待和断言放进一次 CLI 命令链或一次 `tab.run`；不为每个点击单独启动模型回合。
4. DOM/ARIA、URL、Network 和 Console 是主证据；截图只用于视觉判断、失败定位或明确要求的节点。
5. 输出最小结构化收据到项目 `.work`，只保留脱敏的 URL、状态、请求摘要、截图路径、结果和未验项。

## 3. 通道规则

### 3.1 Playwright CLI

确定性流程优先使用 `playwright-cli -s=<task>`。Session 内复用 Cookie/storage；需要跨进程或重启复用时使用 persistent profile 或 storage state。快照限定 selector、深度或交互元素，动作完成后只在页面状态变化时再次取快照。

### 3.2 OMP Browser Eval

使用 `browser.open({ name, app: { relay: true, target } })` 建立具名 tab；使用 `tab.run` 批量执行动作、等待和结构化断言。导航或重渲染会使旧 ref/handle 失效，应在同一 Eval 中重新观察后再操作。不要用无 target 的 Relay 调用导航用户前台 tab。

### 3.3 Chrome DevTools

基础页面任务使用 `--slim` 或 CLI；只有需要 Network、Console、Trace、性能或内存诊断时才启用完整工具面。网络收据只保留方法、脱敏 URL、状态、关键响应字段和请求 ID，不保存 Cookie、Authorization 或完整响应秘密。

### 3.4 探索性工具

`agent-browser`、Stagehand 或 Browser Use 只在页面未知、流程不稳定或需要临时探索时接入；探索成功后把稳定步骤固化到 Playwright CLI、项目 E2E 或 OMP `tab.run`，不把 Agent 自主导航作为长期回归入口。

## 4. 证据收据

推荐路径：`.work/tasks/<task>/evidence/browser/<scenario>/receipt.json`，至少包含：

```json
{
  "scenario": "<name>",
  "route": "playwright-cli | omp-eval | chrome-devtools",
  "target": "<redacted-url-or-workspace-key>",
  "commit": "<commit>",
  "viewport": "<width>x<height>",
  "result": "pass | fail | blocked",
  "dom": {"url": "<redacted>", "assertions": []},
  "network": [{"method": "GET", "path": "<redacted>", "status": 200}],
  "console": {"errors": 0},
  "screenshots": [],
  "unverified": []
}
```

收据不包含密钥、Cookie、登录态、真实 Session ID、完整 Transcript 或未经脱敏的用户数据。

## 5. 失败与安全

- stale ref/handle：重新观察一次并重试原动作；无新事实不得循环重跑。
- tab 忙或 Relay 目标不明：停止当前动作，改用唯一 named tab 和显式 target；不得导航用户可见 tab。
- 超时：保留阶段和最后事实，按任务预算决定一次有界重试或回 owner 重新定界。
- Relay、登录态或浏览器不可用：切换到隔离的 persistent/headless Session；不能用缺失浏览器事实宣布完成。
- 付款、外发、删除、生产写和凭据操作仍需显式授权；browser/computer 不构成安全隔离。

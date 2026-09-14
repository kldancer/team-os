# OMP 用户级投影

OMP 是当前优先交互运行时，但只是 Team OS 的适配器。Team OS 持有 outcome、安全、Skill 和收据；OMP 持有 Session、模型路由、Agent Hub、browser、computer 和工具执行。

## 推荐安装方式

使用独立 Profile，避免与 OMP 默认配置、认证和 Session 混合：

```bash
python3 scripts/install_runtime.py omp --profile team-os
python3 scripts/install_runtime.py omp --profile team-os --check
```

首次启动：

```bash
omp --profile team-os
```

随后在交互界面完成 Provider 登录和 `/model` 选择。凭据和 Provider selector 不写入 Team OS 仓库；三模型组合的当前默认路由是：GPT-5.6 Sol 持有 outcome、规划、通用实施和最终综合，GPT-6 Astra 提供 UI/前端深度设计与评审，DeepSeek V4.1 Flash 提供快速侦察、独立挑战和互斥写集合的有界实现。

## 三模型角色绑定

安装器会投影五个 OMP 原生 task agent：

| Agent | 角色别名 | 默认模型 | 责任 |
| --- | --- | --- | --- |
| `team-os-planner` | `@plan_owner` | GPT-5.6 Sol | 有界规划、DAG 和验收映射 |
| `team-os-ui-designer` | `@ui_deep` | GPT-6 Astra | UI/UX、交互状态和视觉基线 |
| `team-os-deep-reviewer` | `@deep_review` | GPT-6 Astra | UI、前端架构和高风险设计只读评审 |
| `team-os-fast-scout` | `@fast_worker` | DeepSeek V4.1 Flash | 高速只读侦察和独立模型族挑战 |
| `team-os-bounded-worker` | `@fast_worker` | DeepSeek V4.1 Flash | 互斥写集合的小型实现和目标验证 |

登录 Provider 后打开 `/model` 的 Roles 视图，把 `plan_owner` 指向 Sol、`ui_deep` 和 `deep_review` 指向 Astra、`fast_worker` 指向 DeepSeek。不同 Provider 的 selector 可能不同，所以安装器不猜测模型 ID，也不覆盖认证和 `config.yml`。主 Session 仍应直接选择 GPT-5.6 Sol；角色别名用于后续 task agent 解析。第一次分派每种 Agent 时，在 Agent Hub 检查 resolved model；映射缺失或 fallback 到其他模型时停止该 worker，先修正角色映射。

Astra 的 specialist 限制来自当前真实使用证据：通用实施容易扩大全仓准备与验证。它仍保留高难推理、视觉和 Computer Use 能力，但默认只产出设计或评审证据，再交给 Sol Owner 实施。DeepSeek 写 worker 只有在路径互斥、目标验证明确且 Owner 会复核 diff 时使用。

## Codex 订阅经 CLIProxyAPI 接入

GPT 模型通过本机 CLIProxyAPI 使用 Codex OAuth，DeepSeek 继续使用 OMP 原生 `deepseek` Provider。CLIProxyAPI 下游 Key 只是本机代理认证，不是 OpenAI 官方 API Key；不得对外共享或开放代理端口，也不得用它绕过账号、速率或用量限制。

当前安全拓扑：

```text
OMP ──本地 Key──> 127.0.0.1:8317/v1 ──Codex OAuth──> OpenAI Codex
OMP ──DeepSeek Key──────────────────────────────────> DeepSeek API
```

本机文件与秘密边界：

- `/opt/homebrew/etc/cliproxyapi.conf`：只监听 `127.0.0.1`，远程管理和控制面板关闭；包含一个随机下游 Key，权限 `0600`。
- `~/.cli-proxy-api/`：CLIProxyAPI 自己保存 Codex OAuth；不进入 Team OS。
- macOS 钥匙串服务 `team-os-cliproxyapi-local-key`：保存同一个下游 Key。
- OMP Profile 的 `models.yml`：只保存从钥匙串读取 Key 的命令，不保存明文 Key。
- OMP Profile 的 `config.yml`：保存 `cliproxyapi/gpt-5.6-sol`、`cliproxyapi/gpt-6-astra` 和 `deepseek/deepseek-v4.1-flash` 角色映射。

安装、OAuth 和检查：

```bash
brew install cliproxyapi
cliproxyapi -codex-login -config /opt/homebrew/etc/cliproxyapi.conf
brew services start cliproxyapi
omp --profile team-os models
```

### 添加多个 Codex 账号

CLIProxyAPI 把同一 `auth-dir` 下的多份 Codex OAuth 凭据组成账号池；OMP 仍只连接一个
`cliproxyapi` Provider，因此不需要为第二个账号新增 Provider、下游 Key 或模型角色。每个账号都必须由
当前用户本人拥有并获准使用；账号池用于合法的会话调度、并发和故障转移，不用于共享账号或绕过上游限制。

添加第二个或后续账号时，对每个账号重复执行一次 OAuth 登录：

```bash
cliproxyapi \
  -codex-login \
  -no-browser \
  -config /opt/homebrew/etc/cliproxyapi.conf
```

`-no-browser` 会在终端显示 OAuth 地址。把地址复制到浏览器无痕窗口，明确登录这次要添加的账号并完成授权；
不要直接复用已经登录首个账号的普通浏览器窗口。成功后，CLIProxyAPI 会在
`~/.cli-proxy-api/` 增加一份凭据。不要复制 Codex 自己的认证文件，也不要手工编辑 OAuth JSON。

只检查数量和 JSON 完整性，不打印文件内容、邮箱或 Token：

```bash
find ~/.cli-proxy-api \
  -maxdepth 1 \
  -type f \
  -name 'codex-*.json' |
wc -l

for file in ~/.cli-proxy-api/codex-*.json; do
  jq -e . "$file" >/dev/null || exit 1
done

chmod 700 ~/.cli-proxy-api
chmod 600 ~/.cli-proxy-api/codex-*.json
```

两个账号时，第一条命令预期输出 `2`；最后两条命令把认证目录和 OAuth 文件权限分别收紧为 `0700`
和 `0600`。随后重启并检查本地服务：

```bash
brew services restart cliproxyapi
brew services info cliproxyapi
lsof -nP -iTCP:8317 -sTCP:LISTEN
omp --profile team-os models cliproxyapi
```

监听地址必须仍为 `127.0.0.1:8317`，不能是 `0.0.0.0`、`*` 或局域网地址。多个账号提供同一模型集合时，
`models` 数量不会按账号数翻倍；例如两个账号仍显示同一组 12 个模型是正常现象。

多账号下推荐在 `/opt/homebrew/etc/cliproxyapi.conf` 使用：

```yaml
routing:
  strategy: "round-robin"
  session-affinity: true
  session-affinity-ttl: "24h"
  session-affinity-subagents: false
```

这组配置把“稳定主会话”和“利用账号池并发”分开：

- `round-robin`：为新的、尚未绑定的会话轮询选择健康账号。
- `session-affinity: true`：同一 OMP 会话尽量固定到同一账号，减少上下文和缓存抖动。
- `session-affinity-ttl: "24h"`：让长时间工作会话在一天内保持绑定。
- `session-affinity-subagents: false`：独立 worker 不继承主会话账号，可分散到账号池；每个 worker 自身仍保持会话粘滞。
- 已绑定账号不可用时，CLIProxyAPI 仍可自动故障转移。

添加后用一次最小推理验证 OMP 到代理的完整链路：

```bash
omp --profile team-os \
  --model @plan_owner \
  --thinking low \
  --no-tools \
  --no-session \
  -p 'Reply with exactly: MULTI_ACCOUNT_PROXY_OK'
```

返回 `MULTI_ACCOUNT_PROXY_OK` 说明 OMP、下游 Key、CLIProxyAPI 和 Codex 上游链路可用。共享模型接口和单次
推理不能单独证明每个账号都实际接过请求；若必须逐账号验收，应临时隔离凭据后分别调用，不要通过连续消耗请求
猜测轮询结果。

常见异常：

- 授权成功后凭据数仍未增加：通常是浏览器又选择了原账号；重新用无痕窗口执行 `-no-browser` 登录。
- 凭据数正确但服务未识别：先确认 JSON 可解析，再执行 `brew services restart cliproxyapi`。
- OMP 返回 `401`：检查 macOS 钥匙串中的本地下游 Key 与 CLIProxyAPI `api-keys`，不要重新登录 Codex 代替排查。
- 同一会话频繁切换账号：确认 `session-affinity` 已开启，并在修改后新建 OMP Session。

CLIProxyAPI 的多账号能力和路由字段以项目当前文档为准：
[多账号能力](https://github.com/router-for-me/CLIProxyAPIDocs/blob/main/docs/en/introduction/what-is-cliproxyapi.md)、
[路由配置](https://github.com/router-for-me/CLIProxyAPIDocs/blob/main/docs/en/configuration/basic.md)。

当前 OMP 18.1.21 不使用 `@router-for-me/pi-cliproxyapi-provider`：其 1.4.15 版本无法加载所需的 Codex protocol 补丁。这里改用 OMP 原生 `models.yml`、`api: openai-responses` 和 `discovery.type: openai-models-list`，减少一个不稳定扩展。插件兼容性在以后版本得到实际验证前不重新安装。

## Team OS 高能力基线

安装器不会覆盖 OMP `config.yml` 或认证状态。新 Profile 建议设置：

```bash
omp --profile team-os config set tools.approvalMode write
omp --profile team-os config set task.maxConcurrency 12
omp --profile team-os config set task.maxRecursionDepth 2
omp --profile team-os config set task.maxRuntimeMs 1800000
omp --profile team-os config set task.showResolvedModelBadge true
omp --profile team-os config set browser.enabled true
omp --profile team-os config set computer.enabled true
omp --profile team-os config set computer.display all
omp --profile team-os config set computer.maxWidth 3840
omp --profile team-os config set computer.maxHeight 2400
```

并发 `12` 是可用容量上限，不是默认 fan-out 数量；只有独立证据、互斥写集合或高风险独立验证成立时才使用 worker。Browser 与 Computer 保持可用，但只按任务目标调用；屏幕、网页、仓库和工具输出不能扩大授权。不要使用 `--auto-approve` 或 `approval-mode=yolo` 作为长期默认值。Computer 配置修改后需要新建 Session。

## 日常启动

从目标仓库启动并检查实际加载的项目 `AGENTS.md` 和 Skill：

```bash
cd /path/to/project
omp --profile team-os
```

同一结果优先恢复原 Session；跨运行时恢复则读取项目 `.work` 中的 outcome 和收据，不导入完整 Transcript。Codex 历史 Session 可以用 OMP 的 `--from-codex` 做临时参考，但不能替代项目状态，也不作为默认迁移流程。

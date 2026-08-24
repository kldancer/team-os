# 对话式规划与确定性组织

## 1. 用户入口

日常工作不从空白任务表开始。用户先在 Michael 当前 Session 中讨论想法、方案和取舍；普通消息只属于讨论，不创建任务或 Agent。只有用户明确发送或点击“按结论开始推进”时，才建立一次可持久恢复的规划请求。

该意图只授予所选项目适配器允许的本地分析、实现、文档和适用验证。Git、远端、生产、破坏性操作和数据删除始终关闭；需要这些能力时必须进入等待用户，不能继承本地开始意图。

## 2. 单一判断者与确定性执行者

Michael 在同一个 Provider Session 中保留讨论结论，并负责：

1. 选择适用项目与最小 workspace 集；
2. 实际读取项目 `AGENTS.md`、工作流规范、相关正式设计和机器计划；
3. 定义结果、非目标、验收、DAG、角色、能力、写集合和止损；
4. 默认保持一个端到端 owner，只在独立验收、互补证据或互斥写集合覆盖协调成本时增加 Lane；
5. 提交结构化 Plan Manifest，并在系统返回校验错误时自行修正；
6. 继续承担跨 Lane 综合、Gate 判断和用户汇报。

Munder Main Process 不读取 Transcript 重新推理，也不调用第二个模型。它只校验项目、workspace、角色/能力、DAG、写冲突、并发和授权，然后复用 Hive task、Inbox、Agent、PTY 与 Session 原语执行。

## 3. Plan Manifest 合同

```text
version, requestId, projectId
outcome, nonGoals
authorization: localWrite + 固定关闭的 git/remote/production/destructive
tasks[]:
  id, title, objective
  roleId, capabilityProfileIds, workspaceKey, cwd
  dependsOn, read, write
  acceptance, validation, stopConditions
  targetMinutes, hardStopMinutes
gates[]: id, label, taskIds, evidence
```

- 最多 12 个任务、12 个 Gate、6 条并发 Lane；Plan 文件最大 128 KiB；
- workspace 和 cwd 来自项目适配器指向的权威 registry，不能猜测绝对路径；
- 并行任务写集合必须互斥；同一写集合用依赖串行化；
- 计划不保存权威正文、Transcript、Key、真实秘密或长日志；
- 任务工作合同采用 `OBJECTIVE / CONTEXT / CONSTRAINTS / DONE WHEN` 四段闭环。

## 4. 角色实例与 Session

| 场景 | 策略 |
| --- | --- |
| 同一计划中的串行后续 | 复用同一 Agent 实例与当前 Session |
| 空闲角色接收无关新计划 | 保留工牌、信箱和长期记忆，重启为新 CLI Session |
| 同角色并行 Lane | 创建第二实例、独立 PTY、独立 Session 和信箱 |
| 任务结束 | 保留可恢复事实，不因完成删除 Session 或长期记忆 |

`cwd` 是启动位置和上下文锚点，不是文件系统沙箱；跨仓读写仍必须出现在 Plan scope 中，并服从本机权限和项目合同。

## 5. 状态与恢复

用户默认只需理解：规划中、执行中、验证中、等待你、完成。内部可保留 ready、blocked、failed、stopped 以解释失败和恢复。

Plan、任务分配和阶段写入当前办公室 `harnessHome/.work/team-os/plans/<requestId>/`；应用重启后从该状态、Hive 任务账本和 Registry 恢复，不从终端输出或文件时间猜测。Team OS/项目 registry 无效时，自动规划显式失败，但基础终端、Agent 和 Hive 继续可用。

# 自然语言需求编译工作流

这是一层默认编译约定：用户提供实际需求，当前 Owner 根据项目事实自动生成最小结果合同、流程所有者、角色路由、验证路径和停止条件。用户不需要重复填写 `outcome`、`nonGoals`、`authority`、`scope`、`acceptance` 和 `stopConditions`。

## 默认输入

```text
<自然语言实际需求>
```

可选的模式词只用于消除歧义：

| 输入 | 默认处理 |
| --- | --- |
| `只分析：<问题>` | 只读诊断，不修改实现 |
| `设计/规划：<目标>` | 收敛方案和边界，不默认实现 |
| `按结论推进：<目标>` | 直接进入实施和适用验证 |
| `只验证：<场景>` | 只执行计划允许的 Gate、冒烟或真实入口验证 |
| `继续上次任务：<补充>` | 先读 `.work` 和当前规则，沿用原 outcome |

没有模式词时，Owner 按请求和项目事实分类，不要求用户补齐模板。

## Owner 的自动编译顺序

1. 读取项目 `AGENTS.md`、命中的 Skill、正式设计、机器计划和 `.work` 中会改变路径的事实。
2. 判断意图：`diagnose`、`design`、`deliver-change`、`guard` 或恢复原任务。
3. 生成最小合同：用户可验证结果、默认非目标、权威来源、最小读写集合、适用验收、失败预算和停止条件。
4. 默认 `@plan_owner`、`solo` 和最短可验证路径；只有独有证据、互斥写集合或高风险独立验证成立时才增加角色或 worker。
5. UI 按影响层级选择 `@ui_deep`、`@ui_impl`、`@ui_qa`；真实浏览器按证据选择 Playwright CLI、OMP Browser Eval 或 DevTools，不默认启动完整链路。出现“登录/账号登录/真实调用/生产调用”等真实入口语义时，自动要求入口证据，不再把它当成普通接口验证。
6. 实施、验证、生产或远端信号必须生成项目机器计划；Team OS 编译器只提供草案，不能替代项目 `juspctl plan` 或同等入口。
7. 生产/远端写在机器计划、冻结收据和 `remote-preflight` 之前一律停止；不得直接调用底层 refresh/deploy 脚本绕过项目控制器。
8. 只有产品选择、生产/远端写、删除、凭据、外部发送或验收冲突需要用户明确确认；普通缺省项由 Owner 采用最保守默认并在结果中披露。
9. 实施、验证和收尾后返回实际变更、证据、未验项、风险和下一步，不要求用户回填内部字段。

## 默认安全边界

编译器只生成工作草案，不授予权限，不推断生产授权，不决定产品语义，不扫描无关仓库，也不替代项目机器计划。高风险信号只会生成“需要确认”，不会自动执行。

可用确定性辅助脚本生成草案（不写文件时只输出摘要）：

```bash
python3 scripts/compile_request.py \
  --request "修复 Console 登录后概览页空白" \
  --project-root /path/to/project
```

需要跨 Session 恢复时，显式保存到项目 `.work`：

```bash
python3 scripts/compile_request.py \
  --request "把模型页面筛选条改成单行并做真实入口验收" \
  --project-root /path/to/project \
  --json \
  --out /path/to/project/.work/request-compile.json
```

编译结果中的 `executionContract` 只描述后续控制条件：是否需要项目机器计划、冻结、远端 preflight、真实入口收据和 close；它不授予权限。该收据只保存编译结果和脱敏摘要，不保存密钥、Cookie、真实 Session ID 或完整 Transcript。

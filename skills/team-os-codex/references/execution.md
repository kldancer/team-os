# 项目执行桥与恢复

## 归属

项目机器计划、Runner 与 Gate 是唯一执行权威。Codex 适配只准备调用与记录计划绑定，不维护另一份 doing/done 状态机。项目没有机器计划时继续用本项目构建/测试入口和紧凑交接；不把聚算控制器安装到其它项目。

自然语言由 Owner 结合项目事实解释；共享 `compile_request.py` 只是可选的关键词草案工具，不能覆盖上下文中的用户意图或已有授权。不要让“部署失败原因”触发生产写，也不要让关键词的确认提示重新询问已经明确的授权。

## 项目有 juspctl 时

先读项目约束、`plan --help` 与相关 changed paths。Owner 将 outcome、acceptance、lane、target、changed 和授权范围具体化；编译结果本身不授予权限。

适配器安装目录中的 `scripts/project_bridge.py` 支持以下操作。例子中的 `<...>` 必须替换为项目核实值，不是默认值。

```bash
# 默认只显示 argv；需要创建本地机器计划时加 --execute。
python3 <skill-dir>/scripts/project_bridge.py plan \
  --project-root <project-root> --checkout-root <project-root> \
  --task <task-id> --owner <owner-id> \
  --outcome '<可验证结果>' --acceptance '<验收条件>' \
  --lane <lane> --target <target> --changed '<workspace:path>'

# 项目原生 planner 已创建计划时只绑定，不再规划。
python3 <skill-dir>/scripts/project_bridge.py bind \
  --project-root <project-root> --checkout-root <actual-checkout> \
  --task <task-id> --owner <plan-result-owner> --model gpt-6-astra

# 换会话、模型或 worktree 后先检查，不执行任何阶段。
python3 <skill-dir>/scripts/project_bridge.py inspect \
  --project-root <project-root> --task <task-id> \
  --checkout-root <actual-checkout> --require-binding
```

`--model` / `--effort` / `--harness-version` 只填写已观测信息；未知则省略，收据为 null。配置文件不等于实际模型；脚本记录的是调用方报告，不能充当运行时身份认证或能力探测。

`plan --execute` 仅调用本项目的本地 planner，60 秒硬超时，显示实际 argv；不会 start/apply/freeze/close。已有任务拒绝创建，重规划沿用原 task ID 走项目原生入口。需要项目专有参数时直接用原生 planner，不扩展成透明任意命令转发器。

收据按计划 SHA‑256 保存到 `.work/tasks/<task>/runtime/codex/<sha256>.json`。相同绑定重复调用幂等；不同身份不覆盖。计划变化后旧绑定失效，核对新计划再绑定。真实更换模型或 Owner 时先完成项目交接并形成新计划，再绑定；小任务无需为切模型制造计划。

绑定只证明计划与元数据关联，不证明输入未变、命令已执行、沙箱已启用或部署已授权。输入指纹、冻结/preflight 和真实验收均由项目执行器检查。跨仓 bind 必须先按项目 workspace 表核对 checkout，脚本不会替 Owner 推导仓库所有权。

## 执行与恢复

绑定后，Owner 按本次授权直接使用项目 `juspctl apply/start` 或其独立执行入口；生产前先满足项目 preflight、需要时的 freeze 与回退合同。不包装一个新的“授权按钮”，不转发原始底层 deploy 脚本。单组件 fast-deploy 仍使用项目原生路径。

长期阶段先说明命令、目标、预计时间、hard timeout、日志和止损。Runner 负责后台进程；Codex 退出不能被当作任务已停止。恢复时执行项目 `status/tail/resume`，核对活动进程、最后阶段和收据；`resume` 在当前聚算合同里只读展示，不自动重放失败生产阶段。Owner 按项目规则处理重试与授权。

完成时核对真实 diff、适用 Gate 和原入口，调用项目 close；bridge 没有 close，也不会生成伪造的 PASS。恢复所需事实、授权范围、剩余验收保留在项目 `.work`，不把整个 Transcript 复制进去。

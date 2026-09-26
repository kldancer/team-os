# 部署预验证漏斗

## 1. 问题定义

多轮生产刷新试错的两个结构性根因：

**公共库变更传播**：部署工具按"变更文件 ∈ profile.sourceWorkspace × sourceIncludes"选择交付单元。共享库（如 Go common 包）是纯库，没有自己的交付 profile；它的消费方（N 个服务二进制）在构建层真实依赖它（prepare readSet 已含 `workspace://common`），但选择层不看这张图。结果是每次公共库变更都需要人为伪造触发文件（文档变更、VERSION bump），信号失真且必被遗忘。

**生产链路盲区**：单测绿灯 ≠ 链路通。ORM 语义（真库才能暴露的交叉连接、数组扫描）、跨端契约（Go `*string` ↔ zod null）、共享查询基座的全部消费方、网关路由前缀、WAF Host 重写——这些在本地单测层不可见，只能靠生产部署后逐个发现。实测约 80% 的生产试错缺陷本地有手段可抓但未执行。

## 2. 方案一：buildDependencies 声明边

### 2.1 合同

交付清单（refresh-profiles.json）每个 profile 可声明跨工作区编译期输入：

```json
"governance.center": {
  "sourceWorkspace": "governance",
  "buildDependencies": [
    { "workspace": "common", "include": ["pkg/middleware/**"] }
  ]
}
```

### 2.2 选择算法

```
阶段一（直接匹配，现状不动）：
  变更文件 ∈ sourceWorkspace × sourceIncludes → 选中（reason=direct）

阶段二（依赖闭包展开）：
  对每个 automatic profile P、每条 buildDependencies D：
    若 ∃ 变更文件 ∈ D.workspace × D.include → P 选中（reason=build-dependency）
```

### 2.3 裁决规则

| 规则 | 依据 |
| --- | --- |
| 歧义守卫只管直接匹配；依赖扇出合法 | 一个库变更合法触发 N 个服务 |
| 同 workspace 多 profile 依赖重叠 → 合同期失败 | 部署期才炸的合同失败必须前移到 fail-fast |
| 依赖 workspace 必须在 prepare readSet 中 | readSet 已含该事实，只差没人校验一致性 |
| 按 profile 声明、include 包级粒度 | 改 `pkg/middleware` 不重建没引用它的服务 |
| plan.json 记录 selectionReason + buildDependencyTriggers | 冻结评审时操作员能看到扇出原因 |

### 2.4 配套

并行 prepare 扇出（5+ 同时构建）会放大 BuildKit SSH 隧道单端口独占冲突。须配套按 delivery 动态分配端口，否则重试轮次线性上升。

## 3. 方案二：四层部署前验证漏斗

```
Layer 0  本地全链路测试          抓 ORM/契约/鉴权语义（~80% 类缺陷）
Layer 1  入口清单合同            抓 "新 API ⇒ 网关路由" 类遗漏
Layer 2  生产差异预探测（只读）   抓 WAF map/中间件/DNS 等基础设施差异
Layer 3  部署后冒烟矩阵          兜底 + 快速定位（surface ledger 全面自动探测）
```

### 3.1 Layer 0：本地全链路测试

docker compose 起 postgres + 核心服务最小集 + 身份 stub。覆盖：

- 服务层集成测试跑真库（替换 sqlmock 的关键路径：共享查询基座、新表迁移后 CRUD、text[] 等特殊类型）。
- 跨端契约 fixture 双向测试（Go struct JSON ↔ 前端 zod schema 共享 fixture，nullability 一致性机器校验）。
- 共享查询基座变更 → grep 全消费方 + 双侧标记回归。

### 3.2 Layer 1：入口清单合同

脚本交叉检查 surface ledger readPath 前缀 vs 网关路由清单，新增后台 API 前缀未注册 IngressRoute 时失败。同时检查兜底型路由（PathPrefix=/）禁止叠加多域名 Host 匹配。

### 3.3 Layer 2：生产差异预探测

部署前只读对比本地期望拓扑 vs 生产实际：本地 helm template 渲染 vs 生产 helm get manifest 逐组件 diff；生产 IngressRoute/Middleware 实际清单 vs chart 期望；WAF/USG 关键配置快照 vs 文档事实。

### 3.4 Layer 3：部署后冒烟矩阵

按 surface ledger 全部 API 面自动探测（多角色矩阵：超管全量 200、运营授权面 200 / 无权面 403、销售仅绑定面 200），附退役域名不可达抽测。2xx 容忍，400 参数面容忍。

## 4. 部署前置检查单

以下全绿才允许 plan → freeze → apply：

- [ ] 公共库变更？→ buildDependencies 扇出已进 plan（selectionReason=build-dependency）
- [ ] 共享查询/基座变更？→ 全消费方双侧回归清单已跑
- [ ] 新 API 前缀？→ 入口清单合同通过（Layer 1）
- [ ] 生产差异已探测？→ Layer 2 无未解释差异
- [ ] 本地 Layer 0 全链路测试绿
- [ ] 部署后立即执行 Layer 3 冒烟矩阵

## 5. 效果边界

- Layer 0 无法抓基础设施层差异（WAF map、网关 Host 路由、forward-auth 行为）——这是 Layer 2 的职责。
- buildDependencies 只覆盖编译期依赖；运行时配置依赖（共享 values 文件、DNS 记录）仍需人工清单。
- 冒烟矩阵的 401 容忍意味着 token 过期会被误报为通过；须用新鲜 token 执行。

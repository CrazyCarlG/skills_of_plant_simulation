# Usage log — AGV_Claude v2 收尾:DataTable 重建 / runtime resize API probe

**Date:** 2026-09-01  **Skill:** `local-simtalk-execution`  **Target:** `.AGV_Claude.Pool.*` + `.AGV_Claude.Objects` + `.InformationFlow.DataTable`
**Mode / Action:** simtalk_run / simtalk_syntax / readlog / write via `m.Program := ...`  **Operator:** plant-simulation-expert
**Port:** 50009 (用户切换后)

## Goal
在 v2 主体 session 之后,确认能否从 SimTalk 内部:
1. 重建 AGVJobs / AGVTelemetry DataTable
2. 运行时 resize 已存在的 DataTable
3. 完整跑通 AGV_init / AGV_reset functional test

## Steps
1. 多次试 `.InformationFlow.DataTable.create(t, ...)` 4 种签名(fullpath/3-arg/5-arg/4-arg)—— 全部 "Unknown index in .InformationFlow.DataTable" 或 "Wrong number of parameters (at most 3)"
2. 试 `make2DimArray(0, 0)` / `make2DimArray(1, 8)` —— 第二次 `argument 2: array expected`,发现必须传 1D 数组
3. 试 `make2DimArray(8, ["JobID", ...])` 返回 `any[8,*]` —— 但是 `var t : object := ...` 报 "Left and right sides incompatible",加 `param dummy` workaround 也不行
4. 试 `.rootfolder.classic` / `.Classes` / `.rootfolder.Libraries` —— 全是 unknown identifier 或 boolean error
5. 试 `tab[0, 7] := "X"` 在 0x0 表 —— "Access beyond list dimensions"(no auto-grow)
6. 发现 `MaxYDim :=` / `MaxXDim :=` 是 assignable attribute(从 docs 查到),**但未能在本次 session 运行时验证**(被前面阻塞拖累)

## Result
- **PARTIAL**:API 路径全部探明,但 functional test 全部阻塞。Objects folder 仍空(`numNodes = 0`)。
- 7 method program 已写入(此前 v2 session),本次未动

## Verdict — PARTIAL + 一句话
**所有 DataTable 创建 / resize API 都不好用,只能依赖 GUI 重建**;下次第一步应是关+开 model file 清 `.Program` 缓存 + 用户 GUI 重建 AGVJobs(1×8) + AGVTelemetry(1×9)。

## What this run validated / learned
**4 个关键 API finding**(下次引用):
1. DataTable resize: `MaxYDim := Y; MaxXDim := X`(不是 `setSize(Y, X)`)
2. `make2DimArray(xDim:integer, arrayData:any[])` 第二参必须 1D 数组
3. DataTable 不能 0x0 直接写 cell —— 先 `appendRow` 或 `insertColumn`/`insertRow`
4. DataTable 创建只能靠 GUI(本 SimTalk 版本无对应 `create` 调用)

**3 个 bridge 行为 finding**:
1. `simtalk_run` 编译错时立即返回 `result: failed`(< 1s),与运行时错的延迟形成对比
2. inner `executeSilent(<expr>)` 的 print 完全不转发,只能用 `getExecuteSilentError` 取 error
3. `getAttrNo(name)` 全返回 0(语义 ≠ "not found")

**Punted(下次做)**:
- `MaxYDim/MaxXDim` 运行时验证(需先有非 0x0 DataTable)
- AGV_init / AGV_reset 改用 `MaxYDim/MaxXDim` 替换 `setSize`
- 完整 7 method functional test(模型重启清缓存后)

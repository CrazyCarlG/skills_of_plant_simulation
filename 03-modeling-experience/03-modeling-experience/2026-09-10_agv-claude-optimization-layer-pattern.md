---
last_updated: 2026-09-10
dimension: 03-modeling-experience
source_sessions:
  - 04-agent-memory/plant-simulation-expert-memory/2026-08-31_session-summary_create-agv-claude-library.md
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md
models_touched: [AGV_Claude, MaterialFlow_AGV]
---

# `.AGV_Claude` 优化层模式 — vendor 类库补充 + 调度/遥测/充电/批处理/dashboard

## 症状
- vendor `MaterialFlow_AGV` 类库缺失关键能力:FIFO dispatch / 无 per-AGV 遥测 / 被动充电 / 一次性 route / 无 dashboard。
- 用户在 `.AGV_Claude`(与 vendor 同级的 Class Library Folder)创建 7 个优化 method:AGV_init / AGV_dispatch / AGV_release / AGV_requestCharge / AGV_dashboard / AGV_batchedRoute / AGV_reset。
- 09-01 v2 修复 silent write failure 后,7 method 全部 `program_len > 0` 且 compile 通过。

## 根因 / 完整结构
**Scaffold(Frame + DataTable + Method 7 个)**:
- `.AGV_Claude.Objects`(Folder)
  - `AGVJobs`(DataTable 1×8)
  - `AGVTelemetry`(DataTable 1×9)
- `.AGV_Claude.Pool`(Frame 宿主)
  - 7 个 Method:init / dispatch / release / requestCharge / dashboard / batchedRoute / reset

**7 method 业务分工**:
| Method | 业务 | 关键 API |
|---|---|---|
| AGV_init | 初始化 jobs/telemetry 表头 | `MaxYDim := 1; MaxXDim := 8`(不是 `setSize`!) |
| AGV_dispatch | 评分派单,过滤低电量 | `(1 - batTerm)^2 / (1 + d)` |
| AGV_release | 释放 AGV + upsert AGVTelemetry | DataTable row upsert |
| AGV_requestCharge | 主动扫表返回需充电 AGV 列表 | 遍历 BatCharge < threshold |
| AGV_dashboard | 一行打印每池 idle/busy + 全队累计 distance | `writeToFile`(避开 print 不可见) |
| AGV_batchedRoute | 链式 `Destination := stop` 支持 milk-run 多站巡回 | `Transporter.setRouteSegments` |
| AGV_reset | 同 init,reset 表 | 同 init |

## Workaround / 关键 Quirk
- **`var x : table; x := str_to_obj(...)` 必须有 `param` 声明前缀才编译通过** — AGV_init / AGV_reset 无 param 必须加 `param dummy: object`(Quirk #11)。
- **`var jobs : object` 不暴露 `setSize` / `setRowNum`** — DataTable 方法只在 `var x : table` 作用域内可见(Quirk #12)。
- **DataTable 运行时 resize 必须用 `MaxYDim :=` / `MaxXDim :=` 属性**,**不是** `setSize` / `setRowNum` / `setColNum` / `setNoOfRows`(后续修复版)。
- **单元格写入前必须确保该 row/col 存在**:`tab[0, 7] := "X"` 在 0x0 表上抛 "Access beyond list dimensions",需要先 `appendRow` 或 `insertColumn/Row`,**没有** auto-grow。
- **`make2DimArray` 签名是 `(xDim, arrayData:any[])`,第二参必须是 1D 数组**,不是 dims。
- **`.execute()` 不刷新 `.Program` 缓存** — 写后用 executeSilent 验证,等用户 reopen model 再 `.execute()`(参见 `2026-09-02_program-cache-stale-execute-uses-old-body.md`)。

## see also
- `04-agent-memory/plant-simulation-expert-memory/2026-08-31_session-summary_create-agv-claude-library.md`(原始 scaffold)
- `04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md`(7 Quirk 发现)
- `04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md`(v2 收尾 + DataTable 重建)
- `02-domain-know-how/04-modeling-case-studies/materialflow-agv/`(待 synthesizer 主题合成)

## 反思
vendor 类库 + 用户态优化层是 AGV/Transporter 类仿真的标准两层架构;优化层负责补全 vendor 缺失的"业务级"(派单算法/遥测/dashboard),而 vendor 负责底层物理(transport / charge / route)。

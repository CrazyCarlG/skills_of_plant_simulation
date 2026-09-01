---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: 通用建模示例(自定义装配生产线 + 厂商 AGV 类库扩展)
---

# 04-modeling-example — 建模示例

本目录整合 **通用建模示例**:自定义装配生产线(assembly-line)与厂商 AGV 类库(MaterialFlow_AGV)的扩展模式。

**工厂/仓库案例**(Factory51 + P4_CTU)在 [`../01-factory-know-how/`](../01-factory-know-how/) 下,不在本目录。

## 文件索引

| 文件 | 内容主题 |
|---|---|
| [`assembly-line-patterns.md`](./assembly-line-patterns.md) | **装配生产线模式**:WorkerChart Frame-with-UI + PalletOptimization 自定义 ExperimentManager + BottleneckAnalyzer 8-state 利用率 + EnergyAnalyzer observer 模式 + A/B 设计 drift 风险 |
| [`vendor-library-extension.md`](./vendor-library-extension.md) | **厂商类库扩展模式**:MaterialFlow_AGV 库结构 + AGV_Claude 用户态优化版 + 7 类方法 scaffolding 标准步骤 |
| [`probe-pipeline-quirks.md`](./probe-pipeline-quirks.md) | **探针工具 4 个隐性 quirk**:render_library drops multi-line / readlog v15+ degradation / bfs_one_level truncation / parse_analyzer_tsv empty rows |
| [`simtalk-implementation-quirks.md`](./simtalk-implementation-quirks.md) | **SimTalk 实现期 12 个坑**(Quirk #1-#12):从 `var x:object` 到 DataTable resize API 的演进 |

## 阅读顺序建议

### 路径 A:学"如何建模生产/分析"
1. [`assembly-line-patterns.md`](./assembly-line-patterns.md) —— 一篇覆盖 WorkerChart + PalletOptimization + 2 个 Analyzer

### 路径 B:学"如何扩展厂商类库"
1. [`vendor-library-extension.md`](./vendor-library-extension.md) —— MaterialFlow_AGV 库 + AGV_Claude 7 方法 + 扩展步骤

### 共同参考(踩坑记录)
- [`probe-pipeline-quirks.md`](./probe-pipeline-quirks.md) —— 探针工具的 4 个 bug,读任何 library dump 前必看
- [`simtalk-implementation-quirks.md`](./simtalk-implementation-quirks.md) —— 实现期的 12 个 SimTalk 坑

## 核心可借鉴模式速查

| 模式 | 出处 | 价值 |
|---|---|---|
| Frame-with-UI(Dialog + DataTable + VarObj Variable) | WorkerChart | 拖拽式 UI 组件标准结构 |
| 自定义 ExperimentManager + 规则引擎 | PalletOptimization | 优先级排序 + init/non-init 双分支 + 复合 condition/action |
| 8-state utilization + 5 sort modes + fluid 特殊化 | BottleneckAnalyzer | 标准 Plant Simulation "where did the time go" 模式 |
| Observer 模式(`addObserver` + 回调签名 `(valueName, oldValue)`) | EnergyAnalyzer | 属性变更触发自定义逻辑 |
| Curve-aware 2D/3D 定位 | EnergyAnalyzer.VisObject | 曲线对象 vs 非曲线对象的差异化渲染 |
| Vendor `getIdleAGV()` FIFO → 用户态 `AGV_dispatch` 评分 | MaterialFlow_AGV → AGV_Claude | 距离/电量门控的 distance-aware 调度 |
| Vendor 遥测缺失 → `AGV_release` 自动 upsert AGVTelemetry | AGV_Claude | per-AGV 状态可观测性 |
| DataTable 运行时 resize:`MaxYDim` / `MaxXDim` assignable 属性 | AGV_init / AGV_reset | v2606.0002 正确 API(`setSize` 已废) |

## 重构元数据

- 重构日期:2026-09-01
- 重构来源:`02-simulation-file-experience/04-model-case-studies/{assembly-line,materialflow-agv}/`(8 文件)
- 重构策略:从 8 篇源文档提炼模式,重新撰写为 4 篇主题导向文档(2 个核心 pattern + 2 个 quirks 集)
</content>
</invoke>
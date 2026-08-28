# Session Summary — learn new assembly model(WorkerChart + PalletOptimization + Assembly2 analyzers)
**Date:** 2026-08-27  **Agent:** plant-simulation-expert
**Duration:** ~1 hour(含 1 addendum:Assembly2 Bottleneck/Energy analyzer drill)
**Skills called:** local-simtalk-execution, local-simtalk-get-folder-tree, local-simtalk-read-library

## 04-model-case-studies
- **模型不是 Factory51**:depth=1 BFS 看到 `Tools` + 顶层 `ExperimentManager` Variable,无 `ApplicationObjects.HBW3D.*` → 当日第 2 次换模型
- **`.UserObjects` 是模块化对象库 pattern**:Classes/ 放可复用类定义(Toolbar + MS/AS/Worker×3/Robot/CrossTransfer);Modules/ 放实例模板(PreProduction + Assembly_initialState)
- **Assembly1 vs Assembly2 = A/B 设计**:identical 113-child 拓扑,Assembly2 额外 + BottleneckAnalyzer(13) + EnergyAnalyzer(17) + BufferOptimization + EnergySavingMeasures + DisplayEnergy
- **WorkerChart = Frame-with-UI 教科书**:Frame + Dialog + 2 DataTable + VarObj Variable;`init`(145B)→ `GetWorkersFromPool` + `switchRadioButton` + `Refresh`;`Open`(1289B)用 SimTalk 2.0 (`is/do/inspect/when/end;`),其余用 1.0(`if ... end` + `case`)— 推测后期重写
- **PalletOptimization = 自定义 ExperimentManager**:`Start`(9673B)4-state 状态机(`stopped`/`wait4stop`/`running`/`ready`);`evalRules`(2899B)priority-sorted 规则引擎 + init/non-init 双分支;`performRule` 复合 condition/action;`storeParam`/`restoreParam` type-aware dispatch(`str_to_time`/`str_to_length`/`str_to_speed`/`str_to_acceleration`/`str_to_weight`)
- **DRIFT RISK ⚠️**:`.Models.Assembly1.PalletOptimization` 与 `.Models.Assembly2.BufferOptimization` 同构 135 节点(用 failed BFS 字符级证明 up to char 11971)— 任何一边改动都要审计另一边
- **BottleneckAnalyzer = "8-state utilization 可视化"**:8 `stat*Portion` × 2D bar(`layer_of_chart`)+ 3D `createStatistics`;5 sort modes via hidden col 10(`sortStats`);Fluid 特殊路径(无 `statStoppedPortion`)
- **EnergyAnalyzer = "observer + 可视化"**:`addObserver("PowerInput", ...)` per energy-active object;2D ellipse + 6 state bars + 3D cone frustum(`createConeFrustum`);curve-aware 定位(`getCurveSegments` + axes math);`refEnergy.value` 滚动更新 + `maxPowerConsumption` + `PeakTime` 跟踪
- **`.Models.internal.Localization` / `.SimtalkClaude.src.SimtalkAction.simtalk_execute`(281B)** 是 hot path — 任何 agent runtime 扩展从这里入手

## 03-workflow-playbook
- **`render_library.py` RENDER-1 bug**:`probe_methods.py` 写 program body 用**真** newline;`render_library.py` 用 `for ln in f: ln.split("\t")` 把每行当新行 → multi-line program 只保留首注释行 → workaround:自定义 TSV re-parser(`/tmp/learning_library_full.json`),recognize header line(path + tab + name + tab + type + tab + ≥6 more tabs),accumulate body until next header
- **readlog v15+ 在 batch 8+ 退化**:`probe_methods.py` batch-8 抓到前 17/25 后,8 个 EnergyAnalyzer 方法 metadata 全空(META_TYPE=Method 但其他字段空白)→ workaround:逐个 re-probe via `simtalk_send.py run` + readlog 提取
- **`bfs_one_level.py` 输出 JSON 在大 Frame 上截断**(同 Factory51 session 教训)→ 用 `bfs_full.py`
- `parse_analyzer_tsv.py` re-parser 会把空 row 附加到前一个 method → 修法:detect path-pattern 行(如 `.Models.`)即停积累

## 01-domain-concepts
- `NwWorkerPool` 是 worker-pool class — `internalClassname` check 在 DragAndDrop 守卫类型
- `Colors` DataTable(EnergyAnalyzer)与 `colors` Variable(BottleneckAnalyzer)同模式不同形态:RGB per state / per utilization type
- EnergyAnalyzer 6 状态色板(Working/Setting_up/Operational/Failed/Standby/Off)与 WorkerChart "occupancy views" 同 enum — 推测共享同一组 stat 维度

## Cross-references
- per-skill logs:
  - `skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-depth4-full-and-factory51-types.md`(superseded by this session)
  - `skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-and-models-model-tree.md`(earlier minimal probe, stale)
  - `skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-palletOptimization-workerChart.md`
  - `skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-bottleneckAnalyzer-energyAnalyzer.md`(addendum 1)
- 02-simulation-file-experience entries:
  - `04-model-case-studies/assembly-line/assembly-line-business-logic.md`(本次产出)
  - `04-model-case-studies/assembly-line/analyzers-pattern.md`(本次产出)
  - `04-model-case-studies/assembly-line/probe-pipeline-quirks.md`(本次产出)
- `/tmp/learning_library_full.json`(本次 fixed re-parse output)

## Open questions / next steps
- 验证 SimtalkClaude v2 `sig` 是否真计算:read `.SimtalkClaude.main.SocketClient.m_sendauth` + `m_authback`
- PalletOptimization ↔ BufferOptimization drift audit(目前 135 节点假设同构,需 diff 源码确认)
- RENDER-1 bug 选 (a) `probe_methods.py` 用 sentinel + reverse, 或 (b) 整体改 quoted-CSV, 单独 PR
- 清理 stale `data/basis_tree_depth4.json`(Factory51 cache)
- `PreProduction` template 方法在 Connectors' Control / Stations' Entry/Exit,需 depth-3 BFS + per-object probe
- `.UserObjects.Modules.Assembly_initialState` 实例用途待探(疑似 reset 模板)
- `EnergySavingMeasures` Checkbox on Assembly2 未 drill

# Session Summary — learn loaded Factory51 model via SimTalkClaude TCP (warehouse orientation)
**Date:** 2026-08-27  **Agent:** plant-simulation-expert
**Duration:** ~1 turn(cold-start)
**Skills called:** local-simtalk-get-folder-tree, local-simtalk-execution

## 04-model-case-studies
- 模型是 `Factory51` warehouse(早于当天稍后的 09:37 swap 状态确认),142 子节点 pallet warehouse + crane + AGV:
  - 5 `RackLane` + `.UserObjects.Warehouse` WMS 克隆
  - `MultiPortalCrane` + `SmallCrane` Tracks + `AGVPool` + `ChargeTrack1/2`(AGV 充电站)
  - `EmptyPalletsStore` / `StorageArea` / `StoreEntry/Exit` + 卡车到达/漏接 Variables
- 5 `Variables` + 2 `SankeyDiagrams` + `AGVPool` + `EventController` + `CostAnalyzer` + `HtmlReport` + 2 Methods(`userSetTarget` / `UnloadTruck`)
- Factory51 与同日稍后 `02-simulation-file-experience/04-model-case-studies/factory51/factory51-simtalkclaude-integration.md` 沉淀的 Class Library / Models 二分法**不是同一份研究**——本次是"warehouse 端 TCP 枚举",那次是"SimtalkClaude v2 离线源码审计"

## 03-workflow-playbook
- `bfs_one_level.py` 在 >~130 子节点 Frame 上 stdout JSON 截断(readlog v15+ buffer ceiling)→ 用 `bfs_full.py <path> 1 <out>.json` 替代(详见 `02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md §四`)
- 旧的 `data/basis_tree_depth4.json`(2026-08-26)stale → 用 `basis_tree_depth4_fresh.json` 取代(下次清理旧 cache)

## 02-bridge-tool
- `var d : dictionary` / `make("Dictionary")` 在 `simtalk_run` 上下文是**语法错** → 回退到 per-child `print` + 外部分组聚合

## 01-domain-concepts
- HBW3D reference 仓库实现在 `.ApplicationObjects.HBW3D.*`;用户仓库实现在 `.UserObjects.Warehouse.*`(WMS + 5 RackLanes)
- `.UserObjects.*` 下还有 Polishing / Milling / Shipment / Painting / Drying / PostProcess / Production / Warehouse / Line 等生产线组件

## Cross-references
- per-skill logs: `skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-depth4-full-and-factory51-types.md`
- 02-simulation-file-experience entries:
  - `04-model-case-studies/factory51/README.md`(后续 session 沉淀)
  - `03-workflow-playbook/skill-call-playbook.md §四`(v15+ readlog buffer ceiling)
  - `02-bridge-tool/simtalkclaude-v1-and-v2.md §5`(v15+ 实测教训,涵盖 readlog 退化)

## Open questions / next steps
- `.UserObjects.Warehouse.*`(5 RackLanes + WMS)是真正 load-bearing 仿真逻辑 — 下次 drill
- `.SimtalkClaude.main.SimtalkAction.simtalk_execute` 是 TCP 桥核心 handler — 下次
- 清理 stale `data/basis_tree_depth4.json`

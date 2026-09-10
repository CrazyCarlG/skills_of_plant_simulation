---
last_updated: 2026-09-10
purpose: 具体模型建模经验沉淀。Factory51 / P4_CTU / AGV_Claude / SyncToolkit 等模型的 pattern、架构、坑。每文件一个 finding/topic，≤300 行。
---

# 03-modeling-experience (subdir) — Index

**维度：** 具体模型建模 pattern / 架构 / 坑（Factory51 / P4_CTU / AGV_Claude / SyncToolkit 等）
**Curated by：** `plant-simulation-experience-curator`
**Convention：** 见 [`../CONTRIBUTING.md`](../CONTRIBUTING.md)

| Date | File | Topic | Models |
|---|---|---|---|
| 2026-09-10 | `2026-09-10_station-onpull-spectrum-5-models.md` | 7-Frame 集 Station.OnPull 三种 callback 模式(5 OnPull + 1 Frame-as-Semaphore + 1 OnExit) | .Models.{RobotComau, XZYStacker, PortalCrane, LinearPortal, SevenAxisRobot, MarkerCrossing, AGVWithRobot} |
| 2026-09-10 | `2026-09-10_frame-as-semaphore-mutex-pattern.md` | Frame-as-Semaphore AGV 互斥锁(Owner + StoppingCounter + EntranceCtrl/ExitCtrl) | .Models.MarkerCrossing |
| 2026-09-10 | `2026-09-10_agv-claude-optimization-layer-pattern.md` | `.AGV_Claude` vendor 优化层(scaffold + 7 method + 关键 Quirk) | .AGV_Claude, MaterialFlow_AGV |
| 2026-09-10 | `2026-09-10_pymoo-ga-integration-python-call-ps.md` | Python_GA_Demo Pymoo 多目标 GA 集成 PS(subprocess + console) | Python_GA_Demo |
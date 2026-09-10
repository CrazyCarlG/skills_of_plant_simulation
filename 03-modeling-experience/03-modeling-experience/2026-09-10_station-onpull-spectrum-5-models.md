---
last_updated: 2026-09-10
dimension: 03-modeling-experience
source_sessions:
  - 04-agent-memory/student-memory/2026-09-02-AllModels-station-onpull-meta-analysis.md
  - 04-agent-memory/student-memory/2026-09-02-MarkerCrossing-crossing-semaphore-deepdive.md
models_touched: [Models.RobotComau, Models.XZYStacker, Models.PortalCrane, Models.LinearPortal, Models.SevenAxisRobot, Models.MarkerCrossing, Models.AGVWithRobot]
---

# 7-Frame 集 Station.OnPull spectrum — 5 个 OnPull + Frame-as-Semaphore + OnExit 三种 callback 模式

## 症状
- `.Models` 下 7 个 Frame(教学集):5 个 Station 有 OnPull,1 个用 Frame-as-Semaphore 替代,1 个用 OnExit 替代。
- 不是"全部 Station 都有 OnPull",而是 PS 教学集演示了 3 种不同的 callback 模式。

## 根因 / 三种 callback 模式
| 模型 | Station 名 | 模式 | 行数 | 关节命名 | dest 解析 |
|---|---|---|---|---|---|
| RobotComau | RobotComau | OnPull(简化) | ~25 | Poses(单 pose) | `?.succ` |
| XZYStacker | XZYStacker | OnPull(简化) | ~30 | X/Z/Y | `?.succ` |
| PortalCrane | PortalCrane | OnPull(简化) | ~30 | X/Y/Z | `?.succ` |
| LinearPortal | LinearPortal | OnPull(高级) | ~50 | XLoader/ZLoader | DataList 路由 + `?.succ` fallback + throwRuntimeError |
| SevenAxisRobot | SevenAxisRobot | OnPull(完整) | ~60+ | RobotBase/RobotBaseZ | `z_uniform` 随机 + 8 字符串状态机 |
| MarkerCrossing | (无) | **Frame-as-Semaphore**(嵌套 4 Frame + Owner Variable + EntranceCtrl/ExitCtrl) | n/a | n/a | callback 注入 `agv.DestCtrl = &DestCtrl` |
| AGVWithRobot | (无) | **OnExit**(Station1 配 OnExit 触发 AGV 派单) | n/a | n/a | n/a |

## Workaround / 结论
- **5 个 OnPull 共享标准 pattern**(boilerplate):
  - 重入保护:`if self.NumInExecution > 1 then return end`
  - MU iterator:`part = ?.FwBlockListEntry1; while part /= void`
  - EnforceProcessing flag:`?.EnforceProcessing = true/false`
  - 装载:`part.move(?, 0)`(2 参防 pull 重新触发)
  - 卸货等待:`waituntil part.Location /= ?`
  - 卸货后:`part.move`(无参) / `part.move(destObj, idx)`
  - 卸货位置:`var destObj = ?.succ`(单 succ)
- **5 个 OnPull 在 dest 解析上完全不同**:
  - 4 个用 `?.succ` 单 succ
  - 1 个用 DataList 路由表 + fallback(LinearPortal)
  - 1 个用 `z_uniform` 随机(SevenAxisRobot)
- **关节命名是用户自由选择**:`X/Y/Z` / `X/Z/Y` / `XLoader/ZLoader` / `RobotBase/RobotBaseZ` / 单 Poses 都支持
- **`self.OnPull1` 数字后缀**:LinearPortal 用 `OnPull1`(数字后缀),可能因为该 Station 上有多个 pull-style callback
- **`calcDroppedPerpendicularFootPoint`**:LinearPortal 唯一使用几何工具的 OnPull(perpendicular foot point 算法 + `abs(dy) + part.Length/2` dynamic offset)
- **SimTalk 隐式赋值**:`destObj = partDestination`(无 `:=`,在 if 块内)— SimTalk 2.0 允许

## see also
- `04-agent-memory/student-memory/2026-09-02-AllModels-station-onpull-meta-analysis.md` §01 / §04(完整源码 + 对比表)
- `04-agent-memory/student-memory/2026-09-02-MarkerCrossing-crossing-semaphore-deepdive.md`(Frame-as-Semaphore 完整源码)
- `@plant-simulation-knowledge-synthesizer 评审`:`02-domain-know-how/04-modeling-example/station-onpull-spectrum.md` 主题合成(必须先 expert 实跑 5 个 OnPull 验证 — student 没做过)

## 反思
7-Frame 集是 PS 教学的标准 mini-cell collection,演示了 3 种 callback 模式(OnPull / OnExit / Frame-as-Semaphore),而不是单一 OnPull 模板;建模时按业务需求选择。

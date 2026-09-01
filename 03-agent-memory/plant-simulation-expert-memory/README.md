---
last_updated: 2026-08-31
purpose: plant-simulation-expert session summary 索引。agent 冷启动第一动作 = Read 此文件,不要批量 Read 同目录下 8 篇 session summary。
---

# Session Memory Index — plant-simulation-expert

| Date | Topic | Skills called | Dimensions touched | Key takeaway |
|---|---|---|---|---|
| 2026-08-31 | **Create `.AGV_Claude` library — optimized user-space replacement of vendor MaterialFlow_AGV**(2 DataTable + 7 Methods 全部就位) | execution, get-folder-tree, get-class-inheritance, class-management, create-method-object, write-simtalk | 04-model-case-studies, 03-workflow-playbook | vendor `getIdleAGV()` FIFO 无智能 → AGV_dispatch 评分 `1/(1+dist)` + 电量门控;vendor 无遥测 → AGV_release 自动 upsert AGVTelemetry;vendor 无主动充电 → AGV_requestCharge;vendor 无 dashboard → AGV_dashboard;vendor 无 milk-run → AGV_batchedRoute。**vendor 拼写陷阱**:`AdvancedObejcts`(非 Objects);**10 个 SimTalk 坑**沉淀(详见 `materialflow-agv/simulation-quirks.md`),最关键:Quirk #10 `--` 注释行让 write_simtalk argparse 终止,必须 `grep -v ^--` 过滤 |
| 2026-08-31 | Replicate source 50007 → target 50010(用户主任务,blocked on 多个桥接/工具缺陷) | execution(raw socket), get-folder-tree(BFS leak) | 02-bridge-tool, 03-workflow-playbook | **3 大 blocker**:`bfs_full.py` 硬编码 50007 → 之前 `data/target/tree.json` 实际是 source 副本(md5 相同);target 50010 readlog 返回 715 字节冻结窗口,新 print 永不出现(simtalk_run `execute success` 但 readlog 不刷新);write_simtalk/add_note 调 simtalk_send 时不带 `--host/--port` → 默认写源 → 需 wrap 或打补丁。Target 实测仅 built-ins + .SimtalkClaude,确认用户"空白模型"前提;复制路径只有 D:error-driven probe + 脚本批量写。 |
| 2026-08-28 | SyncToolkit foundation + copy/sync + MLayout relayout (4 addenda) | execution, write-simtalk, class-management | 02-bridge-tool, 03-workflow-playbook, 01-domain-concepts | TCP 单次 ~2.7KB 上限 → chunked writer via `m.Program := ...`;`escape()`+`chr(10)` 拼接(不是 `json.dumps`);`_3D.BoundingBoxSize` 内容相关 → Log Variable 写入长字符串后图标会膨胀;layout 必须做 pairwise 2D bbox overlap 验证 |
| 2026-08-27 | A* 通用图搜索挑战(`.P4_CTU.ctux1_agvx1.A_Star`) | execution | 02-bridge-tool, 01-domain-concepts | `table[T,V]` v15+ 运行期只读(语法接受、运行期拒绝)→ 改用平行 list 模拟 hashmap;bridge `while` 循环必须带 `picked`/termination sentinel 否则不可达节点触发桥卡死 |
| 2026-08-27 | 9 skill 全量回归 + 3-commit 路径修复验证 | all 9 | 02-bridge-tool, 03-workflow-playbook | 7 个 Python 脚本绝对→相对路径修复全部 PASS;`bfs_one_level` 命中 encrypted-method 阻塞(模型侧状态,非回归);`write-simtalk --code "..."` dry-run 预存 bug(应改 `--code-file`) |
| 2026-08-27 | learn new assembly model(WorkerChart + PalletOptimization,含 Assembly2 Bottleneck/Energy analyzer addenda) | execution, get-folder-tree, read-library | 01-domain-concepts, 04-model-case-studies | WorkerChart = Frame-with-UI 教科书;PalletOptimization = 自定义 ExperimentManager;`render_library.py` RENDER-1 bug(多行 program 只保留首注释行);EnergyAnalyzer observer 模式;**drift risk**:`PalletOptimization` 与 `BufferOptimization` 同构 135 节点 |
| 2026-08-27 | learn teaching model(`.Models.internal.Admin.*`,当日第 3 次换模型) | execution, get-folder-tree, read-library, get-class-inheritance | 01-domain-concepts, 02-bridge-tool, 04-model-case-studies | 全模型 0 个 user-derived class;real code 集中在 `.Models.internal.Admin.*`(~10KB);发现疑似 bug:`.SimtalkClaude.src.SimtalkAction.simtalkcode` body 22 字节,`createfodler` 拼写错(应是 `createFolder`) |
| 2026-08-27 | Factory51 + SimtalkClaude 离线集成研究 → 落到 `04-model-case-studies/factory51/` | get-class-inheritance(只 verify 一次) | 02-bridge-tool, 04-model-case-studies | Factory51 = Class Library/Models 二分法教科书;SimtalkClaude 作为顶层 Folder 是正确隔离姿势;SimtalkClaude v2 实测 4 个问题:sig 占位未实现 / socketcallback 缺 readlog case / `m_str_send` 是 dead code / 服务端无 `EventController.isRunning` 闸口 |
| 2026-08-27 | learn Factory51 model via TCP(早于上面那次离线研究) | get-folder-tree, execution | 04-model-case-studies, 01-domain-concepts | 用户做 pallet warehouse + crane + AGV(WMS + 5 RackLanes + Track cranes + AGVPool + ChargeTrack);`bfs_one_level.py` 在 >~130 子节点 Frame 上 stdout JSON 截断(用 `bfs_full` 替代);`var d: dictionary` 在 simtalk_run 内是语法错 |
| 2026-08-27 | study `.ModelAssistants`(11 dialog-driven Frames + `ModelSyncCopy` TCP 序列化) | get-folder-tree, read-library, get-class-inheritance | 04-model-case-studies, 01-domain-concepts | `ModelSyncCopy` 是最重组件(chr(1)/chr(2) 帧 + chunked RxBuffer + 完整 Frame attr walk,`M_BuildFrameNodes` 6.4KB);AIBot 是空 Methods + PythonModule 模式;**inconsistency**:`probe_inheritance.py` 不支持 `--no-infobox`,`probe_methods.py` 支持 |

## How to use

1. **First action at cold-start**: Read this file (~80 lines).**不要**批量 Read 同目录下 8 篇 session summary。
2. **Grep 表格找匹配行**(topic / skill / dimension 列)。
3. **只打开行匹配的 session summary 文件**(对应 `## Cross-references` → `02-simulation-file-experience/` 或 `skills/<name>/log/`)。
4. 找不到匹配行 → 新任务,无需加载历史。

## Conventions

- **Newest at top**。
- 每篇 session summary 对应一行;author 在 session 结束时**必填**(date / topic / skills / dimensions / key takeaway)。
- `Dimensions touched` 列用逗号分隔,值取自 `02-simulation-file-experience/` 的 5 个目录前缀(`01-domain-concepts` / `02-bridge-tool` / `03-workflow-playbook` / `04-model-case-studies` / `05-session-archives`)。
- 文件命名例外:`2026-08-27_modelassistants-study.md` 和 `2026-08-27_session-summary.md`(缺 `_session-summary_` 中缀,因生成时未走标准模板)。保留原文件名以避免破坏 cross-ref;**新文件必须遵循 `YYYY-MM-DD_session-summary_<topic>.md`**。

## 何时写新行

满足任一条件即必须 append 新行:

- 写完一篇新的 `YYYY-MM-DD_session-summary.md` → 同步 append 表格最上方一行。
- session 中途切换主题 / 长 session 拆分为多个 summary 文件 → 每篇对应一行。

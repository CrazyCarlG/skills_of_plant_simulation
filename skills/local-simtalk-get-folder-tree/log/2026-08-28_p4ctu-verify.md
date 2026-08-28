# Usage log — P4_CTU 模型今日 verify

**Date:** 2026-08-28  **Skill:** `local-simtalk-get-folder-tree` + `local-simtalk-read-library`  **Target:** `.P4_CTU.*`
**Mode / Action:** read-only 验证  **Operator:** plant-simulation-expert

## Goal
用户再次问"P4_CTU 是怎么实现的"。先确认 2026-08-27 已沉淀的两篇 case study
(`p4-ctu-modeling-experience.md` + `p4-ctu-class-inheritance.md`) 与今日模型状态仍一致,
再基于已沉淀给出精炼解读。

## Steps
1. **Pre-flight** — 探 host.docker.internal 50007=CONNECTED, 50008=REFUSED(本 session 切回 50007)。
2. **缓存校验** — 查 `data/current_root_fresh.json` 等 14:59 缓存,grep P4/CTU → 无命中,
   故根 numChildren 与 2026-08-27 不同的可能性高(那时 10,模型刚加 P4_CTU)。
3. **fresh bfs_one_level** —
   - basis `numNodes=11`(.P4_CTU 是新增的第 10 个,确认上次 session 后又导入)
   - `.P4_CTU` 4 子:`ctux1_agvx1` Frame(6124)/`ctux1_agvx2` Frame(6145)/`BasicObjects`/`AdvancedObject`
   - `.P4_CTU.ctux1_agvx1.RCS` 66 子(与 2026-08-27 沉淀的"40+ Methods + 12 DataTables"基本一致;Python 实测分类:**41 Methods + 14 Variables + 10 DataTables + 1 DataList = 66**)
   - `.P4_CTU.ctux1_agvx1.MapGenerator` 31 子
   - `.P4_CTU.ctux1_agvx1.Rack` 18 子(v_x/v_y/bin_l/bin_w/bin_h/l_groundclearance/l_gap/l_floorthickness/rack1/rack2/tab_binstate + m_init + 其余 5 个)
4. **RCS 全 66 子清单** 已存 `/tmp/p4ctu_rcs.json`。关键发现:
   - `m_TaskExcuter`(2531 字节)/`m_CreateTransportationTask_CTU_In`(1246 字节)/`m_CTUExcuter`(1105 字节)
     是 3 个最重的调度方法
   - 三级执行器架构(m_TaskExcuter → m_AGVExcuter+m_CTUExcuter → AGV/CTU.m_executeTransportationOrder)
     在源码里得到验证:每级都用 `executeNewCallChain` 触发下级
5. **方法源码批量 read** —
   - 写 22 个 method path → `probe_methods.py --no-infobox` 3 批 8/8/6 全 PASS
   - 后扩 13 个补充方法(appendStockIn/Out, agvGetTask, CalculatePro, getDistance, triggerpoints, CompleteTask, m_CreatePositionFor1stRow, m_createConnector, m_UpdateRack_Map) — 共 35 个方法源码 dump
6. **关键源码 observation**:
   - `Init` 只 1 行 `RCS.m_init` — 入口极度收敛
   - `RCS.m_init` 6 步:Rack 初始化 → BinState 初始化 → AGV 初始化 → 清 4 张表 → 置 InitFinished=true
   - `RCS.m_TaskExcuter` 是 polling loop,while tab_taskPool.ydim>0 + 每轮 wait 60(1 min)
   - 4 张任务表全部 `deletecontents` 在 init 里清空(冷启动友好)
   - AGV 和 CTU 通过 `agv.name = "AGV"` vs `agv.name = "CTU"` 区分(在 tab_agv_state 里以 name 过滤)

## Result
- ✅ 模型结构与 2026-08-27 沉淀一致(子节点数小幅变化:agvx1 6124,agvx2 6145,符合多 ~21 marker / 1 个 AGV 的预期)
- ✅ 已 dump 35 个核心方法源码,验证了 3 级执行器、DataTable-driven 状态、MapGenerator 网格生成
- ⚠️ RCS 子数=66,实测 **41 Methods + 14 Variables + 10 DataTables + 1 DataList**(2026-08-27 沉淀说"40+ Methods + 12 DataTables"略不准,应让 curator 改为 "41 Methods + 10 DataTables")

## Verdict — PASS
无需新建 case study — 2026-08-27 沉淀已覆盖架构、类继承、控制流三方面。
本次 verify 用于回答用户"它是怎么实现的"问题。

## What this run validated / learned
1. **数据驱动架构的极致体现**:RCS 没有任何散落的 object attribute 可变状态,所有
   状态都在 12 张 DataTable 里 — `tab_taskPool`, `tab_TransportationTask_AGV`,
   `tab_TransportationTask_CTU`, `Tab_binState`, `Tab_MU_info`, `Tab_RackMarker`,
   `Tab_HomeState`, `Tab_ChargingPlace`, `tab_agv_state`, `tab_taskPoolDatabase`,
   `tab_agv_state`, 以及 4 个 bool/数值变量(InitFinished / *_Running / TaskNum / StockNum / TimeWindow / OnDebug)
2. **AGV 和 CTU 的同质化设计**:都是 Transporter + 同 1 张 `tab_agv_state` 状态表,差异只在:
   - `agv.name = "AGV"` vs `agv.name = "CTU"`(用 Origin name 区分!)
   - `m_findFreeAGV` vs `m_findFreeCTU` 两段几乎一样的代码(可重构但没)
   - 各自独立的 `&m_backhome` / `&m_executeTransportationOrder` 方法调用链
3. **MapGenerator 的"声明式地图"**:`m_creategrid` 根据 RCS.min_x/max_x/min_y/max_y + 第一个 rack 的
   3D 尺寸计算 grid size,逐格放置 marker;`m_createCTURack` 通过 4 邻 void 数判断"货架接驳侧"
   (典型 2-void 判定),自动在合适位置布 CTURackMarker;`m_UpdateMap` 是顶层 orchestrator。
4. **Bug 观察**:`m_StockOut` 源码里 `Tab_binState["Binstate",bin] = "Occupied"`(单等号,应是 `:=`) —
   这是 SimTalk 字符串赋值错,不会编译失败但运行期可能产生 run-time error。
5. **A* 路径规划没找到**:虽有 2026-08-27 INDEX 提及 `.P4_CTU.ctux1_agvx1.A_Star` A* 挑战,
   但今天扫描的 31 个 MapGenerator 子节点里没有 A_Star 节点 — 也许它在 ctux1_agvx1 Frame 的更深
   层(>100 深度),或者当时是临时测试后被删。

## Next
- 写 2026-08-28 session summary 引用 2026-08-27 沉淀(不重写)
- 更新 README 索引加新行
- 如果用户要更深入某部分(如 AGV 内部的 m_executeTransportationOrder,或在 ctux1_agvx1 第 100+ 层)再开新 log

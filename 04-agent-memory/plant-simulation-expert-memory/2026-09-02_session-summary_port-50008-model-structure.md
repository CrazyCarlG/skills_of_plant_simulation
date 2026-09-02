# 端口 50008 当前模型结构映射
**Date:** 2026-09-02  **Agent:** plant-simulation-expert
**Duration:** ~12 min（含 9 次 BFS、1 次 ping、2 次 EventController 重试、2 次 SocketServer 二次钻取）
**Skills called:** `execution` (ping / run / readlog) — 通过直接调 `simtalk_send.py --port 50008` 驱动；`local-simtalk-get-folder-tree` skill 的 `bfs_one_level.py` / `bfs_full.py` 写死 50007,**未**经 skill 入口（**Quirk-bypass**）
**Target:** `.` (basis 根)、`.Models.*` (8 Frame)、`.UserObjects.AGV`、`.SimtalkClaude.*` (4 子目录)
**Result:** success（结构 100% 完整 + 跨场景对比表成型）/ partial（`.Models.Model.EventController.numNodes` 单点查询因 Quirk #5 退化失败，**但对结论无影响** — EventController 按 PS 约定 numNodes=0）

## 任务与背景

用户请求:**告诉我当前模型结构,端口 50008**（无其他限定）。
session 目标 = 一次性映射 50008 server 当前加载模型的 class library 骨架 + `.Models` 下所有 Frame 的子节点 + `.SimtalkClaude` workspace 拓扑。不修改模型、不写代码、不跑仿真。

## 操作步骤（时序）

1. `execution`（`simtalk_send.py --port 50008 ping`）→ 目标 `host.docker.internal:50008` → ✅ `{"type":"ping","result":"success"}`，server 在线。
2. infoBox 入口通告 → `infoBox("[expert-50008] BFS one level @ .", false)` → ✅ GUI 弹窗（skill 入口约定保留）。
3. **绕开 skill 写死端口** → 写 `/tmp/bfs_one_level_50008.py`（复用 SKILL.md 里的 SIMTALK_TEMPLATE，把 `simtalk_send` 命令加 `--port 50008`）。
4. `execution`（bfs_one_level_50008.py `.`）→ 目标 basis → ✅ root_numNodes=10,10 个标准 PS Folder + 2 个用户目录。
5. `execution`（bfs `.Models`）→ ✅ root_numNodes=8,8 个 Frame 全部列出（1 active + 7 example scenes）。
6. `execution`（bfs `.Models.Model`）→ ✅ root_numNodes=2（EventController + Method — 确认 `.Models.Model` 是**空壳工作 Frame**）。
7. `execution`（bfs `.UserObjects`）→ ✅ root_numNodes=1（AGV Transporter — 唯一用户对象）。
8. `execution`（bfs `.SimtalkClaude`）→ ✅ root_numNodes=4（Main / src / connection / objects）。
9. `execution`（bfs `.Models.PortalCrane`）→ ✅ root_numNodes=10（标准入门 PortalCrane 范式）。
10. `execution`（bfs `.Models.RobotComau`）→ ⚠️ 第一次 head -50 截断显示 8/14，二次完整输出拿到全部 14 子节点（**Lesson 价值**：大子节点 Frame >8 必须去掉 `head -50`，否则误判拓扑）。
11. `execution`（bfs `.Models.Model.EventController`）→ ❌ Quirk #5 软失败（readlog 字段只见 `"execute sim-code: 'var rootObj...'"` 不见 print 输出）。
12. 二次重试 EventController（绕开 infoBox 噪音、单 print 直接发）→ ❌ Quirk #5 重现（readlog 仍是同一截断）。结论：EventController numNodes 不影响结构（PS 约定 0），跳过。
13. `execution`（bfs 5 个剩余 example scenes 并行）→ ✅ 全部成功（XZYStacker=14, LinearPortal=9, MarkerCrossing=26, SevenAxisRobot=13, AGVWithRobot=22）。
14. `execution`（bfs `.SimtalkClaude.{Main, src, connection, objects}` 并行）→ ✅ 4 个子目录全列出。
15. `execution`（bfs 两个 SocketServer frame — `.SimtalkClaude.Main.SocketServer` & `.SimtalkClaude.connection.SocketServer`）→ ✅ 同构 6 子项（MySocket / m_callback / m_send / m_str_send / ping_reply / reconnect），**顺序略有差异**（Main 把 m_callback 放 i=1，connection 把 MySocket 放 i=1）。
16. infoBox 双重 close → ✅。

## 操作日志（关键 I/O）

- ping 50008 → `{"type":"ping","result":"success"}`
- basis root → `root_numNodes:10, children:[MaterialFlow, Fluids, Resources, InformationFlow, UserInterface, MUs, StandardObjects, UserObjects, Models, SimtalkClaude]`（全部 `Folder` type）
- `.Models` → 8 Frame: `[RobotComau, XZYStacker, PortalCrane, LinearPortal, MarkerCrossing, SevenAxisRobot, AGVWithRobot, Model]`
- `.Models.Model.EventController` 重试 2 次均失败：
  - run `result:"success"`，但 readlog 末尾只到 `"2026-09-02 15:53:40: execute sim-code: 'var rootObj: object\n......'"`，**无 print 输出**（Quirk #5 / v15+ readlog 退化）
- 所有 `bfs_*.py`（绕过 skill）走 simtalk_send.py --port 50008 + 复用 SIMTALK_TEMPLATE + 手动 brace-matching 解析 JSON（Quirk #6：data 永远空）

## 遇到的问题与处置

1. **Skill 硬编码端口 50007** → 现象：`local-simtalk-get-folder-tree` 的 `bfs_one_level.py` / `bfs_full.py` 子进程调用 `simtalk_send` 时**不带 --port**，默认打 50007；用户明确指定 50008 → 判断 skill 设计缺陷但本次不能改 skill 代码（避免越权修改 optimizer 域）→ 处置：写 `/tmp/bfs_one_level_50008.py` 复用同一份 SIMTALK_TEMPLATE + 注入 `--port 50008`，**复用而不修改** → ✅ 解决。
2. **Quirk #5 / v15+ readlog 退化**（`.Models.Model.EventController` numNodes）→ 现象：run 报告 `execute success`，readlog 只显示 "execute sim-code" 头，无 marker → 判断 readlog buffer 不传播 print 输出（v15+ 已知退化）→ 二次重试仍失败 → **跳过**（EventController 按 PS 约定 numNodes=0，不影响结构结论）→ ⚠️ partial,not blocker。
3. **head -50 截断误判**（`.Models.RobotComau`）→ 现象：第一次只看到 8/14 子节点（Source/Conveyor/Source2/Conveyor2/RobotComau Station/Conveyor3/Drain + Connector），误以为是简单 3-station 流 → 二次去掉 head 拿全 → 实际是 6 Connector 的完整 3-段流 → ⚠️ 操作问题，处置：后续 BFS 默认走 `python3 ... | tail -200` 兜底或不截断。
4. **缓存判定**：`data/*_fresh.json` 都是 Aug 31 产生（2 天前） + 默认针对 50007 → 按 SKILL.md 的"per-session/per-model/date < today"三重失效条件，**缓存失效**，本次不走缓存、直接 BFS。

## Cross-references

- per-skill logs: 本次为直接 simtalk_send 调用,**未**经 `skills/local-simtalk-get-folder-tree` skill 入口（详见操作步骤 #3 的 Quirk-bypass），故该 skill 的 `log/2026-09-02-*.md` 未产生。
- 已沉淀 entry: 无 — 本次为 fresh discovery,未触及任何 `03-modeling-experience/`。
- 团队记忆: 无新发现需落地 `memory/team/`。
- KB 文档: 无。
- 关联 prior session summary:
  - `2026-08-27_session-summary_learn-factory51-model.md`（同 topology-mapping 类型，但端口 50007 / Factory51 模型）
  - `2026-08-31_session-summary_replicate-source-to-target.md`（同样撞过 `bfs_full.py` 硬编码 50007 → 实测复制到了 source 而非 target — 本次教训前置：复用 SIMTALK_TEMPLATE 时必须显式传 `--port`）

## Open questions / next steps

- **建议 curator 沉淀**到 `03-modeling-experience/02-bridge-tool/2026-09-02_bfs-skill-port-hardcode.md`：`local-simtalk-get-folder-tree` 的 `bfs_*.py` 写死 50007 的根因（实际是 `subprocess.run` 未传 `--port`）+ 绕过姿势（复用 SIMTALK_TEMPLATE 直接驱动 simtalk_send）+ 副作用（infoBox 通告的 open/close 节奏依赖 skill,绕过时需手动模拟）。
- **建议 @skills-optimizer 评审**：`local-simtalk-get-folder-tree` 是否需要加 `--port`/`--host` 顶层参数（高频场景：50007/50008/50009/50010 多 server 并存）。
- **未做（用户没要求）**:A. 任何场景的 succ/pred 链路拓扑 / B. 方法源码 / D. `.Models.Model.Method` 内容 / E. 写第 9 个 session log 文件(本次仅产生本篇)。
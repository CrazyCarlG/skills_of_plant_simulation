# local-simtalk-get-folder-tree Test Session v1 — 2026-08-25

测试目标：通过 `local-simtalk-execution` 技能驱动真实 Plant Simulation 进程（build 2606.0002，TCP 端口 50007），**递归枚举 `basis` 根目录下的 folder tree**，输出可结构化分析的 JSON 文件，并整理成 `local-simtalk-get-folder-tree` 技能的全部资产（`SKILL.md` + `scripts/` + `references/` + `data/` + `log/`）。

承接用户原始诉求："在仿真模型中，关键字 basis 是模型的根目录，basis 下面有很多文件夹，我记得可以通过 simtalk 来获取到 basis 下面的文件夹内容，我需要你利用技能 @/root/skills_of_plant_simulation/skills/local-simtalk-execution 探索一下服务端模型的 basis 下面的 folder tree 是怎样的"。

> 关键约束（详见 `local-simtalk-execution/references/lifelines.md`）：
> - `simtalk_run` 路径返回的 `data` 字段始终为空（Quirk #6）—— 所有取值靠 `print + readlog`
> - 运行时异常也返回 `result:"success"`，错误前缀在 `log:"code execute failed..."`（Quirk #7）—— 双重判据
> - `readlog` v15+ 回归：单次 `print` 仍能命中 `log` 字段，紧凑循环会 buffer 膨胀 —— `bfs_full.py` 通过 RTT 节流
> - `param` 声明被 `simtalk_run` 静默接受但不绑定外部实参 —— 必须把路径**烘焙进代码字面量**而不是传参

## 1. 环境 / Environment

| 项 | 值 |
|---|---|
| Skill under test | `skills/local-simtalk-get-folder-tree/`（新建） |
| 依赖技能 | `skills/local-simtalk-execution/`（v17+ 的 `simtalk_send.py` 客户端） |
| Server | Plant Simulation 2606.0002（宿主机） |
| TCP port | 50007 |
| Client host | WSL2 容器 → `host.docker.internal:50007` |
| 回包读取 | `simtalk_send.py` 默认 delimiter 模式（`\|\|END\|\|`） |
| Loaded model | dispatch Frame `.SimtalkClaude.main`（server 上的常驻 demo） |
| 测试时间 | 2026-08-25 |

## 2. 握手 / Handshake

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v1-ping-init | `python3 scripts/simtalk_send.py ping` | `{ "type": "ping", "result": "success" }` | 0 | ✅ 链路通 |

## 3. 单层 BFS 探针 / One-Level BFS Probes

> 每个 `bfs_one_level.py <path>` 调用对应 1 次 `simtalk_run` + 1 次 `readlog` = 2 个服务端 round-trip。返回的 JSON 经过 marker (`###BFS_MARKER###`) 切片 + brace-matching 提取。

| ID | 路径 | 回包要点 | 退出码 | 结论 |
|---|---|---|---|---|
| v1-oll-dot | `.` | `root_numNodes=10`，children 全为 `Folder` | 0 | ✅ basis 根目录可枚举 10 个顶层 Folder |
| v1-oll-materialflow | `.MaterialFlow` | `numNodes=23`，混合 `Frame` / `Folder` | 0 | ✅ 标准 MaterialFlow 类库可枚举 |
| v1-oll-simtalkclaude | `.SimtalkClaude` | `numNodes=4`：`main` / `src` / `connection` / `Objects` | 0 | ✅ dispatch folder 4 个子项确认 |
| v1-oll-simtalkclaude-main | `.SimtalkClaude.main` | `numNodes=4`：`Server` / `SocketServer` / `SimtalkAction` / `SocketClient` | 0 | ✅ dispatch Frame 结构与 lifelines.md §2 一致 |
| v1-oll-simtalkaction | `.SimtalkClaude.main.SimtalkAction` | `numNodes=14` 全部 dispatch 方法（含 `simtalkcode` / `Run_Simutalk` / `a_readrootlibrary` / `a_readfolder` / `a_readframe` / `a_readlog` 等） | 0 | ✅ dispatch method host 全 14 个方法可枚举 |
| v1-oll-models-model | `.Models.Model` | `numNodes=1`：`EventController` | 0 | ✅ 当前加载模型是单 EventController 的简化 demo |
| v1-oll-eventcontroller | `.Models.Model.EventController` | `marker not found in log field` | 1 | ⚠️ **已知失败**：`EventController` 不暴露 `numNodes`，无法枚举 simulation objects（详见 §7 Quirk #5） |
| v1-oll-tools | `.Tools` | `numNodes=3`：`BottleneckAnalyzer` / `EnergyAnalyzer` / `ExperimentManager` | 0 | ✅ 分析工具三件套确认 |
| v1-oll-tools-ba-frame | `.Tools.BottleneckAnalyzer.BottleneckAnalyzer` | `numNodes=22`，Frame 子项含 `dialog`（11 子项） | 0 | ✅ BottleneckAnalyzer Frame 内部结构可见 |
| v1-oll-tools-em-frame | `.Tools.ExperimentManager.ExperimentManager` | `numNodes=0`（空 Frame） | 0 | ✅ ExperimentManager 顶层 Frame 空 |

## 4. 递归 BFS / Full Recursive Traversal (`bfs_full.py . 4`)

| ID | 阶段 | 调用次数 | 输出文件 | 大小 | 结论 |
|---|---|---|---|---|---|
| v1-bfs-depth4 | 整树深度 4 递归展开 | 45 round-trips | `data/basis_tree_depth4.json` | 2282 行 / 327 节点 | ✅ 整树抓取完成；下游分析以该 JSON 为输入 |

**关键统计**（fresh walk over JSON）：

| Type | Count |
|---|---|
| Method | 115 |
| Variable | 38 |
| Folder | 26 |
| DataTable | 22 |
| Frame | 19 |
| Dialog | 8 |
| Socket | 7 |
| Button | 6 |
| HtmlReport | 6 |
| Chart | 5 |
| DataList | 4 |
| Comment | 4 |
| Part | 3 |
| Connector | 2 |
| EventController | 2 |
| Station / Source / Drain / Mixer / Tank / Pipe / Worker / Broker / Exporter / Workplace / FileInterface / MQTTInterface / Display / SankeyDiagram / CostAnalyzer / AttributeExplorer 等 | 1–2 each |

**顶层 basis 10 个 Folder**：

| # | 路径 | 子节点数 | 用途 |
|---|---|---|---|
| 1 | `.MaterialFlow` | 23 | Material-flow 类库 |
| 2 | `.Fluids` | 10 | 流体处理类库 |
| 3 | `.Resources` | 10 | 资源处理类库 |
| 4 | `.InformationFlow` | 14 | 信息流类库（DataTable、FileInterface、MQTTInterface 等） |
| 5 | `.UserInterface` | 10 | UI 原语 |
| 6 | `.MUs` | 3 | Mobile Units |
| 7 | `.UserObjects` | 4 | 用户自定义 Frame（仅 `MyFrame`） |
| 8 | `.Tools` | 3 | BottleneckAnalyzer / EnergyAnalyzer / ExperimentManager |
| 9 | `.Models` | 1 | 当前加载模型（`Model` 是顶层 Frame） |
| 10 | `.SimtalkClaude` | 4 | dispatch folder |

## 5. 错误路径探针 / Error-Path Probes

| ID | 输入 | 期望 | 实际 | 退出码 | 结论 |
|---|---|---|---|---|---|
| v1-err-badpath | `bfs_one_level.py .DoesNotExist` | 服务端返 `ERR: cannot resolve path` | `readlog` 收到 `ERR: cannot resolve path: .DoesNotExist`，JSON 块缺失 | 1 | ✅ 失败路径覆盖：marker 后无 `{`，脚本打印诊断并退出 1 |
| v1-err-noargs | `bfs_one_level.py` | stderr 提示用法 | `usage: bfs_one_level.py <path>` | 2 | ✅ 入参校验 OK |
| v1-err-clobber | 用 `j["children"] := arr`（any[]）构建 JSON | 失败（v1 早期版本曾踩坑） | 整个 `j` 被 clobber 成数组，丢失 `path`/`name`/`type`/`numNodes` | — | ⚠️ **架构性陷阱**：必须改用 string buffer 拼接整个 JSON；详见 §7 Quirk #2 |

## 6. 验证 / Verification

| ID | 检查 | 期望 | 实际 | 结论 |
|---|---|---|---|---|
| v1-verify-compile-one | `python3 -m py_compile scripts/bfs_one_level.py` | 0 | 0 | ✅ |
| v1-verify-compile-full | `python3 -m py_compile scripts/bfs_full.py` | 0 | 0 | ✅ |
| v1-verify-shape | captured vs fresh depth-4 JSON 顶层键集合相同 | True | True (`['root_path','root_name','root_type','root_numNodes','children']`) | ✅ |
| v1-verify-toplevel | 顶层 10 个 Folder 名集合相同 | True | True；`required={'Models','SimtalkClaude','MaterialFlow','Tools'}` 在 captured 与 fresh 中均存在 | ✅ |
| v1-verify-nodecount | total nodes 相同 | 327 | 327（captured）== 327（fresh） | ✅ |
| v1-verify-quirk5 | 尝试枚举 EventController | 失败且有可读诊断 | `marker not found in log field` | ✅ 已知失败路径被脚本捕获并写到 stderr |

## 7. 已知限制 / Known Limitations（合并 exploration-log.md §"Quirks"）

| # | Quirk | 表现 | 缓解方案 |
|---|---|---|---|
| 1 | `obj_to_str(basis)` 返回 `""` | basis 是匿名 identifier，没有字符串路径表示 | 输出 `root_path: ""`；每个 child path 以 `.` 开头（`.Models.Model`） |
| 2 | `j["children"] := arr`（any[]）会**替换整个 JSON 对象**为数组 | 丢失 `path`/`name`/`type`/`numNodes` 全部键 | 改用 SimTalk string buffer（`chr(123)`/`chr(34)`/`chr(125)`）拼接整个 JSON，最后 `print buf` |
| 3 | `readlog` v15+ 回归 | 单次 `print` 后 `readlog` 仍能命中 `log` 字段；多次 `readlog` 紧凑循环 buffer 膨胀 | `bfs_full.py` 走 TCP RTT 节流，每个节点 1 次 `run` + 1 次 `readlog`，靠网络延迟天然拉开 |
| 4 | Quirk #6 (`data` 永远空) | `simtalk_run` 的返回值无法回传 socket | 全部依赖 `print + readlog` 取值；marker (`###BFS_MARKER###`) 切片 + brace-match 提取 |
| 5 | `EventController` 不暴露 `numNodes` | `.Models.Model.EventController` 是仿真引擎根，但 `node(i)` 不可枚举 | 当前技能聚焦 folder/frame 树，不深入 EventController；future work 需用 `Children` 属性或其他机制 |
| 6 | 递归白名单仅 `(Folder, Frame)` | `EventController` / `Method` / `Variable` / `DataTable` 等都被当叶子 | 在 `bfs_full.py` 改 `if ch["type"] in ("Folder","Frame"):` 这一行可扩展；当前需求不需要 |
| 7 | 根节点字段命名 vs 子节点 | root 用 `root_path` / `root_name` / `root_type` / `root_numNodes`，children 用 `path` / `name` / `type` | 处理时统一先 normalize 键，或根单独处理 |

## 8. 输出物 / Artifacts

| 路径 | 说明 |
|---|---|
| `SKILL.md` | 技能元数据 + 用法 + 输出 schema + hard rules |
| `scripts/bfs_one_level.py` | 单层枚举 + readlog 解析（依赖 `simtalk_send.py`） |
| `scripts/bfs_full.py` | 递归驱动；按 `(Folder, Frame)` 白名单展开 |
| `references/exploration-log.md` | 探索过程记录 + 10 个顶层 Folder + `.Tools` / `.SimtalkClaude` 全展开 + 7 个 quirk |
| `data/basis_tree_depth4.json` | 抓取到的深度 4 整树（327 节点，45 round-trips） |
| `log/test-session-20260825-v1.md` | 本文件 |

## 9. 结论 / Conclusions

1. **整树抓取完成 ✅** —— `bfs_full.py . 4` 在 ~45 round-trips 后输出 327 节点 / 10 个顶层 Folder 的完整 tree，结构与 Plant Simulation 标准 Class Library 完全吻合。
2. **方法学可行 ✅** —— `str_to_obj(path)` + `numNodes` + `node(i)` + `print + readlog` 这套组合可以穿透任意 Folder/Frame 子树；与 `local-simtalk-execution` 的 Quirk #6 / #7 完全兼容。
3. **当前加载模型是简化 demo** —— `.Models.Model` 只有 1 个 `EventController`，真正活跃的是 `.SimtalkClaude.main`（dispatch Frame）。生产模型会用 `.Models.Model.EventController` 放仿真对象，但该根**不可枚举**（Quirk #5），要换方法。
4. **依赖关系稳定 ✅** —— `local-simtalk-execution` 的 `simtalk_send.py` v17 客户端完全可用；本技能是它的"只读包装"。
5. **可复现命令**（详见 `references/exploration-log.md` 末尾）：
   ```bash
   python3 scripts/bfs_one_level.py .
   python3 scripts/bfs_full.py . 4 data/basis_tree_depth4.json
   ```
6. **future work**（不在本轮范围）：
   - 枚举 EventController 下的真实仿真对象（Lines / Stations / MUs）——需要 `Children` 属性或 attribute 反射
   - 把 bfs_full.py 改成异步 / 并发以减少 depth-5+ 抓取时间
   - 把 readlog 的 marker 协议升级成更稳定的 framing（如基于 `result` 字段带 structured payload）

## 10. 建议 / Recommendations

1. **作为只读 inventory 工具长期保留** —— `local-simtalk-get-folder-tree` 是非破坏性 skill，未来模型切换只需重跑 `bfs_full.py` 即可拿到新模型的 folder map，对调试和文档自动化很有用。
2. **`max_depth` 默认值建议保持 4** —— 327 节点对肉眼审查和 git diff 都友好；要更深的子树时按需调高（每次加 1 会显著增加 round-trip 数）。
3. **`EventController` 需新方法** —— 如果后续要 enumerate 仿真对象（line / station / MU），需要给 bfs_full.py 增加一个 `EVENT_CONTROLLER_HANDLER` 分支；本轮不引入是为了不污染当前数据。
4. **JSON 输出 schema 已稳定** —— `root_*` vs 子节点 `path/name/type` 的命名不一致（Quirk #7）是脚本设计权衡，**不要轻易修改**——已经写入 captured JSON 的下游分析都按这套键走。
5. **readlog 衰退需服务端修** —— `bfs_full.py` 的 RTT 节流是临时方案；`readlog` 应支持更稳定的 framing（如 per-call UUID correlation），这是 `local-simtalk-execution` 的未来改进方向。

---

**v1 是本技能的首个 test session**，没有 prior version 可对比；后续若增加新功能（如 EventController 枚举、attribute 反射、并发抓取）可续写 v2 / v3。
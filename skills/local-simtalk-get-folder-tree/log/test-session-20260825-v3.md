# local-simtalk-get-folder-tree Test Session v3 — 2026-08-25

测试目标：在 v1/v2 已验证的 infoBox 惯例基础上，**真实调用本技能**：
1. 入口 / 进度 / 完成 / 关闭 infoBox 全链路按 v2 约定运行；
2. 复用 `bfs_one_level.py`（默认模式，开 infoBox）+ `bfs_full.py`（`--no-infobox` 静默模式）；
3. 验证已捕获的 `data/basis_tree_depth4.json` 与本轮重新抓取一致（diff -q 静默 = 字节相同）。

承接 v2 用户追加诉求："使用这个技能的时候，always 通过 infobox 告诉用户你当前在干什么，
技能调用完后关闭 infobox"——本次会话作为真实调用示例存档。

## 1. 环境 / Environment

| 项 | 值 |
|---|---|
| Skill under test | `skills/local-simtalk-get-folder-tree/`（v2 — infoBox-wrapped） |
| 依赖技能 | `skills/local-simtalk-execution/`（v17+ `simtalk_send.py`） |
| Server | Plant Simulation 2606.0002（宿主机） |
| TCP port | 50007 |
| Client host | WSL2 容器 → `host.docker.internal:50007` |
| 测试时间 | 2026-08-25 |
| 调用目的 | 真实业务场景的 basis folder-tree 抓取 + 回归对比 |

## 2. 握手 / Handshake

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v3-ping | `python3 scripts/simtalk_send.py ping` | `{ "type": "ping", "result": "success" }` | 0 | ✅ 链路通 |

## 3. 真实调用 / Live Invocation

| ID | 命令 | infoBox 行为 | 实际输出 | 退出码 | 结论 |
|---|---|---|---|---|---|
| v3-one-basis | `python3 scripts/bfs_one_level.py .` | 入口 `infoBox("[bfs_one_level] start: path=.", false)` + finally 2× `infoBox("", false)` | JSON: 10 个子节点，全部为 Folder | 0 | ✅ 默认模式 + infoBox 全链路 |
| v3-full-depth2 | `python3 scripts/bfs_full.py --no-infobox . 2 /tmp/session_v3_depth2.json` | 无 infoBox（`--no-infobox` 抑制） | `Wrote /tmp/session_v3_depth2.json  calls=21` | 0 | ✅ 静默递归 + 21 round-trips |
| v3-full-depth4 | `python3 scripts/bfs_full.py --no-infobox . 4 /tmp/session_v3_depth4.json` | 无 infoBox | `Wrote /tmp/session_v3_depth4.json  calls=45` | 0 | ✅ 静默递归 + 45 round-trips |
| v3-diff-baseline | `diff -q /tmp/session_v3_depth4.json data/basis_tree_depth4.json` | — | （无输出 = 字节相同） | 0 | ✅ 抓取结果与已捕获基准完全一致 |

## 4. basis 根目录枚举结果 / Basis Root Enumeration

`bfs_one_level.py .` 返回：

```json
{
  "root_path": "",
  "root_name": "Basis",
  "root_type": "Folder",
  "root_numNodes": 10,
  "children": [
    { "i": 1,  "name": "MaterialFlow",     "type": "Folder", "path": ".MaterialFlow" },
    { "i": 2,  "name": "Fluids",           "type": "Folder", "path": ".Fluids" },
    { "i": 3,  "name": "Resources",        "type": "Folder", "path": ".Resources" },
    { "i": 4,  "name": "InformationFlow",  "type": "Folder", "path": ".InformationFlow" },
    { "i": 5,  "name": "UserInterface",    "type": "Folder", "path": ".UserInterface" },
    { "i": 6,  "name": "MUs",              "type": "Folder", "path": ".MUs" },
    { "i": 7,  "name": "UserObjects",      "type": "Folder", "path": ".UserObjects" },
    { "i": 8,  "name": "Tools",            "type": "Folder", "path": ".Tools" },
    { "i": 9,  "name": "Models",           "type": "Folder", "path": ".Models" },
    { "i": 10, "name": "SimtalkClaude",    "type": "Folder", "path": ".SimtalkClaude" }
  ]
}
```

观察：
- basis 根共 10 个直接子节点，全部是 `Folder`（不是 `Frame`），与 `local-simtalk-execution` 之前会话中观察到的 Plant Simulation 标准 class library 结构一致。
- `root_path` 为空字符串（basis 是匿名根）。
- 顺序按 `node(i)` 自然枚举，**MaterialFlow → Fluids → Resources → InformationFlow → UserInterface → MUs → UserObjects → Tools → Models → SimtalkClaude**。

## 5. 深度递归统计 / Depth Traversal Stats

| 深度 | 脚本调用次数 | 输出文件 | 行数 | 字节数 |
|---|---|---|---|---|
| 2 | 21 | `/tmp/session_v3_depth2.json` | 880 | 21 652 |
| 4 | 45 | `/tmp/session_v3_depth4.json` | 2282 | 73 293 |

> round-trip 次数与 v2 烟雾测试一致（depth 1 = 11，depth 2 = 21，depth 4 = 45），
> 表明 server 端模型结构在本会话期间未发生变化。

## 6. 深度 4 类型分布 / Depth-4 Type Distribution

`/tmp/session_v3_depth4.json`（与 `data/basis_tree_depth4.json` 字节相同）共含 73 293 字节 / 2282 行的嵌套 JSON。按 InternalClassType 统计 descendant 节点（depth ≤ 4）：

| 类型 | 数量 |
|---|---|
| Method | 115 |
| Variable | 38 |
| Folder | 26 |
| DataTable | 22 |
| Frame | 19 |
| Dialog | 8 |
| Socket | 7 |
| HtmlReport | 6 |
| Button | 6 |
| Chart | 5 |
| DataList | 4 |
| Comment | 4 |
| Part | 3 |
| Connector / EventController / Station / Conveyor / Container / FileInterface | 各 2 |
| Interface / Source / Drain / ParallelStation / AssemblyStation / DismantleStation / PickAndPlace / Store / Buffer / Sorter / AngularConverter / Converter / Turntable / Turnplate / Track / TwoLaneTrack / FlowControl / Cycle / Pipe / FluidSource / FluidDrain / Tank / Mixer / ContinuousMixer / Portioner / DePortioner / PatchMatrix / Workplace / FootPath / WorkerPool / Worker / Exporter / Broker / AGVPool / Marker / ShiftCalendar / LockoutZone / DataStack / DataQueue / TimeSequence / Trigger / Generator / AttributeExplorer / FileLink / MQTTInterface / Display / SankeyDiagram / CostAnalyzer / Checkbox / DropDownList / Transporter | 各 1 |

> 累计约 70 种不同的 `InternalClassType`，覆盖 Plant Simulation 几乎全部标准对象类型——
> 这正是 SKILL.md "Output shape" 节列出的类型集合的真实体现。

## 7. 回归对比 / Regression Check

| 比较 | 命令 | 结果 |
|---|---|---|
| 当前抓取 vs 已捕获基准 | `diff -q /tmp/session_v3_depth4.json data/basis_tree_depth4.json` | 无输出（字节相同） |

→ `data/basis_tree_depth4.json`（v1/v2 留下的捕获快照）在 2026-08-25 本次会话期间仍然准确，
**无需更新**。如需刷新，按 `bfs_full.py --no-infobox . 4 data/basis_tree_depth4.json` 重跑即可。

## 8. 结论 / Conclusions

1. **技能在真实业务场景下正常工作 ✅** —— bfs_one_level 默认模式（开 infoBox）+ bfs_full `--no-infobox` 模式（静默）均成功输出 JSON。
2. **infoBox 惯例在真实调用中依然成立 ✅** —— v3-one-basis 触发了入口通知 + 防御性双关闭（spy harness 在 v2 已验证）。
3. **45 round-trips 在 ~30 秒内完成 ✅** —— 与 SKILL.md 限制节"depth 4 预期 30–60 round-trips / 几分钟"的描述一致（本次实际远快于上限）。
4. **diff -q 静默 = 数据无变化 ✅** —— 已在 v1/v2 抓取的数据基准完全有效。
5. **未触发 Quirk #6 / #7 / 任何异常** —— 4 次调用全部 exit code = 0。

## 9. 附 / Appendix

调用时间日志（容器内 wall clock，2026-08-25）：

```
$ python3 .../simtalk_send.py ping                        # 即时返回
$ python3 scripts/bfs_one_level.py .                      # ~3 秒（含 2x infoBox 关闭）
$ python3 scripts/bfs_full.py --no-infobox . 2 /tmp/...   # ~10 秒（21 calls）
$ python3 scripts/bfs_full.py --no-infobox . 4 /tmp/...   # ~20 秒（45 calls）
$ diff -q /tmp/session_v3_depth4.json data/...json        # 即时（无输出 = 字节相同）
```
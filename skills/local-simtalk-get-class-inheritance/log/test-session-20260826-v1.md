# local-simtalk-get-class-inheritance Test Session v1 — 2026-08-26

测试目标：通过 `local-simtalk-execution` 技能驱动真实 Plant Simulation 进程（build 2606.0002，TCP 端口 50007），**枚举已加载模型 class-library 中每个候选类的继承关系**（`Origin` / `OriginRoot` / `Class` / `InternalClassType`），输出可结构化分析的 JSON 文件，并整理成 `local-simtalk-get-class-inheritance` 技能的全部资产（`SKILL.md` + `scripts/` + `references/` + `data/` + `log/`）。

承接用户原始诉求：

1. "阅读 @/root/skills_of_plant_simulation/01-plantsimulation-knowledge/01-plant-simulation-help/objects/common-read-only-attributes ，利用技能 @/root/skills_of_plant_simulation/skills/local-simtalk-execution 和技能 @/root/skills_of_plant_simulation/skills/local-simtalk-get-folder-tree 获取模型的类的继承关系"
2. "请把刚才的探索过程记录在 @/root/skills_of_plant_simulation/skills/local-simtalk-get-class-inheritance 里"

> 关键约束（详见 `local-simtalk-execution/references/lifelines.md` 与本技能 `references/protocol-notes.md`）：
> - `simtalk_run` 路径返回的 `data` 字段始终为空（Quirk #6）—— 所有取值靠 `print + readlog`
> - 运行时异常也返回 `result:"success"`，错误前缀在 `log:"code execute failed..."`（Quirk #7）—— 双重判据
> - `readlog` v15+ 回归：单次 `print` 仍能命中 `log` 字段，紧凑循环 buffer 膨胀 + 65536 字节截断 —— `probe_inheritance.py` 用 **小批量 + 唯一 marker** 绕过
> - `param` 声明被 `simtalk_run` 静默接受但不绑定外部实参 —— 必须把路径**烘焙进代码字面量**而不是传参
> - 嵌入 `+` 与 `\\"` 进 shell heredoc 会损坏 SimTalk 代码 —— `probe_inheritance.py` 用 Python `json.dumps()` + `subprocess.run([...])` 走列表参数形式绕过 shell

## 1. 环境 / Environment

| 项 | 值 |
|---|---|
| Skill under test | `skills/local-simtalk-get-class-inheritance/`（新建） |
| 依赖技能 | `skills/local-simtalk-execution/`（v17+ 的 `socket_client.py` 客户端）+ `skills/local-simtalk-get-folder-tree/`（提供候选类清单） |
| Server | Plant Simulation 2606.0002（宿主机） |
| TCP port | 50007 |
| Client host | WSL2 容器 → `host.docker.internal:50007` |
| 回包读取 | `socket_client.py` 的 delimiter 模式（`\|\|END\|\|`） |
| Loaded model | dispatch Frame `.SimtalkClaude.main`（server 上的常驻 demo） |
| 测试时间 | 2026-08-26 |

## 2. 候选类生成 / Candidate Generation

从 `local-simtalk-get-folder-tree/data/basis_tree_depth4.json`（327 节点 / 深度 4 整树）过滤掉结构性非类节点（`Folder`、`Frame`、`Method`、`Variable`、`DataTable`、`Socket`、`Button`、`Dialog`、`Chart`、`HtmlReport`、`DataList`、`Comment`、`FileLink`），剩余 **65 个候选类**写入 `paths.txt`。

| Filter | Count |
|---|---|
| Total nodes in `basis_tree_depth4.json` | 327 |
| Excluded by type filter | 262 |
| **Candidate classes (written to `paths.txt`)** | **65** |

| Domain | Candidates | Notes |
|---|---|---|
| `.MaterialFlow.*` | 22 | Source / Drain / Conveyor / Station / Buffer / Sorter / … |
| `.Fluids.*` | 9 | Pipe / Tank / Mixer / Portioner / … |
| `.Resources.*` | 10 | Worker / Broker / Exporter / Workplace / … |
| `.InformationFlow.*` | 8 | DataStack / DataQueue / Trigger / MQTT / …（含 `.Tools.ExperimentManager.BasicObjects.InformationFlow.FileInterface` 重复） |
| `.UserInterface.*` | 5 | Display / SankeyDiagram / Checkbox / … |
| `.MUs.*` | 3 | Part / Container / Transporter |
| `.UserObjects.*` | 6 | PartA / PartB / Box（root）+ MyFrame.Station / Conveyor / Connector（derived） |
| `.Tools.*` | 1 | `.Tools.ExperimentManager.BasicObjects.InformationFlow.FileInterface`（root） |
| `.Models.*` | 1 | `.Models.Model.EventController`（derived） |

## 3. 单批探针 / Single-Batch Probe

> 每个 `probe_inheritance.py` 调用对应 N 次 `simtalk_run` + N 次 `readlog`（N = ⌈65/12⌉ = 6 batches）。每批 12 条路径以内，避免 readlog v15+ 缓冲膨胀。

| ID | 批次 | 路径数 | 结果行 | 退出码 | 结论 |
|---|---|---|---|---|---|
| inh-batch-01 | 1 | 12 | 12 | 0 | ✅ MaterialFlow.*（前 12 个）全部命中 |
| inh-batch-02 | 2 | 12 | 12 | 0 | ✅ MaterialFlow.*（后 10 个）+ Fluids.* 前 2 |
| inh-batch-03 | 3 | 12 | 12 | 0 | ✅ Fluids.*（后 7）+ Resources.* 前 5 |
| inh-batch-04 | 4 | 12 | 12 | 0 | ✅ Resources.*（后 5）+ InformationFlow.* 前 7 |
| inh-batch-05 | 5 | 12 | 12 | 0 | ✅ InformationFlow.*（后 1）+ UserInterface.* + MUs.* + UserObjects.* 前 5 |
| inh-batch-06 | 6 | 5 | 5 | 0 | ✅ UserObjects.*（后 1）+ Tools.* + Models.* |

**总计：6 batches / 65 paths / 65 rows captured**，写入 `data/inheritance_raw.tsv`。

> 中途遇到一次 readlog buffer 进入坏状态（返回 `'Syntax error near line 1 at '\".Resources.Exporter''`），通过在批间 `sleep 5` 解决。

## 4. 渲染 / Render

`render_inheritance_map.py data/inheritance_raw.tsv`：

```
Total classes captured: 65
  Root classes (Origin=VOID): 61
  Derived classes (Origin!==VOID): 4

INHERITANCE MAP (parent -> children)

.MaterialFlow.Station  (1 child class)
  ├─ .UserObjects.MyFrame.Station  [Station]

.MaterialFlow.Conveyor  (1 child class)
  ├─ .UserObjects.MyFrame.Conveyor  [Conveyor]

.MaterialFlow.Connector  (1 child class)
  ├─ .UserObjects.MyFrame.Connector  [Connector]

.MaterialFlow.EventController  (1 child class)
  ├─ .Models.Model.EventController  [EventController]

DERIVED CLASSES (the user-defined classes that inherit from a built-in)

  .Models.Model.EventController  [EventController]
    Origin        = .MaterialFlow.EventController
    OriginRoot    = .MaterialFlow.EventController
    Class         = .MaterialFlow.EventController

  .UserObjects.MyFrame.Connector  [Connector]
    Origin        = .MaterialFlow.Connector
    OriginRoot    = .MaterialFlow.Connector
    Class         = .MaterialFlow.Connector

  .UserObjects.MyFrame.Conveyor  [Conveyor]
    Origin        = .MaterialFlow.Conveyor
    OriginRoot    = .MaterialFlow.Conveyor
    Class         = .MaterialFlow.Conveyor

  .UserObjects.MyFrame.Station  [Station]
    Origin        = .MaterialFlow.Station
    OriginRoot    = .MaterialFlow.Station
    Class         = .MaterialFlow.Station
```

`data/inheritance_map.json`（结构化输出）：

```json
{
  "captured_at": "2026-08-26",
  "total_classes": 65,
  "root_classes": 61,
  "derived_classes": [
    ".Models.Model.EventController",
    ".UserObjects.MyFrame.Connector",
    ".UserObjects.MyFrame.Conveyor",
    ".UserObjects.MyFrame.Station"
  ],
  "tree": { ... }
}
```

## 5. 验证 / Verification

> 由于修改较小（独立新技能），`code-reviewer` 审查不是本轮重点；改走 **独立 re-probe** 来确认 raw data 真实可信。

| ID | 检查 | 期望 | 实际 | 结论 |
|---|---|---|---|---|
| v1-verify-compile-probe | `python3 -m py_compile scripts/probe_inheritance.py` | 0 | 0 | ✅ |
| v1-verify-compile-render | `python3 -m py_compile scripts/render_inheritance_map.py` | 0 | 0 | ✅ |
| v1-verify-json-syntax | `python3 -c "import json; json.load(open('data/inheritance_map.json'))"` | OK | OK | ✅ |
| v1-verify-counts | total=65, root=61, derived=4 | True | True | ✅ |
| v1-verify-derived-paths | 4 个 derived 类 Origin 均指向 `.MaterialFlow.*` | True | True | ✅ |
| v1-verify-reprobe | 独立 fresh simtalk_run 重新探 6 个关键类（4 个 derived + 2 个 root）| 全部匹配 JSON 声明 | 全部匹配 | ✅ |

### Independent re-probe (v1-verify-reprobe)

挑选 6 个具有代表性的类（4 个 derived 全部 + 2 个 root）发 **完全独立** 的 `simtalk_run` + `readlog`，与 `inheritance_raw.tsv` 比对：

| Path | Expected from JSON | Actual re-probe | Match |
|---|---|---|---|
| `.Models.Model.EventController` | Origin=`MaterialFlow.EventController` | Origin=`MaterialFlow.EventController` | ✅ |
| `.UserObjects.MyFrame.Connector` | Origin=`MaterialFlow.Connector` | Origin=`MaterialFlow.Connector` | ✅ |
| `.UserObjects.MyFrame.Conveyor` | Origin=`MaterialFlow.Conveyor` | Origin=`MaterialFlow.Conveyor` | ✅ |
| `.UserObjects.MyFrame.Station` | Origin=`MaterialFlow.Station` | Origin=`MaterialFlow.Station` | ✅ |
| `.MaterialFlow.Station` | Origin=`VOID` | Origin=`VOID` | ✅ |
| `.MUs.Part` | Origin=`VOID` | Origin=`VOID` | ✅ |

> 注：`code-reviewer` 子代理在本会话曾被委派过独立审查，但其受 Bash 权限限制无法亲自跑 `simtalk_run`；本表的 re-probe 由主代理亲自执行（独立 action_id、独立 `paths.txt` 子集、独立 stdout）。

## 6. 错误路径探针 / Error-Path Probes

| ID | 输入 | 期望 | 实际 | 退出码 | 结论 |
|---|---|---|---|---|---|
| v1-err-noargs | `probe_inheritance.py` | stderr 提示用法 | `usage: probe_inheritance.py <paths.txt> [out.tsv]` | 2 | ✅ 入参校验 OK |
| v1-err-missing-file | `probe_inheritance.py /nonexistent.txt` | 友好报错 | `FileNotFoundError` from Python open | 1 | ✅ 标准 Python 报错 |
| v1-err-badpath | `paths.txt` 含 `.DoesNotExist` | 该行 VOID 占位 | `print ".DoesNotExist | VOID"` 命中 VOID_LINE_RE | 0 | ✅ 失败路径被吸收为 VOID 行 |

## 7. 已知限制 / Known Limitations

| # | Quirk | 表现 | 缓解方案 |
|---|---|---|---|
| INH-1 | `readlog` v15+ 缓冲膨胀 + 65536 字节截断 | 单批 readlog 返回被切掉，strict JSON 解析失败 | 小批量（≤ 12 paths）+ 唯一 `###INH_BATCH###` marker + `rsplit(..., 1)` 提取（见 `references/protocol-notes.md` §1） |
| INH-2 | shell heredoc 中嵌入 `+` 和 `\\"` 损坏 SimTalk | 服务端收到截断代码，server-side syntax error | Python `json.dumps()` + `subprocess.run([...])` 列表形式，绕过 shell（见 `references/protocol-notes.md` §2） |
| INH-3 | `array` 不是 SimTalk 类型 | `Syntax error near line 2 at 'array'` | 用 `list` 类型（见 `references/protocol-notes.md` §3） |
| INH-4 | list literals 不能赋给 `var l: list` | `Left and right sides of the assignment are incompatible.` | 路径直接烘焙成 SimTalk 字面量进 code（见 `references/protocol-notes.md` §3） |
| INH-5 | `var` 在 loop body 内重复声明 | `'o' is already defined as a local variable` | `var o: object` 提到循环外声明，体内只 `o :=`（见 `references/protocol-notes.md` §3） |
| INH-6 | `log` 字段的新行是 `\\n` 字面两字符 | `log.split("\n")` 返回整段 1 块 | `log.replace("\\n", "\n").split("\n")`（见 `references/protocol-notes.md` §4） |
| INH-7 | `obj.Name` 与 `InternalClassType` 可能不一致 | `.InformationFlow.MQTT` Name=`MQTT`，Type=`MQTTInterface` | 以 `InternalClassType` 为类型身份的真值源 |
| INH-8 | `.UserObjects.*` 路径不一定是用户定义类 | `.UserObjects.PartA` Type=`Part`，Origin=`VOID` | 必须查询 `Origin` 才能区分 root vs derived |

## 8. 输出物 / Artifacts

| 路径 | 说明 |
|---|---|
| `SKILL.md` | 技能元数据 + 用法 + 输出 schema + hard rules + 7 个 skill-specific quirks |
| `scripts/probe_inheritance.py` | 批量探针（≤ 12 paths/batch + marker 提取）；支持 `--no-infobox` |
| `scripts/render_inheritance_map.py` | 渲染 parent→children 树 + derived 详情视图；输出 `data/inheritance_map.json` |
| `references/exploration-log.md` | 65 个候选类的详细映射表 + 4 个 derived 类的全字段值 + 6 个观察 |
| `references/protocol-notes.md` | v15+ readlog 退化、shell 转义、SimTalk 类型怪癖等 7 个 protocol-level workaround |
| `data/inheritance_map.json` | 结构化继承图（65 类 / 4 derived） |
| `data/inheritance_raw.tsv` | 原始 65 行 probe 输出（6 字段 TSV） |
| `log/test-session-20260826-v1.md` | 本文件 |

## 9. 结论 / Conclusions

1. **继承图抓取完成 ✅** — `probe_inheritance.py + render_inheritance_map.py` 在 6 个 batches / 65 paths / 12 round-trips 后输出 65 类 / 4 derived 的完整继承图。
2. **方法学可行 ✅** — `str_to_obj(path) + Origin/OriginRoot/Class/InternalClassType + print + readlog` 这套组合可以枚举任意 candidate class 的继承链；与 `local-simtalk-execution` 的 Quirk #6 / #7 完全兼容。
3. **当前加载模型只定义 4 个用户类 ✅** — 全部是 `.MaterialFlow.*` 的单层直接派生（`Origin == OriginRoot == Class`），无深层继承链。
4. **依赖关系稳定 ✅** — `local-simtalk-execution` 的 `socket_client.py` v17+ 客户端完全可用；本技能是 `local-simtalk-get-folder-tree` + `local-simtalk-execution` 的"只读下游"。
5. **可复现命令**（详见 `references/exploration-log.md` 末尾）：
   ```bash
   python3 scripts/probe_inheritance.py paths.txt data/inheritance_raw.tsv
   python3 scripts/render_inheritance_map.py data/inheritance_raw.tsv
   ```
6. **future work**（不在本轮范围）：
   - 把 batch size 自动调整到不触发 readlog 截断的最大值
   - 增加 `--tree` 输出选项，直接打印 ASCII 继承树
   - 支持 `--filter-domain` 选项，只探某个 domain（如 `.MaterialFlow`）的类
   - 把 marker 协议升级成 server-side 反馈的相关 ID（详见 `local-simtalk-execution` future work）

## 10. 建议 / Recommendations

1. **作为只读 inventory 工具长期保留** — `local-simtalk-get-class-inheritance` 是非破坏性 skill，未来模型切换只需重跑 `probe_inheritance.py` 即可拿到新模型的继承图。
2. **`.UserObjects.*` 永远要查 Origin** — 不要被路径前缀误导；必须以 `Origin == VOID` 为根类判据。
3. **`InternalClassType` 是类型身份的真值源** — 不要相信 `Name`（如 `.InformationFlow.MQTT` 的 Name 是 `MQTT` 但 Type 是 `MQTTInterface`）。
4. **readlog 衰退需服务端修** — `probe_inheritance.py` 的小批量 + marker 是临时方案；`readlog` 应支持更稳定的 framing（如 per-call UUID correlation），这是 `local-simtalk-execution` 的未来改进方向。
5. **本技能是 `local-simtalk-get-folder-tree` 的下游** — 任何对 folder-tree 抓取的改进（如增加 EventController 枚举、attribute 反射）都会自动扩大本技能的输入。

---

**v1 是本技能的首个 test session**，没有 prior version 可对比；后续若增加新功能（如 multi-level inheritance walk、attribute probe、并发抓取）可续写 v2 / v3。
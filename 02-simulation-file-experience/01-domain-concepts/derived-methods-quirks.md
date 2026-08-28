---
last_updated: 2026-08-28
contributors: [@z004bjuu, @plant-simulation-expert]
scope: 跨文档反复出现的字面契约 + SimTalk 2.0 易踩小坑速查（`strLen` / observer 签名 / `writeValue` 不转类型 / `infoBox` 模态陷阱等）
---

# Plant Simulation 字面契约与易踩小坑速查

> **定位**：本文是 **跨文档反复出现的"硬字面值 / 容易踩的语言小坑"** 的速查表。
> 修任何一处都会破坏远程调用或编译时正确性，所以集中放这里——改之前先 grep。
>
> 涉及 Plant Simulation 核心概念（Class / Instance / Frame / Folder）的判定规则见
> [`class-instance-frame-folder.md`](./class-instance-frame-folder.md)。
> 涉及 SimtalkClaude 软失败、readlog 截断等传输层 Quirk 见
> [`../03-workflow-playbook/skill-call-playbook.md`](../03-workflow-playbook/skill-call-playbook.md)。

---

## 一、SimTalk 字面契约（远程调用必中）

| 字面契约 | 出处 | 踩坑案例 |
|---|---|---|
| `action_result["result"]` 取值是小写 `"success"` / `"failed"` | `simtalk_hasError` 返回值契约 | 写错大小写（`"Success"`）→ 远端判断逻辑失效 |
| log 前缀 `"code execute failed. error msg:..."`（开头无空格、句点+空格） | Quirk #7 软失败检测字符串 | 改了大小写/标点 → 漏判软失败 |
| 语法失败前缀 `" hasError "`（**有前导空格**） | `simtalk_syntax` 返回值契约 | "顺手 ASCII 化"破坏远程解析 |
| `hasSyntaxError` 必须挂在 `&Method` 上 | Plant Simulation 文档 | 想对临时字符串检查 → 必须先写到 `&simtalkcode.program` |
| `chr(10)` 是 newline，SimTalk **不**解释 `\n` 转义序列 | Quirk #1 | 写字面 `\n` 当 newline → 服务端收到 `\` + `n` |
| `infoBox(text, false)` 第二参数是 `Modal` 标志 | Plant Simulation 文档 | 漏掉 `false` → 服务端挂死 |

## 二、变量 / 属性名易错

| SimTalk 写法 | 错误 | 正确 |
|---|---|---|
| 字符串长度 | `s.length` / `s.numCharacters` | `strLen(s)`（顶层函数） |
| 字符串切片 | `s.copy(...)` | `strCopy(s, pos, n)` |
| List 长度 | `l.length` | `l.dim` |
| List 构造 | `l := [1, 2, 3]` 不可赋 | 走 list-returning 函数（`getFilesOfFolder` / `makeList`） |
| Frame.NumChildren | "数 Frame 里的所有实例数" | **只数结构子节点**，**不含** 2D 视图里的 placed 实例；要查实例用 `Frame.extendPath(name) /= void` |
| 节点类型判断 | `path.NumChildren > 0` | `path.InternalClassType = "Frame"` / `"Folder"` |
| 类 vs 实例判断 | `InternalClassType` 不区分 | **`Origin == VOID AND Class == VOID` → 类；否则实例** |
| 设置实例 2D 位置 | `<obj>.setPosition := [100, 100]` → 编译错 | `<obj>.setPosition(100, 100)` → 方法调用 |
| `&` 取 ref | `&o.Encrypted`（已经是 object）→ "The ref-operator has no effect in this context" | `o.Encrypted`（已经是 object 时不加 `&`） |
| 当前方法所属对象 | `?` | `current.~` 拿父对象；`?` 拿当前对象 |
| 父对象方法 | `parent.method` | `?.~.method`（直接在方法内用） |
| Method 命名 | `method`（小写）→ "Invalid identifier"（SimTalk 保留字） | `Method`（大写，Frame 自带） |
| 实例化非 MU 对象 | `cls.create(frame)` → "Unknown identifier 'create'" | `<Class>.duplicate(frame, name)` |

## 三、模态陷阱（永久阻塞服务端）

| 禁忌写法 | 后果 | 替代 |
|---|---|---|
| `infoBox("text")`（单参 → 模态） | GUI + 服务端永久阻塞 | `infoBox("text", false)` 非模态 |
| `infoBox("text", true)` | 同上 | `infoBox("text", false)` |
| `prompt(...)` / `promptList*(...)` | 同上 | `print(...)` 写 GUI Console |
| `messageBox(...)`（Plant Simulation 旧 API） | 同上 | `infoBox(text, false)` 或 `print` |

> **收尾必须**：`infoBox("", false)` 防御性连发两次关闭。GUI 端消息框不会被 socket 关闭；
> 不主动关 → 下次跑测试时 GUI 上挂着前一轮 msgBox 让用户困惑。

## 四、Plant Simulation 私有 API 易踩字段

| 对象 | 易踩字段 | 注意事项 |
|---|---|---|
| `obj._3d` | `.dimensions` / `.position` / `.boundingboxmax` / `.boundingboxmin` / `.gap` / `.FloorThickness` / `.GroundClearance` / `.getworldcoordinate` | `_3d` 是私有 API，旧版本字段名可能不同 |
| `obj.stat*Portion` | 8 个状态：`statWorkingPortion` / `statSetupPortion` / `statWaitingPortion` / `statBlockedPortion` / `statPoweringUpDownPortion` / `statFailedPortion` / `statStoppedPortion` / `statPausedPortion` | **Fluid 对象**（NwTank/NwFluidSource/...）**没有 `statStoppedPortion` 和 `statPausedPortion`**；pipe 也无 blocking/fail/powering/pause。读前必须先 `isFluid` 判定 |
| `obj.EnergyActive` | `EnergyAnalyzer.detectEnergyobjects` 用 error handler 包装读取 | 直接读会抛错；必须用包装函数 |
| `obj.addObserver("Attr", methodRef)` | observer 回调签名**必须**是 `(valueName: string, oldValue: any)` | 签名错 → callback 静默不触发 |
| DataTable 行复制 | `tab.copyrangeto({0,row}..{*,row}, dstTab, 0, dstTab.ydim+1)` | range 用 `{col,row}` 格式；目标位置 `0` 表示追加 |
| `writeValue(attr, val)` | **不自动转类型**，字符串直接写入 | restore 时必须按 type 用 `str_to_length` / `str_to_time` / `str_to_speed` / `str_to_acceleration` / `str_to_weight` 转换 |
| WorkerPool | 不能直接 `writeValue` 修改成员 | `setCreationTable(void)` + `inheritAttribute` 才能改继承链 |

## 五、log 文件读取（独占锁陷阱）

```simtalk
-- ✅ 正确：copy → read → delete
var logFilePath := getLogFile
if copyFile(logFilePath, logFilePath + ".copy")
  result := readStringFromFile(logFilePath + ".copy")
  deletefile(logFilePath + ".copy")
else
  result := "can not read log , the log file might be use in another program"
end
```

> 不要直接 `readStringFromFile(getLogFile)` —— Plant Simulation 自己持有 log 文件的独占句柄，会失败。

## 六、变量命名约定（强烈推荐照搬）

来自 P4_CTU 模型沉淀。Plant Simulation 大小写不敏感但展示是大小写敏感——用前缀区分意图，可读性高 10 倍。

| 前缀 | 含义 | 示例 |
|---|---|---|
| `m_` | Method（私有） | `m_init`, `m_logger`, `m_findFreeAGV` |
| `m_Onxxx` | 生命周期 hook | `m_Oncreate`, `m_OnMove`, `m_OnDelete` |
| `m_xxx_triggerpoint` | 防重入触发点 | `m_TaskExcuter_triggerpoint` |
| `v_` | Variable | `v_x`, `v_y`, `bin_w`, `RCS` |
| `l_` | length 数值 | `l_groundclearance`, `l_gap` |
| `b_` | boolean | `b_needcharging`, `backhome` |
| `tab_` / `Tab_` | DataTable | `tab_taskPool`, `Tab_binState` |
| `cur*` | 局部临时 | `cur_x`, `curtime`, `curpro` |
| `obj_*` | 通用 object 引用 | `obj_type` |

> ⚠️ **真实踩坑**：模型内部常**混用大小写**（`m_Oncreate` / `m_ondelete` / `m_oncreate` 等多种写法并存）。
> 下游 agent 复用时**永远用精确路径 grep**，别靠"看上去一样的命名"匹配。

---

## 七、SimTalk 2.0 vs 1.0 语法混用

Plant Simulation 模型**允许**同一项目内 SimTalk 2.0 (`is`/`do`/`inspect`/`when`/`end;`/`then`) 与 1.0 (`if ... end` + `case`) 共存。Assembly-line 模型里只有 `WorkerChart.Open` 用了 2.0，其他都是 1.0——是 per-method 选择，不是项目级开关。

**选择建议**：
- 控制流复杂（多层嵌套 + pattern match）→ 2.0 的 `inspect`/`when` 更清晰
- 简单分支 → 1.0 的 `if`/`case` 足够，避免引入新语法认知负担

---

## 八、JSON 字段处理（SimtalkClaude 桥内部）

| 操作 | 写法 | 备注 |
|---|---|---|
| JSON 序列化（紧凑） | `jsondata.asString(false)` | 默认 `false`；用于网络传输 |
| JSON 序列化（带缩进） | `jsondata.asString(true)` | 用于调试 |
| 兼容旧 toString | `jsondata.toString` | 不推荐，兼容性差 |
| 字段读取 | `j["key"]` | 不存在返回 void |
| 字段存在判断 | `j.contains("key")` | v2 handler 入口校验用 |
| 字段删除 | （无内建方法） | 用 `j["key"] := ""` 模拟清空；或整个 `action_result` 重建 |

---

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾，**不要修改主体**。
> 贡献流程、entry 字段格式、Supersede 模式见 [`CONTRIBUTING.md`](../../CONTRIBUTING.md)。

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-001]

### 2026-08-28 by @plant-simulation-expert — `_3D.BoundingBoxSize` 是 content-dependent 的
- **症状**：同一 `Variable` 子节点，`Value` 空串时 `sz[1]=2.69`、`sz[2]=0.7`；写入 80 字符长串后 `sz[1]=23.55`、`sz[2]=0.7`（**宽度涨 8.7 倍，高度不变**）。这意味着 MLayout 之后只要 LastSummary 写入一行 report，LastSummary 立刻宽到覆盖相邻 Variable。
- **根因**：Variable icon 在 2D Frame 里按当前 `Value` 文本长度自适应渲染宽度。`_3D.BoundingBoxSize` 是 **icon 实际渲染 bbox**，不是 Variable 类型的固有尺寸。
- **Workaround / 结论**：
  1. **布局设计必须用 nominal (empty) 宽度**——不能假设 "Variable = 2×0.7"。
  2. **MLayout / probe Method 末尾必须 auto-clear 报告类 Variable**（`LastPayload` / `LastSummary` / `LastError` / `LastErrorCode`），否则下次执行完 layout 失效。
  3. 与 Quirk #1 (`chr(10)` newline) 互补——前者是写入时的内容陷阱，后者是读取时的尺寸陷阱。
- **tags**：`v15+`, `Variable`, `_3D.BoundingBoxSize`, `content-dependent`, `layout`
- **see also**：`02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` §经验 Log（json.dumps antipattern）；`skills/local-simtalk-write-simtalk/log/2026-08-28_synctoolkit-frame-relayout.md §No-overlap relayout`
- **反思**：布局前先 probe 一遍 `BoundingBoxSize`（每 Variable 空 / 每 Method / 每 Resource），拿到真实 nominal 尺寸再设计坐标——比拍脑袋"所有 Variable 宽 2"靠谱 10 倍。

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-002]

### 2026-08-28 by @plant-simulation-expert — `table[T,V]` v15+ 运行期只读 + `make_array` 不是 v15+ 内置
- **症状 1 (table)**:用 `table[string, real]` 当 `gScore` hashmap,`table.append(key, value)` 编译过、`m.Program` push 成功;但调用时返回 `Unknown identifier`。**`simtalk_hasError` 也抓不到**(运行期才触发)。
- **症状 2 (make_array)**:`var lst: list[real]; lst := make_array(...)` 编译失败——`make_array` 不在 v15+ identifier 表里。
- **根因**:Plant Simulation v15+ 编译器接受 table syntax 以保旧代码兼容,但**运行期禁止** `table.append` / `table.delete` / 类似 mutator;文档未标 deprecated。`make_array` 在 1.0 文档有,v15+ 文档已移除(只剩 `lst.create` + `lst.insert` 模式)。
- **Workaround / 结论**:
  1. 任何"动态 hashmap"需求 → **平行 `list[T]` + `list[V]` + 线性扫描模拟**;性能可接受,O(N²) 可控。
  2. 列表初始化 → **`lst.create` + `lst.insert(N, value)`**(canonical pattern,可在官方 `Small Parts Production/BottleneckAnalyzer` 模型验证)。
- **tags**:`table`, `runtime-readonly`, `make_array`, `v15+`, `hashmap-alternative`, `parallel-list`, `lst.insert`
- **see also**:团队记忆 `memory/team/simtalk-runtime-constraints.md`;`memory/team/bridge-infinite-loop-safety.md`(`while` 循环时,table + bridge 死循环耦合)
- **反思**:**写非平凡 SimTalk 算法前先 grep Quirk 列表**——本次 A* 踩了 table + chunked-write + bridge 卡死三连坑,每个都是"语法过 / 运行挂"型,缺一不可。

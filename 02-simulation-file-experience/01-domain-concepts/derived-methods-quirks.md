---
last_updated: 2026-09-01
contributors: [@z004bjuu, @plant-simulation-expert, @plant-simulation-experience-curator]
scope: 跨文档反复出现的字面契约 + SimTalk 2.0 易踩小坑速查（`strLen` / observer 签名 / `writeValue` 不转类型 / `infoBox` 模态陷阱 / Method-typed UDA / DataTable / make2DimArray / zero-param Method 等）
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

### 2026-08-31 by @plant-simulation-experience-curator — 给非 Frame/Folder 对象（Station / Drain / Source / Conveyor / ...）添加自定义 method：canonical 模式是 `createAttr(name, "Method")` + `getAttribute(name) → any`

- **症状**：尝试给 Station（或任何 `InternalClassType ≠ "Frame"` 且 `≠ "Folder"` 的对象，例如 `.UR10.UR10` 是 Station）添加一段自定义 SimTalk 时，三条直觉路径全部失败：
  1. `local-simtalk-create-method-object --frame .UR10.UR10` → `frame_invalid: path .UR10.UR10 is not a Frame (got 'Station')`
  2. `&Method.duplicate(<station>, <name>)` / `<parent_class>.duplicate(<station>, <name>)` → `duplicate_returned_void` 或 `Argument 1 is neither a Frame nor a Folder`
  3. `o.setAttrType(idx, "Method")` → `setAttrType` **不支持** `"Method"` 类型（仅支持 `boolean / integer / real / string / object / table / list / stack / queue / time / money / length / weight / speed / acceleration / date / dateTime / randtime`）。`createAttr(name, "Method")` 成功之后，`o.<methodName>` 点访问返回 `void`（不能用来读/写 `.Program`），让 agent 误以为 "createAttr 失败"。

- **根因**：Method-typed UDA **不是** child Method object —— Plant Simulation 把它当作一种特殊的"属性值"，与 Frame 下的子 Method 对象走完全不同的存储 / 访问路径。`getAttribute` 文档明确说 *"For user-defined attributes of `method` data type, `getAttribute` returns the method itself — not the result of executing it"*；调用 `.execute` 才会真正执行。要拿它的 `Program` 来读写，必须经过 `getAttribute` 而不是点访问。

- **Workaround / 结论**：

  ```simtalk
  -- canonical pattern: createAttr + getAttribute + any-typed var
  var o : object := str_to_obj(".UR10.UR10")  -- any non-Frame object works

  -- 1) create (idempotent: 检查 getAttrNo 是否已存在)
  if o.getAttrNo("myMethod") = 0
      var ok : boolean := o.createAttr("myMethod", "Method")
      -- ok = true on success; false if name is reserved or invalid identifier
  end

  -- 2) access the method (return type 是 `any`，不是 `object`！)
  var m : any
  m := o.getAttribute("myMethod")

  -- 3) write Program (用 chr(10) + chr(34) 安全拼接 multi-line + 嵌入引号)
  m.Program := "-- myMethod -- example body" + chr(10)
             + "self._3D.Poses.moveTo(" + chr(34) + "home" + chr(34) + ")"

  -- alternative 写法（更简洁，不需要 any 变量）
  o.setAttribute("myMethod.Program", "-- myMethod" + chr(10) + "print 1")

  -- 4) read back
  var m2 : any
  m2 := o.getAttribute("myMethod")
  print m2.Program                    -- reads back the source verbatim
  print m2.HasSyntaxError             -- true/false
  ```

  调用方式（client 端）保持不变：`o.myMethod()` 或 `o.myMethod.execute(...)`。

  **关键铁律**：
  - `var m : object := o.getAttribute("myMethod")` → **编译错** *"Left and right sides of the assignment are incompatible"*。必须用 `var m : any`。
  - `var m : object := o.myMethod` → 编译过但运行时 `m = void`。**不要** 用点访问拿 Method 对象。
  - SimTalk 2.0 **不允许** `var m` 不带类型；不允许 `var x;`。
  - `o.<methodName>`（无 `()`）会**执行**方法（空 method 也返回 `void`）；要拿对象引用，必须走 `getAttribute`。

- **tags**：`simtalk`, `createAttr`, `method-typed-UDA`, `getAttribute`, `any-type`, `station`, `non-frame-object`, `setAttribute-attr-path`, `chr(10)-chr(34)-safe-encoding`
- **see also**：`01-plantsimulation-knowledge/.../objects/common-methods/common-methods.md §7 createAttr + §6 getAttribute`（独立来源 #1）；`skills/local-simtalk-create-method-object/SKILL.md` Step "Choosing a target Frame"`（明确拒绝 Station，与本 entry 形成 "skill 限制 vs. 实际可行方案" 的对照）；`02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md` §经验 Log（`method-uda-on-station` 跨 skill 工作流决策表）

> 这条经验教会我：
> - **Method-typed UDA ≠ child Method object**。两者底层存储模型不同：UDA 是 "属性值 = Method 对象"，child Method 是 "Frame 子节点"。读写代码要走完全不同的路径 (`getAttribute` vs `<parent>.<name>`)，不能用同一个 mental model。
> - `getAttribute` 返回 `any` 不是 bug，是设计 —— 因为它要兼容所有 UDA 数据类型（integer / string / list / table / method ...），method 只是其中之一。声明 receiving var 时一定要 `var x: any`，不要想当然 `var x: object`。
> - `createAttr("Method")` vs `setAttrType("Method")` 的不对称容易让人栽跟头：**只有 `createAttr` 接受 "Method"**，`setAttrType` 完全不支持。两条 API 的 type-string 白名单不一样，是 Plant Simulation 历史包袱。
> - 跨 skill 工作流的盲区：`local-simtalk-create-method-object` 只覆盖 Frame-挂-Method 的场景；Station-挂-Method-typed-UDA 这个**同样合法且高频**的 case 没有 skill 包装，只能直接走 `simtalk_run` + `createAttr`。下次任何 agent 接到"给 X 加个 method"的任务，第一步必须先判断 `X.InternalClassType ∈ {"Frame","Folder"}` 还是其他 —— 走哪条路天差地别。

### 2026-09-01 by @plant-simulation-experience-curator — `make2DimArray(xDim:integer, arrayData:any[])` 第二参必须是 1D 数组,不是 `(y, x)` 双重 dim

- **症状**:
  - `make2DimArray(1, 8)` → "argument 2: array expected"(8 是 integer,不是数组)
  - `make2DimArray(y, x)`(把 y/x 当成 shape 传)→ "argument 2: array expected" 或返 `any[x, *]` 错位 shape
  - 误以为 `make2DimArray(yDim, xDim)` 第二个 dim 是 shape → 写出来的"二维数组"实际是 `any[8, *]` 而不是 `any[y, x]`,后续索引完全错位
- **根因**:`make2DimArray` 的签名是 `(xDim:integer, arrayData:any[])`——第一参是**行数 (xDim = number of rows / YDim)**,第二参是**展平的 1D 数据数组**。函数把 1D 数组 reshape 成 `[xDim, *]` 的二维表(第二维自动算 = `length(arrayData) / xDim`)。"x" 这个名字容易误导,Plant Simulation 文档里 `xDim` 实际指的是"输入 1D 数组要被切成几段",即行数。
- **Workaround / 结论**:

  ```simtalk
  -- 正确用法:3 行 × 4 列
  var flat : any[]
  flat := ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]  -- 1D, 12 elements
  var matrix : any[3, *]  -- 第 2 维自动 = 12/3 = 4
  matrix := make2DimArray(3, flat)
  -- matrix[0, 0] = "a", matrix[2, 3] = "l"
  ```

  **典型错误**:
  ```simtalk
  -- 错: 第二参传 integer
  var m : any[*, *]
  m := make2DimArray(1, 8)  -- "argument 2: array expected"

  -- 错: 第二参传 tuple/double 想表达 shape
  var m : any[*, *]
  m := make2DimArray(3, [3, 4])  -- 第二维 = 2/3 不整除 → 不可预测
  ```

  **何时** `make2DimArray` **有用 vs 直接构造**:
  - 已知 1D 数据 + 想要指定行数 → `make2DimArray(rows, flatArr)`
  - 想要 `var t : table` 的引用 → 走 DataTable(`MaxYDim` / `MaxXDim`)
  - 想要 matrix multiply / linear algebra → 走 numpy / Plant Simulation 自带 `.~.~.~.~.~.Matrix` 类

- **tags**:`make2DimArray`, `array-signature`, `1D-vs-2D`, `xDim-misleading`, `v2606.0002`, `simtalk-predefined-function`
- **see also**:`01-plantsimulation-knowledge/.../simtalk/predefined-functions-iii-…/model-debugging/model-debugging.md`(独立知识源,canonical signature);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md` §01-domain-concepts;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` Step 2

> 这条经验教会我:
> - **函数签名的语义 ≠ 函数参数名**:`make2DimArray(xDim, arrayData)` 的 `xDim` 其实是"行数 (YDim)",名字误导。**任何看到 `xDim` / `xSize` / `rows` 这种模糊命名时,先 trace 一次最小调用 + 看 KB docs 签名,再下笔**。
> - 1D vs 2D 在动态类型语言里是常见混淆源。SimTalk 没强类型 shape,只能靠名字 + 文档——意味着 agent 必须**先读 docs 再写代码**,不能像 Python 那样 `numpy.reshape` 给个 -1 让它算。
> - 与 exp-001 (DataTable resize) + exp-003 (no auto-grow) 互补:**先把 DataTable 用 `MaxYDim/MaxXDim` 扩成正确尺寸,再用 `appendRow` / `insertColumn` 写入;`make2DimArray` 用于内存里 1D→2D 转换,不用于 DataTable**。

### 2026-09-01 by @plant-simulation-experience-curator — 零-param Method 里 `var x : table; x := str_to_obj(...)` 必须前置 `param` 声明,否则 "incompatible"

- **症状**:在**没有 `param` 声明的 Method** 里写下面这段 SimTalk:
  ```simtalk
  var t : table
  t := str_to_obj(".Foo")
  t.MaxYDim := 100
  t[0, 0] := "x"
  ```
  → 编译报 `"Left and right sides of the assignment are incompatible"`(line 3 / line 2 视具体版本)。`simtalk_syntax` 校验失败,method 不进入任何 `executeSilent` / `.execute()` 路径。
- **根因**(bisect 定位到 line 3——`t := str_to_obj(...)`):
  - SimTalk v2606.0002 parser 在 method 没有 `param` 行时,对 `var x : table; x := <expr>` 做更严格的 type-check
  - 推断 `x` 类型时,似乎把"method 没有 param"视为"method 内部不允许做跨 scope type 推断"
  - 添加 `param dummy: object`(任何类型都行)→ 编译器认为 method 在 "带参数的正常调用上下文" → type-check 放宽 → 编译通过
  - **空格 / 变量名 / 路径 / 类型 / 数据类型全都无影响**,只有 "param 必须存在" 才生效(bisect 验证)
- **Workaround / 结论**:

  ```simtalk
  param dummy: object    -- ← 关键;零-param Method 必须先加 dummy param
  -> integer             -- (如果 method 返回 integer)
  var t : table
  t := str_to_obj(".Foo")
  t.MaxYDim := 100
  t[0, 0] := "x"
  return 0
  ```

  **判定**:
  - Method 已经有 `param x: type` 任何一行 → 直接写 `var t : table; t := str_to_obj(...)` → OK
  - Method 零-param → 必须先 `param dummy: object`(or any type),否则 incompatible
  - 替代:用 `executeSilent(str_to_obj(...).Program)` 调用模式(永远 fresh compile + 无 method 上下文),绕开这个 quirk

- **tags**:`simtalk`, `param-required`, `zero-param-method`, `str_to_obj`, `incompatible-type-error`, `bisect-validated`, `var-table`, `workaround-pattern`
- **see also**:`materialflow-agv/simulation-quirks.md §Quirk #10`("param x: object OK, var x: object ERR" 是相关的 var-vs-param 不对称,本条是它的扩展——"method 零-param 时 var 全部 ERR");`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings 第 1 条;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-write-and-cache.md` Finding #1(bisect 验证)

> 这条经验教会我:
> - **"无 param 的 method" 在 v2606.0002 是个特殊状态**:编译器把这类 method 当成"内部脚本"(类似 top-level code),type-check 比"带 param 的 method"更严格——这是 Plant Simulation parser 的内部设计,**任何零-param method 写复杂 type 推断都建议先加 dummy param 避免踩坑**。
> - **bisect-validated 是强 P0 信号**。本次用 `init_bisect.py` 把一个 method body 二分,定位到 line 3 = `t := str_to_obj(...)` 这一行——说明这是 100% 可复现的 quirk,不是概率性 user-error。
> - **跨 skill 工作流影响**:AGV_Claude 这种"all-in-one 初始化 Method"(无 param,内部做一堆 `str_to_obj`)是高频模式,以前所有 "7 method 写 OK" 报告里都默认走 `param pool: object` 路径,所以未踩。本次 `AGV_init` / `AGV_reset` 零-param 才发现这个 quirk。**任何 "method 内部需要 str_to_obj + var 推断" 的场景,第一动作就是加 dummy param**。

### 2026-09-01 by @plant-simulation-experience-curator — `length()` 不是 SimTalk 函数(必须 `x.length` 属性);但 `.length` 在 string 上也有版本敏感问题 → 字符串永远走 `strLen`

- **症状**:
  - `print length("hello")` → "Unknown identifier 'length'"(function call 形式不存在)
  - `print str_to_obj(".Foo").length` → 0 或 "A 'string' cannot accept the method 'Length'"(取决于 object 类型 + PS 版本)
  - `print "hello".length` → "A 'string' cannot accept the method 'Length'"(v2606.0002 已知)
- **根因**:
  1. **SimTalk 没有 `length()` 顶层函数**——`length` 在 SimTalk 词法里**只作为 attribute** 存在(`str.length` / `list.dim`),不能作为函数调用
  2. **`.length` attribute 在 string 上不是 universal**:在某些 PS build / 版本上 string 不暴露 `Length` attribute → 报类型错误
  3. **list 的长度**走 `l.dim`(不是 `.length`)——已在 `derived-methods-quirks.md §二` 沉淀过
  4. **DataTable** 的"长度"语义不明确——行数走 `tab.YDim`、列数走 `tab.XDim`,**不**是 `tab.length`
- **Workaround / 结论**:

  | 类型 | 拿长度 | 不要用 |
  |---|---|---|
  | string | `strLen(s)` | `s.length`(可能 ERR)/ `length(s)`(永远 ERR) |
  | list | `l.dim` | `l.length`(不存在)/ `length(l)`(永远 ERR) |
  | DataTable | `tab.YDim` (rows) / `tab.XDim` (cols) | `tab.length`(无意义) |
  | Object (Frame) | `obj.NumChildren` / `obj.NumAttr` | 任何 `.length`(语义不对) |

  **强约束**:**字符串永远走 `strLen(s)`**——不要相信 "string `.length` works" 的旧记忆,跨版本不稳定。

- **tags**:`length`, `strLen`, `simtalk-attribute-not-function`, `version-sensitive`, `string-vs-list-vs-table`
- **see also**:`derived-methods-quirks.md §二 变量/属性名易错`(已有 `strLen` / `l.dim` 提示,但本 entry 是 P0 强化版);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings 第 4-5 条;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-write-and-cache.md` Finding #4

> 这条经验教会我:
> - **`.length` 作为 attribute 跨版本不稳定**——v18 文档可能写 `.length`,v2606.0002 报错。**字符串长度 = `strLen` 这条铁律不动摇**;list / DataTable 用专属 attribute(`.dim` / `.YDim` / `.XDim`)。
> - **`length()` 作为函数永远不存在**——任何"试试看" 都不会编译通过,直接信"无此函数"。
> - **多源校验的胜利**:本 entry 是从 `derived-methods-quirks.md §二` 已有 "s.length is wrong, use strLen" 表格 + 09-01 新发现 "length() also wrong" + "string.length version-sensitive" 三方合成的——单独看任一 source 都不够,合并后才暴露完整的语义陷阱。

### 2026-09-01 by @plant-simulation-experience-curator — `getAttrNo(attrName)` 在本版本语义"全部返回 0",不能用它探测属性存在性(⚠️ tentative:可能是 wrong signature)

- **症状**:`o.getAttrNo("setSize")` / `o.getAttrNo("setRowNum")` / `o.getAttrNo("DummyMethod")` —— 不论存在与否,**全部 0**。
- **根因**(tentative,待复测):
  - 可能 1:Plant Simulation v2606.0002 把 `getAttrNo` 的语义从 "返回 attribute index" 改为 "返回 0 if not found, 0 if found"(永远是 default)—— buggy implementation
  - 可能 2:**签名错了**——可能是 `getAttrNo(o, name)`(把 object 作为第一参)而非 `o.getAttrNo(name)`(method call)。如果用错签名,可能 default 到返回 0 而非 throw——本次 session 自标"可能是用错了签名"
- **Workaround / 结论**:**不要用 `getAttrNo` 探测属性存在性**。直接读 attribute:
  ```simtalk
  var o : any
  o := str_to_obj(".Foo")

  -- 不要用:
  -- if o.getAttrNo("myAttr") = 0  -- 永远 = 0,无意义
  --   ...

  -- 改用:
  if o.getAttribute("myAttr") /= void
      print "exists"
  else
      print "does not exist"
  end

  -- 或探测 program 是否非空:
  if strLen(o.Program) > 0
      print "method has body"
    end
  ```

  **判定**:
  - 探测"attribute 是否存在" → `getAttribute(name) /= void`(类型安全,返 any)
  - 探测"method body 是否非空" → `strLen(o.Program) > 0`(直接读 .Program 长度)
  - 探测"attribute 当前值" → 直接 `o.<attrName>`,让 SimTalk 自己 throw(明确信号)

- **tags**:`getAttrNo`, `attribute-existence`, `tentative`, `getAttribute-vs-getAttrNo`, `v2606.0002`, `wrong-signature-suspected`
- **see also**:`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md` §02-bridge-tool 第 4 条;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` §"3 bridge 行为 findings" #3;`derived-methods-quirks.md §经验 Log entry 2026-08-31`(method-typed-UDA 用 `getAttribute` 是正解,本 entry 是对 `getAttrNo` 反例的补强)

> 这条经验教会我:
> - **`getAttribute` ≠ `getAttrNo`**:前者返 attribute value(类型=any),后者返 attribute index(integer)。语义完全不同。**探测存在性用 `getAttribute(name) /= void`**——这是 typed 模式,任何 Plant Simulation 版本都一致。
> - **本次 session 自身 sanity-check 不够**:session summary 自标 "可能是用错了签名",说明当时没有花 5 分钟 trace 正确签名——下次类似"全部返 0"的发现,**第一步就是查 KB docs 确认签名**再下定论。
> - **保留 tentative 标签**:本 entry 标 ⚠️ tentative,等下次 session 用正确签名复测一次。如果复测后 `getAttrNo(o, name)` 正确返回 index,则本 entry 改为 supersede(`o.getAttrNo(name)` 是 wrong syntax)。如果复测仍返 0,则本 entry 升 P0 永久保留。

# `.ModelAssistants` 最佳实践 — 12 条 SimTalk 模式

> 来源：`/tmp/modelassistants_sources/` 下 42 份 Siemens 原厂 method 源码（2026-08-27 抓取）
> 适用：所有「写给 agent / 写给人 / 写给未来的自己」的 SimTalk method

---

## 模式 ❶ — 防御式参数校验（每个 method 开头）

**动机**：SimTalk 缺少类型系统，参数是 `object` / `string` / `integer` 时运行期才会报错。
每个 method 的第一件事应该是**拒绝坏输入**。

**模板**（来自 `M_AddUserMenu`, `M_CallInternalMethod`, `replaceObject`, `EncryptFrame`）：
```simtalk
param o_frame:object

if o_frame = void then return; end
if o_frame.InternalClassName /= "Network" then return; end
```

**返回类型升级版**（来自 `EncryptFrame` 的 boolean 返回）：
```simtalk
param FrameObj:object, password:string, bol_encrypt:boolean := True -> boolean

if FrameObj = void then return False; end
if FrameObj.InternalClassName /= "Network" then return False; end
```

**何时升级到 boolean**：当调用方需要知道「成功 / 失败 / 跳过」时（典型场景：M_ApplyFrame
对每个对象应用失败时要 +1 skipped 计数）。Void 返回适合「单动作执行」型 method。

**反面**：❌ 不校验 → `o_frame.NumNodes` 报 "void has no attribute" → 整个 eventcontroller 挂起。

---

## 模式 ❷ — 9 字段 doc header（每个 method 顶部）

**所有 Siemens method 顶部都有这个头**，空 method 也保留：

```simtalk
------------------------------------------------------------
--| Function   : <一句话说明>
--| Parameter  : <参数 + 类型 + 默认值>
--| Return     : <返回值 + 类型>
--| Called     : <被谁调用>
--| Call       : <调用了谁，逗号分隔>
--| Date       : YYYY.MM.DD
--| Programmer : <作者 / yizhu@siemens.com>
------------------------------------------------------------
```

**真实例子**：
```simtalk
--| Function   : rebuild MSCF v2 contents directly under a target Frame
--| Parameter  : payload:string, destParent:object
--| Return     : object (destParent on success)
--| Called     : M_Paste, M_OnReceive
--| Call       : M_Split, M_Decode, M_GetMappedPath,
--|              M_ApplyObject, M_SetObjectAttribute
```

**关键纪律**：
- **必须填 Date**（哪怕是占位 `2023.02.14`）——便于追踪 method 历史。
- **Call 字段要反向交叉引用**——别人能从这里跳进 call chain；不必正向引用（grep
  能查正向）。
- **Function 字段一句话**——不要超过一行 80 char。

**Templates method 的特殊用法**（`.ModelAssistants.Templates`）：

```simtalk
------------------------------------------------------------
--| Function   :
--| Parameter  :
--| Return     :
--| Called     :
--| Call       :
--| Date       : 2023.02.14
--| Programmer :
------------------------------------------------------------
```

这是**空 method 充当 copy-paste 模板**——建模师新建 method 时把头拷过去填。

---

## 模式 ❸ — Tab ↔ List 互转（`Namer` / `QuickArrayTool`）

**动机**：GUI（Tab）显示友好但难遍历；List 字符串遍历友好但 GUI 难编辑。两者经常要互转。

**`exchangeListRow` 模板**：
```simtalk
-- list → Tab（按行 append）
for var i := 1 to listObj.Dim
    tabObj[i, 1] := listObj[i]
next
```

**`exchangeTabRow` 模板**：
```simtalk
-- Tab → list（按行 extract）
var lst: list; lst.create
for var i := 1 to tabObj.YDimIndex
    lst.append(to_str(tabObj[i, 1]))
next
```

**`copyFromTableColumn`**（来自 `AutoSorter`，整列快拷）：
```simtalk
var objArr: string[]; objArr.copyFromTableColumn(current.Objects, 1)
```

**优势**：用 `copyFromTableColumn` 一次拿到整列 string[]，比 `for + append` 快很多倍
（O(n) 内部优化 vs O(n²) 的逐次 realloc）。

---

## 模式 ❹ — `param := default` 默认值（API 友好）

```simtalk
param rootObj:object := void,
     defaultName:string := "DefaultModel",
     isWorkshop:boolean := True,
     isLayer:boolean := True,
     isLine:boolean := True
```

**好处**：调用方写 `current.AddNewModel()` 也能跑，写 `current.AddNewModel(.MyFolder)`
也行，写 `current.AddNewModel(.MyFolder, "Line1", False, True, False)` 全自定义也行。

**默认值的选型原则**：
- `object` 默认 `void`（让 method 内部 fall back 到 `Basis`）
- `boolean` 默认 `True`（除非语义上是「破坏性操作」如 `bol_encrypt` 默认 `True`）
- `string` 给一个具体业务默认值（不是空串——空串往往触发 `if x = ""` 早返回）
- `integer` / `real` 给 `0` 是合法的，但**只有当 0 = "do nothing" 时才安全**

---

## 模式 ❺ — 显式 type switch（`M_SetObjectAttribute`）

**动机**：SimTalk 的 `setAttribute` 是**重载**——string/integer/real/boolean/time/length
各自有强类型转换函数。**用 type switch 显式分发**比 `if … elseif` 链更清晰，且易扩展。

```simtalk
switch attrType
case "string"
    owner.setAttribute(attrName, value)
case "integer"
    owner.setAttribute(attrName, round(str_to_num(value)))
case "real"
    owner.setAttribute(attrName, str_to_num(value))
case "boolean"
    owner.setAttribute(attrName, strToUpper(value) = "TRUE")
case "time"
    owner.setAttribute(attrName, str_to_time(value))
case "length"
    owner.setAttribute(attrName, str_to_length(value))
case "speed"
    owner.setAttribute(attrName, str_to_speed(value))
case "weight"
    owner.setAttribute(attrName, str_to_weight(value))
case "date"
    owner.setAttribute(attrName, str_to_date(value))
case "datetime"
    owner.setAttribute(attrName, str_to_dateTime(value))
else
    return false
end
return true
```

**agent 启示**：当你要把**外部 string → SimTalk 强类型属性**时，照抄这个 switch。
不要用 `str_to_*` 系列之外的尝试（`to_str` 是反方向）。

---

## 模式 ❻ — 三态 sentinel switch（`AIBot.M_Response`）

**动机**：外部协议（LLM JSON / 远端控制）经常用「数字 code」表示状态。SimTalk 的 switch
让你能**给每个 code 命名 + 留一个 default debug 兜底**。

```simtalk
switch js_output["AutoSave"]
case 0  -- Close autosave
    rootfolder.AutoSave.Dialog.callback("OffAutoSave")
    rootfolder.AutoSave.Dialog.callback("Apply")
case 1  -- Open autosave
    rootfolder.AutoSave.Dialog.callback("OnAutoSave")
    rootfolder.AutoSave.Dialog.callback("Apply")
case -1  -- ignore
else
    debug   -- 进入 debugger，强制人工介入
end
```

**关键点**：
- **`-1` 是显式 ignore**（不是 default fallback）——LLM 经常给 `-1` 表示「无事可做」。
- **`debug` 兜底**——未知 code 不要静默吞掉，让用户进 debugger。
- **`--` 注释说明每个 case 的语义**——code 本来是 magic number，注释把它变成 API doc。

**变体**（来自 `M_TransCtrl`）：用字符串 code（`"up"` / `"down"`）做 sentinel。

---

## 模式 ❼ — `current.LastSummary` 作为 scratch variable（`M_ApplyFrame`）

**动机**：SimTalk method 不能直接传 string 给另一段代码，但可以**借用一个 Variable 当中转**。

```simtalk
-- 准备一段 SimTalk 表达式字符串
current.LastSummary := value
executeSilent(to_str(ownerPath, ".&", attrName,
    ".Program := .ModelAssistants.ModelSyncCopy.LastSummary"))
```

**原理**：`executeSilent("xxx := LastSummary")` 让服务器把 `LastSummary` Variable 的当前值
**内联进 SimTalk 程序**再执行——你不需要把 string 拼成 hot-path。

**前提**：`current.LastSummary` 必须预先存在（它是 ModelSyncCopy Frame 上的一个 Variable）。

**适用场景**：跨 method / 跨对象的 string 注入，特别是 attribute name 动态拼接时
（你不能让 attribute name 出现在 `executeSilent` 的 literal 里——它会被当成 SimTalk
identifier）。

**反面**：❌ `executeSilent(to_str(...))` 拼一长串——一旦有 quote / newline 嵌入，整个
silent program 就坏掉。

---

## 模式 ❽ — Dialog 回调触发副作用（`AutoSave`, `M_Response`）

**动机**：对话框有复杂的「Apply / Cancel / OK」按钮逻辑和内部事件链。**与其直接写
Variable，不如调 `Dialog.callback(...)`**——这样能复用对话框的所有副作用。

```simtalk
rootFolder.AutoSave.Dialog.setCheckBox("OffAutoSave", True)
rootFolder.AutoSave.Dialog.callback("Apply")
```

**另一个例子**：
```simtalk
rootfolder.AutoSave.Dialog.callback("OnAutoSave")
rootfolder.AutoSave.Dialog.callback("Apply")
```

**两段调用 vs 一段**：先 `setCheckBox(...)` 改 GUI 状态，再 `callback("Apply")` 触发
「Apply」动作。**顺序很重要**——Apply 读的是 checkbox 当前值，不是历史值。

**agent 启示**：如果你要模拟用户在对话框里点 Apply，不要写 Variable，直接走 callback。

---

## 模式 ❾ — `putIconToClipboard` + `setCurrIconFromClipboard`（图标替换）

**动机**：原厂 Frame 工具需要在每个被注入的 Frame 上画图标。**统一通过 clipboard API**
而不是直接操作 PNG 文件。

```simtalk
obj.putIconToClipboard(to_str(s_obj, "_32"))   -- 把 s_obj_32 图标放进剪贴板

var s_icon: string := to_str(current.TabUserMenu[1, i], "_32")
if not o_frame.existsIcon(s_icon)
    o_frame.createIcon(s_icon, 32, 32)            -- 32x32 图标 slot
end
o_frame.setCurrIconFromClipboard(s_icon)         -- 把剪贴板内容灌进 slot
```

**关键约束**：
- 图标命名约定：`<tool_name>_<size>`，size 常用 `32`。
- **`existsIcon` 检查再 `createIcon`**——避免「图标已存在」错误。
- **`setCurrIconFromClipboard` 不是持久的**——它把当前剪贴板内容作为「一次性画笔」
  写到 slot 上；下次再 set 时若剪贴板空了就画空。

**agent 启示**：建模 agent 给 Frame 注入 UI 工具，照这个三步走。

---

## 模式 ❿ — `while + sleep` 后台守护（`AutoSaveModel`）

```simtalk
if current.IsExecuting = True then return; end   -- 防重入

current.putIconToClipboard("On")                  -- 改图标为「运行中」
current.setCurrIconFromClipboard("ClassLibrary")
current.IsExecuting := True

while current.IsContiuned                          -- IsContiuned 是 typo "Continued"
    if not current.MSaveModel(...) then exitloop; end
    sleep(current.SavePeriod, False)               -- 非阻塞 sleep
end

current.putIconToClipboard("Off")                  -- 改图标为「停止」
current.setCurrIconFromClipboard("ClassLibrary")
current.IsExecuting := False
```

**细节**：
- **`sleep(sec, True)` 是同步**——会卡 eventcontroller，**永远不要用**。
- **`IsExecuting` flag 防重入**——`autoexec` 跑过一次后用户再触发，不会启动第二个 loop。
- **退出图标重置**——后台守护停的时候要把图标改回去，否则 UI 永远显示「On」。
- **`IsContiuned` 是原厂 typo**（应是 `IsContinued`）——沿用别改，改了反而找不到变量。

---

## 模式 ⓫ — `isComputerAccessPermitted` 守门（`MSaveModel`）

```simtalk
if not isComputerAccessPermitted
    promptMessage("Please activate access to computer! Cancel checkbox " +
                  "File> Model Setting> Prohibit access to the computer")
    return False
end
```

**动机**：SimTalk 的 `saveModel` / `os.files.*` / `os.execute` 等系统调用需要用户在
「File > Model Setting > Prohibit access to the computer」里放权。**任何写盘 / 启进程
的 method 都要先守这一道门**。

**注意**：
- 这里用的是 `promptMessage`（非阻塞消息）——别用 `prompt` / `infoBox(msg, true)`（模态
  陷阱，会挂死 GUI）。
- 错误信息要**告诉用户怎么修**，不只是报「拒绝」。

---

## 模式 ⓬ — 防御性编码（`MSaveModel` 的 auto-save 命名）

```simtalk
var fn: string := modelfile
var i := pos(".spp", fn)
if i = -1
    return False
else
    fn := incl("-AutoSave", fn, i)         -- 在 .spp 前插入
end
return saveModel(fn, StopMethodExecution, UseNewName)
```

**`incl(prefix, str, pos)`** 是 SimTalk 的就地插入函数（insert at position），比字符串
拼接再赋值快且易读。

**双重保护**：
- `pos(".spp", fn) = -1` → 文件名不含 `.spp`（异常情况），直接 return。
- `UseNewName` flag → 不改名直接覆写原文件 vs 改名 `-AutoSave.spp`（防用户数据丢失）。

---

## 综合：一个 method 的「Siemens 风格」完整示例

把以上 12 个模式叠在一起：

```simtalk
------------------------------------------------------------
--| Function   : apply one MSCF attribute (program body)
--| Parameter  : owner:object, attrName:string, body:string
--| Return     : boolean
--| Called     : M_ApplyFrame
--| Call       : <none>
--| Date       : 2026.07.20
--| Programmer : ModelSyncCopy
------------------------------------------------------------
param owner:object, attrName:string, body:string -> boolean

-- ❶ 防御式校验
if owner = void then return false end
if not owner.hasAttribute(attrName)
    owner.createAttr(attrName, "method")
end

-- ❺/❼ 通过 scratch variable 注入
current.LastSummary := body
executeSilent(to_str(owner, ".&", attrName,
    ".Program := .ModelAssistants.ModelSyncCopy.LastSummary"))

return true
```

读起来：doc header 一目了然 / 参数校验 3 行 / 业务逻辑 1 行 / 返回值 1 行。这就是 Siemens
的 method 美学。
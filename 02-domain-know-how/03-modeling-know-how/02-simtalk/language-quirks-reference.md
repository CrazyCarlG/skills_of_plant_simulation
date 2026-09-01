---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: SimTalk 语言层的字面契约与易踩小坑速查(strLen / observer 签名 / writeValue / infoBox 模态 / Method-typed UDA / DataTable / make2DimArray / zero-param Method)
---

# SimTalk 语言层字面契约与易踩小坑

写 SimTalk 代码时**必查**的速查表——跨文档反复出现的"硬字面值 / 容易踩的语言小坑",改任何一处都可能破坏远程调用或编译时正确性。

## 一、SimTalk 字面契约(远程调用必中)

| 字面契约 | 出处 | 踩坑案例 |
|---|---|---|
| `action_result["result"]` 取值是小写 `"success"` / `"failed"` | `simtalk_hasError` 返回值契约 | 写错大小写(`"Success"`)→ 远端判断逻辑失效 |
| log 前缀 `"code execute failed. error msg:..."`(开头无空格、句点+空格) | Quirk #7 软失败检测字符串 | 改了大小写/标点 → 漏判软失败 |
| 语法失败前缀 `" hasError "`(**有前导空格**) | `simtalk_syntax` 返回值契约 | "顺手 ASCII 化"破坏远程解析 |
| `hasSyntaxError` 必须挂在 `&Method` 上 | Plant Simulation 文档 | 想对临时字符串检查 → 必须先写到 `&simtalkcode.program` |
| `chr(10)` 是 newline,SimTalk **不**解释 `\n` 转义序列 | Quirk #1 | 写字面 `\n` 当 newline → 服务端收到 `\` + `n` |
| `infoBox(text, false)` 第二参数是 `Modal` 标志 | Plant Simulation 文档 | 漏掉 `false` → 服务端挂死 |

## 二、变量 / 属性名易错

| SimTalk 写法 | 错误 | 正确 |
|---|---|---|
| 字符串长度 | `s.length` / `s.numCharacters` | `strLen(s)`(顶层函数) |
| 字符串切片 | `s.copy(...)` | `strCopy(s, pos, n)` |
| List 长度 | `l.length` | `l.dim` |
| List 构造 | `l := [1, 2, 3]` 不可赋 | 走 list-returning 函数(`getFilesOfFolder` / `makeList`) |
| Frame.NumChildren | "数 Frame 里的所有实例数" | **只数结构子节点**,**不含** 2D 视图里的 placed 实例;要查实例用 `Frame.extendPath(name) /= void` |
| 节点类型判断 | `path.NumChildren > 0` | `path.InternalClassType = "Frame"` / `"Folder"` |
| 类 vs 实例判断 | `InternalClassType` 不区分 | **`Origin == VOID AND Class == VOID` → 类;否则实例** |
| 设置实例 2D 位置 | `<obj>.setPosition := [100, 100]` → 编译错 | `<obj>.setPosition(100, 100)` → 方法调用 |
| `&` 取 ref | `&o.Encrypted`(已经是 object)→ "The ref-operator has no effect in this context" | `o.Encrypted`(已经是 object 时不加 `&`) |
| 当前方法所属对象 | `?` | `current.~` 拿父对象;`?` 拿当前对象 |
| 父对象方法 | `parent.method` | `?.~.method`(直接在方法内用) |
| Method 命名 | `method`(小写)→ "Invalid identifier"(SimTalk 保留字) | `Method`(大写,Frame 自带) |
| 实例化非 MU 对象 | `cls.create(frame)` → "Unknown identifier 'create'" | `<Class>.duplicate(frame, name)` |

## 三、模态陷阱(永久阻塞服务端)

| 禁忌写法 | 后果 | 替代 |
|---|---|---|
| `infoBox("text")`(单参 → 模态) | GUI + 服务端永久阻塞 | `infoBox("text", false)` 非模态 |
| `infoBox("text", true)` | 同上 | `infoBox("text", false)` |
| `prompt(...)` / `promptList*(...)` | 同上 | `print(...)` 写 GUI Console |
| `messageBox(...)`(Plant Simulation 旧 API) | 同上 | `infoBox(text, false)` 或 `print` |

> **收尾必须**:`infoBox("", false)` 防御性连发两次关闭。GUI 端消息框不会被 socket 关闭;不主动关 → 下次跑测试时 GUI 上挂着前一轮 msgBox 让用户困惑。

## 四、Plant Simulation 私有 API 易踩字段

| 对象 | 易踩字段 | 注意事项 |
|---|---|---|
| `obj._3d` | `.dimensions` / `.position` / `.boundingboxmax` / `.boundingboxmin` / `.gap` / `.FloorThickness` / `.GroundClearance` / `.getworldcoordinate` | `_3d` 是私有 API,旧版本字段名可能不同 |
| `obj.stat*Portion` | 8 个状态:`statWorkingPortion` / `statSetupPortion` / `statWaitingPortion` / `statBlockedPortion` / `statPoweringUpDownPortion` / `statFailedPortion` / `statStoppedPortion` / `statPausedPortion` | **Fluid 对象**(NwTank/NwFluidSource/...)**没有 `statStoppedPortion` 和 `statPausedPortion`**;pipe 也无 blocking/fail/powering/pause。读前必须先 `isFluid` 判定 |
| `obj.EnergyActive` | `EnergyAnalyzer.detectEnergyobjects` 用 error handler 包装读取 | 直接读会抛错;必须用包装函数 |
| `obj.addObserver("Attr", methodRef)` | observer 回调签名**必须**是 `(valueName: string, oldValue: any)` | 签名错 → callback 静默不触发 |
| DataTable 行复制 | `tab.copyrangeto({0,row}..{*,row}, dstTab, 0, dstTab.ydim+1)` | range 用 `{col,row}` 格式;目标位置 `0` 表示追加 |
| `writeValue(attr, val)` | **不自动转类型**,字符串直接写入 | restore 时必须按 type 用 `str_to_length` / `str_to_time` / `str_to_speed` / `str_to_acceleration` / `str_to_weight` 转换 |
| WorkerPool | 不能直接 `writeValue` 修改成员 | `setCreationTable(void)` + `inheritAttribute` 才能改继承链 |

## 五、log 文件读取(独占锁陷阱)

```simtalk
-- ✅ 正确:copy → read → delete
var logFilePath := getLogFile
if copyFile(logFilePath, logFilePath + ".copy")
  result := readStringFromFile(logFilePath + ".copy")
  deletefile(logFilePath + ".copy")
else
  result := "can not read log , the log file might be use in another program"
end
```

> 不要直接 `readStringFromFile(getLogFile)` —— Plant Simulation 自己持有 log 文件的独占句柄,会失败。

## 六、变量命名约定(P4_CTU 沉淀,强烈推荐照搬)

| 前缀 | 含义 | 示例 |
|---|---|---|
| `m_` | Method(私有) | `m_init`, `m_logger`, `m_findFreeAGV` |
| `m_Onxxx` | 生命周期 hook | `m_Oncreate`, `m_OnMove`, `m_OnDelete` |
| `m_xxx_triggerpoint` | 防重入触发点 | `m_TaskExcuter_triggerpoint` |
| `v_` | Variable | `v_x`, `v_y`, `bin_w`, `RCS` |
| `l_` | length 数值 | `l_groundclearance`, `l_gap` |
| `b_` | boolean | `b_needcharging`, `backhome` |
| `tab_` / `Tab_` | DataTable | `tab_taskPool`, `Tab_binState` |
| `cur*` | 局部临时 | `cur_x`, `curtime`, `curpro` |
| `obj_*` | 通用 object 引用 | `obj_type` |

> ⚠️ **真实踩坑**:模型内部常**混用大小写**(`m_Oncreate` / `m_ondelete` / `m_oncreate` 等多种写法并存)。下游 agent 复用时**永远用精确路径 grep**,别靠"看上去一样的命名"匹配。

## 七、SimTalk 2.0 vs 1.0 语法混用

Plant Simulation 模型**允许**同一项目内 SimTalk 2.0 (`is`/`do`/`inspect`/`when`/`end;`/`then`) 与 1.0 (`if ... end` + `case`) 共存。Assembly-line 模型里只有 `WorkerChart.Open` 用了 2.0,其他都是 1.0——是 per-method 选择,不是项目级开关。

**选择建议**:

- 控制流复杂(多层嵌套 + pattern match)→ 2.0 的 `inspect`/`when` 更清晰
- 简单分支 → 1.0 的 `if`/`case` 足够,避免引入新语法认知负担

## 八、DataTable 运行时操作速查

| 操作 | 正确 API(v2606.0002) | 已废弃 |
|---|---|---|
| 运行时 resize | `t.MaxYDim := Y; t.MaxXDim := X`(assignable) | `setSize(y, x)` / `setRowNum` / `setColNum` / `setNoOfRows` |
| 写入前必须 | 先 resize **或** 用 `appendRow` / `insertColumn` / `insertRow` | 不能依赖 auto-grow |
| 数组创建 | `lst.create` + `lst.insert(N, value)` | `make_array`(v15+ 已移除) |
| `make2DimArray` 签名 | `make2DimArray(xDim:integer, arrayData:any[])` — 第二参必须 **1D 数组**(不是 dims) | `make2DimArray(y, x)` 双 dim |

## 九、JSON 字段处理(SimtalkClaude 桥内部)

| 操作 | 写法 | 备注 |
|---|---|---|
| JSON 序列化(紧凑) | `jsondata.asString(false)` | 默认 `false`;用于网络传输 |
| JSON 序列化(带缩进) | `jsondata.asString(true)` | 用于调试 |
| 兼容旧 toString | `jsondata.toString` | 不推荐,兼容性差 |
| 字段读取 | `j["key"]` | 不存在返回 void |
| 字段存在判断 | `j.contains("key")` | v2 handler 入口校验用 |
| 字段删除 | (无内建方法) | 用 `j["key"] := ""` 模拟清空;或整个 `action_result` 重建 |

## 十、Method-typed UDA(非 Frame 对象加 method 的 canonical 模式)

```simtalk
-- canonical pattern: createAttr + getAttribute + any-typed var
var o : object := str_to_obj(".UR10.UR10")  -- any non-Frame object works

-- 1) create (idempotent: 检查 getAttrNo 是否已存在)
if o.getAttrNo("myMethod") = 0
    var ok : boolean := o.createAttr("myMethod", "Method")
end

-- 2) access the method (return type 是 `any`,不是 `object`!)
var m : any
m := o.getAttribute("myMethod")

-- 3) write Program (用 chr(10) + chr(34) 安全拼接 multi-line + 嵌入引号)
m.Program := "-- myMethod -- example body" + chr(10)
           + "self._3D.Poses.moveTo(" + chr(34) + "home" + chr(34) + ")"
```

**关键铁律**:

- `var m : object := o.getAttribute("myMethod")` → **编译错** *"Left and right sides of the assignment are incompatible"*
- 必须用 `var m : any`
- `createAttr("Method")` vs `setAttrType("Method")` 的不对称:**只有 `createAttr` 接受 "Method"**,`setAttrType` 完全不支持

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->
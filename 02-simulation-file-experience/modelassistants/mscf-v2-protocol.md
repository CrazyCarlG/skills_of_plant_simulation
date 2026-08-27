# MSCF v2 协议 — `ModelSyncCopy` 私有格式规范

> 来源：`/tmp/modelassistants_sources/ModelAssistants_ModelSyncCopy_M_ApplyFrame.simtalk`
> + 同目录其他 16 个 method。
> 性质：Siemens 原厂私有协议，**不是公开 API**，但 agent 有可能与之交互。

## 1. 协议概述

MSCF（**M**odel **S**ync **C**opy **F**ormat）v2 是 `.ModelAssistants.ModelSyncCopy`
Frame 用于**跨模型 / 跨节点**复制整棵 Frame 子树时使用的文本序列化格式。

| 特性 | 取值 |
|---|---|
| 帧定界符 | `RS = chr(1)`（record separator） |
| 字段定界符 | `FS = chr(2)`（field separator） |
| 字符集 | UTF-8，但所有「分隔符」必须先做 `M_Encode` 转义 |
| 编码 | base64-ish escape（见 §6） |
| 版本字段 | header 第 2 字段固定为 `"v2"` |
| 记录类型 | `F`, `S`, `O`, `U`, `A`, `P`, `G`, `W`, `C`（共 9 类） |

**Header**（每条 payload 的第一行）：
```
MSCF<FS>v2<FS><sourceModelPath><FS><sourceVersion>
```

完整 payload 结构：
```
MSCF<FS>v2<FS><source><FS><sourceVer><RS><rec1><RS><rec2>...<RS><recN>
```

## 2. 9 种 record 类型

| Type | 字段 | 含义 | 处理 pass |
|---|---|---|---|
| `F` | `parentRel<FS>sourceRel<FS>classScope<FS>classRef<FS>objName<FS>x<FS>y<FS>z` | 嵌套 Frame | 1 |
| `S` | `parentRel<FS>sourceRel<FS>objName<FS>infoFlowClassRef` | InformationFlow 节点 | 2 |
| `O` | `parentRel<FS>sourceRel<FS>classScope<FS>classRef<FS>objName<FS>x<FS>y<FS>z` | 通用类实例 | 2 |
| `U` | (no fields) | **未支持类型占位**（pass 2 直接 skipped += 1） | 2 |
| `A` | `sourceRel<FS>attrName<FS>value` | 用户自定义 method attribute | 3 |
| `P` | `sourceRel<FS>attrName<FS>attrType<FS>isUser<FS>value` | scalar attribute（string/int/real/boolean/length/...） | 3 |
| `G` | `sourceRel<FS>attrName<FS>value` | object reference（隐式 by path） | 4 |
| `W` | `sourceRel<FS>attrName<FS>attrType<FS>isUser<FS>refScope<FS>targetRel` | 控制 reference（with scope） | 4 |
| `C` | `sourceRel<FS>targetRel` | MaterialFlow 连接 | 5 |

**`classScope` 取值**：
- `R` = relative（相对路径，要查 pathMap 解析）
- (其他) = absolute path（直接 `str_to_obj`）

**`refScope` 取值**（`W` record 用）：
- `S` = by path string（用 `executeSilent` 赋值）
- `R` = relative（查 pathMap）
- (其他) = absolute path（直接 `str_to_obj`）

**`isUser` 取值**：
- `"1"` = 用户自定义属性（需要先 `createAttr`）
- `"0"` = 内置属性（直接 `setAttribute`）

## 3. pathMap — sourceRel → destPath 的运行时映射

**核心数据结构**（pass 1 创建，pass 2-5 共用）：
```simtalk
pathMap := .InformationFlow.DataTable.derive(current, "FrameApplyMap")
pathMap.DataType := "string"
pathMap.setDataType(1, "string")  -- col 1: sourceRel
pathMap.setDataType(2, "string")  -- col 2: destPath
pathMap.appendRow("", to_str(destParent))  -- root 映射
```

**关键函数**：
```simtalk
current.M_GetMappedPath(pathMap, sourceRel)
→ string  -- "" if not found
```

`sourceRel` 是源模型里的相对路径（以 `Models.<ModelName>.` 开头），`destPath` 是目标
模型里被映射的绝对路径。

**用途**：每次 apply 一个新对象，把 `(sourceRel, destPath)` 追加到 pathMap；后续
record 的 `parentRel` 通过 pathMap 反查得到目标 parent。

## 4. 5-pass scan（`M_ApplyFrame` 主流程）

### Pass 1 — Frame 子树（嵌套）
- 遍历所有 `F` record
- `classObj.derive(parentObj, objName)` 创建新 Frame
- `newObj.Coordinate3D := [x, y, z]` 恢复 3D 坐标
- 立即 `pathMap.appendRow(sourceRel, to_str(newObj))`

### Pass 2 — 节点对象（S/O/U）
- `S` = information flow 节点，用 `M_ApplyObject(classRef, parentObj)` 特殊创建
- `O` = 通用类实例，同 Pass 1 的 `classObj.derive(...)`
- `U` = 未支持类型，**仅 `skipped += 1`，不报错**（用于前向兼容）

### Pass 3 — 属性赋值（A/P）
- `A` = method attribute，**用 `executeSilent` 注入 Program**
- `P` = scalar attribute，调 `M_SetObjectAttribute` 走 ❺ type switch

### Pass 4 — 引用（G/W）
- **关键时序**：pass 4 必须在 pass 2 之后——所有被引用的对象必须已经存在
- `G`（隐式 by path）→ `executeSilent(... := LastSummary)`
- `W`（带 scope）：
  - `refScope = "S"` → path string 模式
  - `refScope = "R"` → 查 pathMap
  - 否则 → absolute path

### Pass 5 — MaterialFlow 连接（C）
```simtalk
alreadyConnected := false
for succNo := 1 to sourceObj.NumSucc
    if sourceObj.succ(succNo) = targetObj
        alreadyConnected := true
        exitLoop
    end
next
if not alreadyConnected
    .MaterialFlow.Connector.connect(sourceObj, targetObj)
    connectors += 1
end
```

**幂等性保证**：检查 `NumSucc` 避免重复连接。

## 5. OnCollision 三策略

`current.OnCollision` 是 ModelSyncCopy Frame 上的一个 Variable，调用方在 `M_Paste` 前可设：

| 值 | 行为 |
|---|---|
| `"skip"` | 保留目标已存在对象，**不覆盖**，仅加 `pathMap` 映射；计数 `skipped += 1` |
| `"rename"` | 追加 `_N` 后缀（`_1`, `_2`, …, `_999` 上限），强制唯一 |
| (default / 其他) | **`deleteObject` 后重建**——破坏性最大 |

**默认行为**是 `deleteObject`——意味着 agent 若不显式设 OnCollision 就 `M_Paste`，
目标子树会被**无声地覆盖**。这是 MSCF v2 的**最大隐患**。

**agent 启示**：
- 调用 `M_Paste` 前务必 `current.OnCollision := "rename"`（最安全）或 `"skip"`。
- 永远不要用默认覆盖模式，除非明确知道目标子树可丢弃。

## 6. M_Encode / M_Decode — 字符串转义

由于 payload 用 `chr(1)` / `chr(2)` 作分隔符，**任何用户字段里出现这两个字符都会破坏
解析**。`M_Encode` 把它们替换为占位符；`M_Decode` 还原。

（具体替换表未在已读源码中暴露，但每个 record 的字段都用 `current.M_Decode(f[i])`
读取，意味着 caller 也必须用 `M_Encode` 写入。）

## 7. 摘要格式（`M_ApplyFrame` 返回）

```simtalk
current.LastSummary := to_str(
    "type=FrameContents source=", current.M_Decode(h[4]),
    " frames=", frames,
    " objects=", created,
    " attrs=", attributes,
    " refs=", references,
    " connectors=", connectors,
    " skipped=", skipped,
    " missing=", missing,
    " sourceVersion=", h[3])
```

**agent 怎么读摘要**：M_ApplyFrame 走完后调用 `print current.LastSummary`，
得到一行 key=value 串，agent 可解析它判断成败（`missing > 0` 即失败）。

## 8. MSCF v2 vs SimtalkClaude 协议

| 维度 | MSCF v2（ModelSyncCopy） | SimtalkClaude（v2） |
|---|---|---|
| 用途 | 整棵子树 copy | 远程方法调用 + 鉴权 |
| 传输 | 文本（可粘贴到 clipboard） | TCP JSON-line |
| 分隔符 | chr(1) / chr(2) | `\n` |
| 鉴权 | 无 | token + ts + sig（v2 新增） |
| 错误恢复 | OnCollision 三策略 | 错误包 result="error" |
| 适用范围 | Siemens 原厂内置 | 用户导入 |

**两者协议层完全不兼容**——MSCF v2 是「建模工具的传输层」；SimtalkClaude 是「agent 的
RPC 层」。**代理不能直接用 SimtalkClaude 驱动 ModelSyncCopy**。

## 9. agent 使用 MSCF v2 的边界

- ✅ 可以**读取** MSCF payload（如 clipboard / 文件），用 `M_Split + M_Decode` 反序列化
- ✅ 可以**写** MSCF payload（用 `M_Encode` 转义字段）
- ❌ **不应该**调用 `M_Paste` 写入用户模型，除非用户明确授权
- ❌ **不应该**覆盖 ModelSyncCopy 现有 OnCollision 策略（用户可能依赖默认行为）

**触发条件**：如果你看到 `M_ApplyFrame` 或 `current.OnCollision` 这种代码，**停下来问
用户**——这是破坏性操作，不是只读探查。
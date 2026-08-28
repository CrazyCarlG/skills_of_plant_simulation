# SimTalk 2.0 — Quick Reference for Writing Methods

> 这一页是 `local-simtalk-write-simtalk` 写代码时的速查。完整 SimTalk 文档见
> `01-plantsimulation-knowledge/01-plant-simulation-help/objects/simtalk/`
> 与 `programming-a-method/`。

## 注释

```simtalk
// 单行注释（C++ 风格）   — 到行尾结束
-- 单行注释（SQL 风格）   — 到行尾结束
/* 块注释（C 风格）        — 可跨行
   任何字符都被忽略 */
```

**Quirk #11 警告**：装饰行（`=====` / `-----` / `*****`）必须 `--` / `//` 开头，
否则 SimTalk lexer 会先把 `==` tokenize 成等号运算符：

```simtalk
// ❌ WRONG — 触发 Syntax error near line 1 at '=='.
============================================
-- Purpose: count parts

// ✅ RIGHT — 用 -- 前缀
--------------------------------------------
-- Purpose: count parts

// ✅ ALSO RIGHT — 整段塞在 /* */ 里
/*
============================================
-- Purpose: count parts
============================================
*/
```

## 字符串

SimTalk 字面量**不**解释转义序列：

```simtalk
// ❌ WRONG — "\n" 是两个字面字符 \ 和 n
var s := "line1" + "\n" + "line2"  // s == "line1\nline2"（带反斜杠）

// ✅ RIGHT — 用 chr(10) 表真换行
var s := "line1" + chr(10) + "line2"  // s == "line1\nline2"（真换行）
```

写代码到 `program` 时（`obj.program := <source>`），source 字符串内部也要
`chr(10)` join。`local-simtalk-add-note-to-method/scripts/add_note.py` 已经
处理这个细节。

### Python → SimTalk 双层嵌套引号转义（`chr(34)` 模式）

当 Python 字符串里需要嵌入一段 SimTalk，而 SimTalk 内部又要包含
双引号字符串字面量（如 `print "hello from..."`），三层引号会撞车：

```python
# 三层引号失败
code = "print \"hello\""       # Python 解析为: print "hello"
                                # 看起来对，但 SimTalk 端没问题
                                # 问题在更复杂的场景

# 真正的陷阱：Python 内嵌 SimTalk 字符串，SimTalk 内嵌 "..."
code = '"hello from \"world\""' # ❌ Python OK，但传给 SimTalk 后变成
                                # "hello from \"world\"" —— SimTalk 不解释 \"
                                # 服务端拿到的是字面 \" 两字符，print 输出
                                # 包含反斜杠的怪字符串

# ❌ 失败的尝试
code = '"hello from \"world\""'  # SimTalk 端看到的不是 " 而是 \"
                                # print 输出: hello from \"world\"
                                # 这不是想要的
```

**为什么 SimTalk 不解释 `\"`**：SimTalk 字符串字面量**不支持**反斜杠转义。
任何 `\` 在 SimTalk 里都是字面字符。要在 SimTalk 字符串里放 `"`，必须用
SimTalk 自己的**双引号 doubling**规则（`""` → `"`）：

```simtalk
-- ✅ SimTalk 双引号 doubling
print "hello ""world"""          -- 输出: hello "world"
print "say ""hi"" please"        -- 输出: say "hi" please
```

或者用 `chr(34)` 拼接：

```simtalk
-- ✅ chr(34) = ASCII 34 = "
print "hello " + chr(34) + "world" + chr(34)
-- 输出: hello "world"
```

**Python 端的安全模式**（避免引号嵌套地狱）：用 `chr(34)` 在 Python 里
组装 SimTalk 字符串，绝不依赖 Python `\"` 转义穿透到 SimTalk：

```python
# ✅ 推荐 — Python 用 chr(34) 在 SimTalk 字符串里放引号
code = 'print "hello from " + chr(34) + "world" + chr(34)'

# ✅ 也推荐 — Python 把整个 SimTalk 字符串用 chr(34) 拼接
DQ = chr(34)
code = f'print {DQ}hello from "world"{DQ}'
# SimTalk 端看到: print "hello from "world""
# SimTalk 解析: 字符串 "hello from "（含 closing "）, 然后
#               裸标识符 world，然后字符串 "" (空字符串)，然后 "world"
# 等下这解析不对 —— doubling 才能保证安全
```

**最稳的写法**（不依赖 doubling 的解析细节）：

```python
# Python 端用 chr(34) 在 SimTalk 里放 ASCII 34
def quote_simtalk(s):
    """在 SimTalk 字符串字面量里放 ASCII "（chr(34)）。"""
    return chr(34) + s + chr(34)

code = f'print {quote_simtalk("hello from \"world\"")}'
# SimTalk 端看到: print chr(34) + "hello from \"world\"" + chr(34)
# SimTalk 解析: print 是一个表达式，左侧 chr(34) + "..." + chr(34) 是
#   字符串拼接。等下 —— 这要在 print 的实参位置才合法。
# 简化为: code = 'print chr(34) + "hello from "world" + chr(34)'
# 不对，字面量里不能有 " 除非 doubling 或 chr(34)
```

**实操结论**：Python 写 SimTalk 源时，**任何需要 `"` 的地方**用以下两选一：

1. **SimTalk doubling**：`""text""`（在 SimTalk 源码里直接写）
2. **`chr(34)` 拼接**：用 `+ chr(34) +` 在运行时构造 `"` 字符

避免：Python 的 `\"` 转义（不会穿透到 SimTalk），任何形式的
`escape_sequence` 在 SimTalk 字符串字面量里都不工作。

**来源**：`log/2026-08-27_flow-a-replace-and-flow-b-duplicate.md` §"What this run validated / learned" lines 198-208（Test 2 step 5 first attempt 失败）。

## Method 引用运算符 `&`

```simtalk
myMethod                  // ❌ 触发执行（运行源代码）
root.Frame2.myMethod      // ❌ 同样触发执行
&myMethod                 // ✅ 拿到 Method 对象本身
&myMethod.execute         // ✅ 显式调用
&myMethod.program         // ✅ 读源代码
&myMethod.program := "..."// ✅ 写源代码
```

**为什么 `&` 重要**：访问 Method 对象自身的属性 / 方法（如 `program` /
`execute` / `hasSyntaxError`），必须用 `&`；裸引用会触发源代码执行。

## Method 程序结构

```simtalk
// 1. 参数（可选）
param Sender: object
param Num: integer := 10

// 2. 返回类型（可选）— 必须第一行或紧接参数
->string

// 3. 局部变量（可选）
var i: integer := 0
var s: string

// 4. 源代码
i := Num + 1
if i > 100
    print "too many"
    return
end
s := to_str(i)
return s
```

## 常用内置

| 类别 | 名称 | 用途 |
|---|---|---|
| I/O | `print "..."` | 输出到 GUI Console（v15+ readlog 不可靠） |
| 类型转换 | `to_str(x)` / `to_num(s)` / `to_int(s)` | 任意→string / string→real / string→integer |
| 列表 | `.length` / `.first` / `.last` / `.append(x)` / `.delete` | list / DataList 操作 |
| 表格 | `[row, col]` / `.[row, col] := x` / `.`（删除） | DataTable 单元格操作 |
| 字符串 | `chr(10)` / `chr(13)` / `length(s)` / `copy(s, i, n)` | ASCII / 字符串操作 |
| 对象 | `str_to_obj(path)` / `obj_to_str(o)` | 路径 ↔ 对象互转 |
| 数学 | `abs(x)` / `round(x)` / `floor(x)` / `ceil(x)` / `sqrt(x)` / `pow(x, y)` / `min(a, b)` / `max(a, b)` | |
| 时间 | `eventController.simTime` | 当前仿真时间（real） |
| 文件 | `fileExists(path)` / `deleteFile(path)` | 文件操作 |

## 流程控制

```simtalk
if cond
    // ...
elseif other
    // ...
else
    // ...
end

while cond
    // ...
end

for var i := 1 to 10
    print i
next
```

## 创建 Method 实例

```simtalk
// ⚠️  create() 不能用来创建 Method — 它是 SimTalk 关键字 + List 方法
// 三种"看起来合理"的写法都失败：
//   var p: object := str_to_obj(".InformationFlow.Method");
//   p.create(f, "myMethod");                  -- ❌ Unknown identifier 'create'
//   .InformationFlow.Method.create(f, "x");   -- ❌ can only be applied to lists
//   .InformationFlow.&Method.create(f, "x");  -- ❌ 仍然失败，create 是保留字

// ✅ 正确 — 用 duplicate() + & 引用操作符
var f: object := str_to_obj(".Models.Model");
.InformationFlow.&Method.duplicate(f, "myMethod");

// 自定义父类同样 — & 加在路径最后一段前
var f2: object := str_to_obj(".Models.Model");
.UserObjects.&LoggingMethod.duplicate(f2, "log_warn");

// 验证：duplicate 后路径必须可解析
var obj: object := str_to_obj(".Models.Model.myMethod");
print to_str(obj.internalclasstype);   -- 期望 "Method"
```

**关键细节**：
1. `&` 加在路径**最后一段**前（如 `.InformationFlow.&Method.duplicate(...)`），告诉 SimTalk 把名字当 class object 而不是 data type `Method`
2. `<frame>` 参数是 **object 引用**，不是 string。必须先 `var f: object := str_to_obj(...)` 再传 `f`
3. 文档出处：`01-plantsimulation-knowledge/01-plant-simulation-help/objects/common-methods/common-methods.md` line 164 (`.InformationFlow.&Method.duplicate`)

### 替代路径：用 `local-simtalk-class-management` 的 `duplicate`

Plant Simulation 的 `duplicate(Destination:object, Name:string)` 方法的
`Destination` 参数同时接受 Folder 和 Frame —— 传 Folder 创建 Class
Library 新 class，传 Frame 创建 Frame 实例。
`local-simtalk-class-management/scripts/class_ops.py duplicate` 内部走
`srcObj := str_to_obj(<path>); srcObj.duplicate(str_to_obj(<dest>), "<name>")`，
因为是 object 引用调用，**不需要** `&` 操作符，能直接拿来建 Method 实例：

```bash
# 把 .InformationFlow.Method 的实例塞进 .Models.Model
python3 ../local-simtalk-class-management/scripts/class_ops.py \
    duplicate .InformationFlow.Method .Models.Model myMethod
```

实测 envelope（节选）：

```json
{
  "ok": true,
  "data": {
    "BEFORE_PATH": ".InformationFlow.Method",
    "AFTER_PATH":  ".Models.Model.myMethod",
    "AFTER_TYPE":  "Method",
    "AFTER_ORIGIN": ".InformationFlow.Method"
  }
}
```

什么时候用哪条路：

| 场景 | 推荐 |
|---|---|
| 创建 Method 实例 + 立即写入源代码（一步到位） | `write_simtalk.py --frame ... --new-method ...` |
| 单纯创建实例，源代码稍后单独写 | `class_ops.py duplicate <parent_class> <frame> <name>` |
| 想拿 JSON envelope 做脚本化校验 / audit | `class_ops.py`（自带 before/after/log_tail） |
| 想跑 raw SimTalk、不想要 `&` 之类的 dot-path 陷阱 | `class_ops.py`（走 `str_to_obj` 自动绕过） |

注意 `class_ops.py duplicate` **不能**写源代码 —— 写源代码仍走
`add_note.py --mode replace --confirm --note ...` 或
`write_simtalk.py --frame ... --new-method ...`。

## 写入 program

```simtalk
// 直接赋值字符串
&myMethod.program := "var i := 0" + chr(10) + "print i";

// 写完后立即执行验证
&myMethod.execute;
```

## 读 program

```simtalk
print &myMethod.program;   // 打印完整源代码
var src: string := &myMethod.program;
```

## 常见错误

| 错误信息 | 原因 | 修法 |
|---|---|---|
| `Syntax error near line 1 at 'result'` | `result` 是保留字 | 改名 `synOut` / `ret` |
| `Syntax error near line 1 at '=='` | 装饰行没用 `--` 或塞 `/* */` | 加 `--` 或用块注释 |
| `Left and right sides of the assignment are incompatible.` | 类型不匹配（如把 string 赋给 boolean） | 检查赋值两侧类型 |
| `Unknown identifier: foo` | 未声明的标识符（变量名拼错 / 没 import） | 检查 `var foo: type := ...` |
| `Error in line 1: Unexpected end of string` | program payload > 2 KB 被截断 | 分块写（见 Quirk #7 / #13） |

## Method 程序结构示范

**Init pattern**（在 Frame 启动时跑一次）：

```simtalk
-- init — initializes global state
var s: string := "system ready"
print s
```

**MU 处理**（作为 Station 的 Entrance Control / Exit Control 跑）：

```simtalk
-- count_part — increments counter for each MU entering
@.counter := @.counter + 1
print "MU " + to_str(@.counter) + " entered"
```

**Trigger 处理**（绑定到 EventController 的 Trigger Method）：

```simtalk
-- onTrigger — fires when the trigger activates
print "triggered at " + to_str(eventController.simTime)
&myMethod.executeIn(5)   // 5 秒后调度 myMethod
```
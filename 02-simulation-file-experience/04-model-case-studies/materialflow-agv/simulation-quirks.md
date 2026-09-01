# MaterialFlow_AGV — 实现期 SimTalk 坑

> 2026-08-31 实现 AGV_Claude 期间踩到的所有非显然问题。

## Quirk #1 — `var x : object` 实际可用,`var x : any` 才是真万能

**症状**:
- `var root : object; root := str_to_obj(...)` → "Syntax error near line 2 at 'root'"
- `var root : any; root := str_to_obj(...); print root.name` → OK

**原因猜测**:Plant Simulation 2606 的 parser 把 `object` 当成已保留关键字,可能与某些 object literal 冲突。

**Workaround**:
- 表格 → `var t : table`
- 对象引用 → `var x : any` (NOT `object`)
- 数字 → `var i : integer` / `var r : real`
- 字符串 → `var s : string`

**Validate**:
```simtalk
var x : any
x := str_to_obj(".InformationFlow.Method")
print x.name    -- "Method"
```

## Quirk #2 — `str_to_obj("...")[idx, idx] := value` 链式索引 parse error

**症状**:
```simtalk
str_to_obj(".Jobs")[0, 0] := "JobID"
-- Syntax error near line N at '['
```

**原因**:argparse/parser 不接受函数调用结果后直接跟 `[` 索引。

**Workaround**:
```simtalk
var t : table
t := str_to_obj(".Jobs")
t[0, 0] := "JobID"
```

## Quirk #3 — `createObject(class: object, ...)` 的第一参数是 class 对象,不是字符串

**症状**:
```simtalk
str_to_obj(".AGV_Claude").createObject("Folder", "Objects", 1)
-- Incompatible types in 'createObject', argument 1: object expected.
```

**Workaround**:用 `class_ops.py derive` 或 `duplicate` 创建子 Folder/MMethod。直接 `createObject` 在 SimTalk 里需要先 `str_to_obj` 到 class 引用,容易踩坑。

**推荐做法**:
```bash
python3 local-simtalk-class-management/scripts/class_ops.py derive \
    .MaterialFlow .AGV_Claude Objects
```

## Quirk #4 — Method 参数声明 `param x: type` 单独行有效,逗号分隔也有效

**实测**:
```simtalk
param pool: object              -- OK
return pool

param pool: object              -- OK
param pickStation: object       -- OK
param minBattery: real
return pool

param pool: object, pickStation: object, minBattery: real  -- OK
-> object
return pool
```

三种格式都可。`write_simtalk` 把代码按行传入,所有写法都通过。

## Quirk #5 — `write_simtalk --code-file` 对 `--` 开头行(注释)敏感(Quirk #10 in lifelines.md)

**症状**:
```simtalk
-- AGV_init: ...
var t : table
...
```
→ write_simtalk 报错 `add_note.py --mode replace failed (rc=2)`,argparse 把 `--` 当成 flag 终止符。

**Workaround**:
- 选项 A:`grep -v '^--'` 过滤注释行再写入
- 选项 B:用 `write_astart.py` 的 chunked TCP 模式,直接发 `obj.program := ...`
- 选项 C:把注释改成 `//` 形式 — Plant Simulation SimTalk 也支持 `//` 注释

实测 `//` 也有效,但 vendor 大多用 `--`。**约定:实现期使用 `//` 或不放注释**,交付/长期留存前再补 `--` 注释。

## Quirk #6 — `bfs_full.py` 在含特殊字符的 Frame 上 JSON parse 失败

**症状**:dump `.MaterialFlow_AGV.AdvancedObejcts.CapacityCalculation_v2` 报 "Unterminated string"。

**绕过**:绕过 BFS,直接用 read_library 的 single-method probe 或 get-folder-tree depth=1。

## Quirk #7 — readlog v15 回归:无法看到 `print` 输出

**症状**:`print "hello"` 在 GUI console 实际打印,但 `simtalk_send.py readlog` 取回陈年 trace 或空。

**Workaround**(本 session 使用):
- 用 `simtalk_syntax` 子命令(syntax check 实际会执行)替代 `simtalk_run` 来做快速反馈
- 关键验证用 `[verify] method executes OK after edit`(由 write_simtalk 输出)
- 最终结构用 `bfs_full.py` 抓 tree dump
- 大段结果存储到 DataTable cell 再用 syntax check 取出来

## Quirk #8 — 当前 SimTalk 不允许链式 `.~.~.~.~.~.~.~.~...` 属性导航

**症状**:写代码时容易 hallucinate 这样的链:
```simtalk
agv.~.~.~.~.~.~.~.~:~:~:~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~.~:~:~:~.~.~.~.~.~.~.~.~.~.~.~.~.~.~................name
```
这不是真实语法。`.~` 单独存在(`.~` = "any attribute access"),但不接受链式深度。

**Workaround**:直接属性访问 `agv.name` / `agv.IsIdle` / `agv.BatCharge` / `pool.NumIdleAGVs`。

## Quirk #9 — DataTable 必须先 setSize 才能索引

**症状**:
```simtalk
var t : table
t := str_to_obj(".Foo")
t[0, 0] := "header"
-- Access beyond the list dimensions in .Foo.
```

**Workaround**:
```simtalk
var t : table
t := str_to_obj(".Foo")
t.setSize(100, cols)
t[0, 0] := "header"
```

## Quirk #10 — `param x: object` 的"object" 与 `var x : object` 的"object" 是两个东西

**实测**:
- `param x: object` (声明方法形参) → OK
- `var x : object` (声明局部变量) → SYNTAX ERROR

可能是 parser 把 `var : object` 当成 `(var) : (object)` 错误解析,但 `param` 行有更明确的语法上下文,OK。

**统一约定**:全部用 `var x : any` / `var x : table` / `var x : integer` / `var x : real` / `var x : string`。避开 `object` 类型。
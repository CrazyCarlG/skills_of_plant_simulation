---
last_updated: 2026-09-01
contributors: [@z004bjuu, @plant-simulation-expert, @plant-simulation-experience-curator]
scope: 04-model-case-studies/materialflow-agv 实现期 SimTalk 坑(Quirk #1-#12)
---

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

> [superseded 2026-09-01 by @plant-simulation-experience-curator — see new Quirk #11 below; `setSize` workaround 不再有效 for Plant Simulation v2606.0002]

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

## Quirk #11 — DataTable 运行时 resize:必须用 `MaxYDim :=` / `MaxXDim :=` 属性,不是 `setSize`

> **supersedes**: Quirk #9 的 workaround(同症状,但 setSize 在 v2606.0002 已无效)。

- **症状**:AGV_init / AGV_reset 试图用 `tab.setSize(y, x)` 在运行时初始化 DataTable 头一行;compile 报 "Unknown identifier 'setSize'" / "Unknown identifier 'setRowNum'" / "Unknown identifier 'setColNum'" / "Unknown identifier 'setNoOfRows'"。同样地,在 `var t : object` 类型的 var 上调这些方法**直接不存在**(getAttrNo 全返 0)。
- **根因**:Plant Simulation v2606.0002 把 DataTable 的行/列尺寸从"method"挪到"assignable attribute";`setSize` 这类 mutator method 在 PS v15+ 文档里已不出现,只剩 `MaxYDim` / `MaxXDim` 两个 attribute 是 assignable 的。
- **Workaround / 结论**:

  ```simtalk
  -- canonical: 用属性赋值
  var t : table
  t := str_to_obj(".MyTable")
  t.MaxYDim := 1     -- 必须先 resize 才能写 cell
  t.MaxXDim := 8
  t[0, 0] := "JobID"
  t[0, 1] := "PickStation"
  -- ... headers 单独 cell 赋值
  ```

  **为什么不能 `var t : object`**:
  - `var t : object` 在 v2606.0002 是 SYNTAX ERROR(见 Quirk #10)
  - 即使声明成功,`var t : object` 也不暴露 DataTable 的 `MaxYDim` / `MaxXDim`(getAttrNo 全 0)
  - 必须 `var t : table` 才能访问 assignable attribute

  **0×0 表写 cell 的限制**(Quirk #12 详述):resize 后才能写;没有 "tab[0, 0] := v on 0x0 table" 这种 auto-grow。

- **tags**:`DataTable`, `resize`, `MaxYDim`, `MaxXDim`, `setSize-deprecated`, `v2606.0002`, `assignable-attribute`
- **see also**:`materialflow-agv/simulation-quirks.md §Quirk #9`(superseded) + `§Quirk #12`(新加:no auto-grow);`01-plantsimulation-knowledge/01-plant-simulation-help/objects/information-flow-objects/DataTable/attributes/attributes.md`(独立知识源);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md` §01-domain-concepts;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` Finding #1

> 这条经验教会我:
> - **Plant Simulation 跨版本 API 不稳**:同一个 method (`setSize`) 在 v18 文档有、v2606.0002 没有。**任何 DataTable 的"标准"方法都要先查当前版本的 KB docs**——别信通用记忆。
> - **assignable attribute ≠ method**:`MaxYDim := Y` 是属性赋值、`setSize(y, x)` 是方法调用——语法位置(`a := b` vs `a.method(b)`)和语义(永久生效 vs 一次性调用)都不同,Plant Simulation 把 resize 归到属性层是有意为之(可能为了避免 mutation order 问题)。
> - **supersede 时保留旧 entry 正文,只加 marker + 新 entry**——这样未来考古能看到 "setSize → MaxYDim/MaxXDim" 这个演进路径,而不是只看到最终答案。

## Quirk #12 — DataTable 0×0 表写 cell 抛 "Access beyond list dimensions",**没有** auto-grow

> 与 Quirk #11 配套(resize 后才能写 cell)。

- **症状**:新建/刚 `deleteObject` 清空的 DataTable(默认 0×0)上执行 `tab[0, 7] := "X"` 抛 "Access beyond the list dimensions in <path>"。任何 0×0 表的 cell 写入都崩。
- **根因**:DataTable 设计上是 strict-dimension;`tab[i, j] := v` 要求 `i < YDim AND j < XDim`。0×0 表的 `YDim=0`,所以任何 `i` 都 `≥ YDim` → 报 dimension error。**Plant Simulation v2606.0002 没有 Python list 那种 append-to-empty 自动扩容的行为**。
- **Workaround / 结论**:

  ```simtalk
  var t : table
  t := str_to_obj(".MyTable")

  -- 选项 A: 一次性 resize 到目标尺寸 + 直接写 cell
  t.MaxYDim := 100
  t.MaxXDim := 8
  t[0, 0] := "header_1"

  -- 选项 B: 边写边扩(appendRow 自动增 YDim;insertColumn 自动增 XDim)
  t.appendRow("v1", "v2", "v3")   -- YDim += 1, 同时写第一行 3 列
  t.insertColumn(0, "ColName")     -- XDim += 1, 新增列名为 "ColName"
  ```

  **API 选择**:
  - 已知目标尺寸 → `MaxYDim` / `MaxXDim`(最便宜,O(1))
  - 不知道 / 边构建边加 → `appendRow` / `insertColumn` / `insertRow`(O(N))
  - **不能** 依赖 "0×0 直接写 cell 然后 auto-resize" —— 不存在。

- **tags**:`DataTable`, `no-autogrow`, `appendRow`, `insertColumn`, `insertRow`, `access-beyond-dimensions`, `strict-dimension`
- **see also**:`materialflow-agv/simulation-quirks.md §Quirk #11`(resize API)+ `§Quirk #9`(superseded);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md` §01-domain-concepts;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` Step 5

> 这条经验教会我:
> - Plant Simulation 的"严格 dimension"哲学比 Python list 严格得多——任何"我要先写一行试试"都会被 dimension check 挡住。**永远先 resize 再写 cell**。
> - `appendRow` / `insertColumn` 是 v15+ 仍支持的方法(不像 `setSize` 那样被砍)——这印证了"DataTable 的 mutation API 跨版本大幅缩水"的判断。
> - 0×0 表 vs "刚 `deleteObject` 清空"是同一回事:`deleteObject` 把 dimension 重置成 0,所以"清空"和"不存在"在 DataTable 上是等价的——下次重建路径必须显式 resize。
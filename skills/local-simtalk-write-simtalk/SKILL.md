---
name: local-simtalk-write-simtalk
description: Write SimTalk source code into a Plant Simulation Method object, end-to-end. Use this skill whenever the user wants to "write SimTalk code", "implement a method", "add SimTalk logic to a Frame", "put code in `<path>`", "create a method that does X", "把 SimTalk 写到 `<path>`", "在 Frame 里写一个方法", "给 method 写代码". Workflow: (1) read Plant Simulation knowledge base for SimTalk syntax, (2) clarify what functionality the user wants, (3) confirm the working Frame path (SimTalk only runs inside a Frame), (4) if user already has a target Method path → write code via `local-simtalk-add-note-to-method` directly; if user needs a NEW Method → invoke `scripts/write_simtalk.py` which creates the instance via `.&Method.duplicate(<frame>, <name>)` (default parent class `.InformationFlow.Method`) then writes code via `local-simtalk-add-note-to-method`. Always respects `chr(10)`-for-newlines, `//` / `--` / `/* */` comments, and the note-language-matching rule. Does NOT execute the code itself — it only writes source into `program`. Triggers: "write a method that calculates throughput", "在 `.Models.Model` 下加一个叫 `count_parts` 的 method,内容是…", "I want SimTalk code that does X".
---

# local-simtalk-write-simtalk

把 SimTalk 源代码写入 Plant Simulation 中一个 Method 对象的完整工作流。本 skill
**不负责执行代码**，只负责**写出源代码**——执行是调用 Method 的下游行为。

写代码的实际搬运由 `local-simtalk-add-note-to-method` 完成（其内部用
`obj.program := <source>` 把字符串赋值给 Method 的 `program` 属性）。新 Method
的创建则通过 `simtalk_send.py run` 直接发 `.<class>.duplicate(<frame>, <name>)`——
**`create()` 在 SimTalk 里是关键字 + List 方法双重身份，不能用来创建 Method
实例**（详见 Step 5 / Quirk #15）。

> **何时触发本 skill.** 用户描述一段要实现的 SimTalk 功能（无论中文 / 英文），
> 即使没明说"写 SimTalk"，只要意图是**生成 SimTalk 源代码并存进 Plant Simulation
> 模型**，都应触发本 skill。如果用户只是问 SimTalk 语法（不写代码）则不触发。

## When to use

- "在 `.Models.Model` 下创建一个 `count_parts` 的 method，内容是遍历所有 MU 并打印数量"
- "Write SimTalk code that reads `attr1` from each part and stores it in a table"
- "给这个 Frame 写一个 init method，初始化全局变量"
- "我需要在 `.CTU.Frame.Program` 里加一段 SimTalk，做实时统计"
- "帮我写一段 SimTalk，遍历 Buffer 里的 MU"
- 用户贴出一段逻辑需求 → skill 输出 SimTalk 源代码并写入指定 Method

## Do NOT use for

- **查询 / 读取** Method 当前源代码（用 `local-simtalk-read-library`）
- **修改 `program` 以外的属性**（用 `local-simtalk-modify-object-atrribute`）
- **只想了解 SimTalk 语法而不写代码**（直接读 `01-plantsimulation-knowledge`）
- **执行 SimTalk 代码**（用 `local-simtalk-execution` 直接 `simtalk_run`）
- **只加注释、不改代码**（用 `local-simtalk-add-note-to-method` 的 `prepend` / `append`）
- **加密 / 解密 Method**（手动 `&Method.encrypt` / `&Method.decrypt`）
- **批量给多个 Method 加结构化注释**（用 `local-simtalk-simtalk-note-adder`）
- **写入 `.SimtalkClaude.*`** 下的方法（用户约定：禁止）

## 工作目录约定

SimTalk 只能在 **Frame** 内部运行，所以写代码的目标 Method 必须挂在某个 Frame
下。常见 Frame 路径示例：

| Frame 路径 | 说明 |
|---|---|
| `.CTU.Frame` | 经典 2D 模型工厂 Frame |
| `.Models.Model` | 模型根 Frame（Plant Simulation 默认模型根） |
| `.Models.Model.Frame` | 模型根下的二级 Frame |
| `<user 自定义>` | 用户项目里的 Frame |

**默认行为：必须先向用户确认目标 Frame 路径。** 如果用户说"随便找个地方"或
"默认的"，则推荐 `.Models.Model`（Plant Simulation 模板里几乎都存在）。

## 默认 Method 父类

新 Method 的默认父类是 **`.InformationFlow.Method`**（Plant Simulation Class
Library 的 Basic Objects → InformationFlow → Method）。这是 Plant Simulation
帮助文档明确推荐的路径：

> 点击 Home 功能区选项卡上的 **Manage Class Library > Basic Objects >
> InformationFlow > Method**。

如果用户指定了别的父类（例如自定义 `MyMethod`），则使用用户指定的。

## Method 命名

默认 `myMethod`，但必须询问用户期望的名字（因为 Frame 里已有同名对象时会冲突）。

## Workflow

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. 读 Plant Simulation 知识库 → 掌握 SimTalk 语法                       │
│    /root/skills_of_plant_simulation/01-plantsimulation-knowledge/      │
│      01-plant-simulation-help/objects/information-flow-objects/Method/ │
│      01-plant-simulation-help/programming-a-method/                   │
│      01-plant-simulation-help/objects/simtalk/                         │
│ 2. 与用户确认：要实现什么功能（功能描述）                                │
│ 3. 与用户确认：目标 Frame 路径                                          │
│ 4. 与用户确认：Method 路径（已有就用现有的，没有就指定新 Method 的名字）  │
│ 5. 若新 Method → 用 simtalk_send.py run 发送                           │
│    .InformationFlow.&Method.duplicate(<frame>, "<name>")               │
│    （默认 .InformationFlow.Method，或用户指定的 parent class；           │
│     也可走 class_ops.py duplicate <parent> <frame> <name>，            │
│     但本 skill 默认走 write_simtalk.py 一步到位）                      │
│ 6. 用 SimTalk 语法写源代码                                              │
│ 7. 调 local-simtalk-add-note-to-method 的 --mode replace --confirm     │
│    把代码写入 program（它会自动备份原 program 到 log/）                  │
│ 8. 让用户 review（可选：在 GUI 双击 Method 看高亮是否正确）             │
└────────────────────────────────────────────────────────────────────────┘
```

### Step 1 — 读知识库（必做）

每次接到"写 SimTalk"请求，**先读** `/root/skills_of_plant_simulation/
01-plantsimulation-knowledge/01-plant-simulation-help/` 里的相关章节：

- `objects/information-flow-objects/Method/` — Method 对象本身
- `objects/simtalk/` 或 `programming-a-method/` — SimTalk 语言本身
- `objects/common-methods/common-methods.md` — 所有对象共有的方法（`create`
  / `deleteObject` / `moveToFolder` / `setName` 等）

至少要确认：

- 注释语法：`//` 单行、`--` 单行、`/* */` 块注释
- 字符串字面量：`chr(10)` 才是真换行，文字 `\n` 是两字符（重要 Quirks）
- Method 引用：`&Method` 才拿到 Method 对象本身，裸 `Method` 会被执行
- SimTalk 2.0 是新 Method 默认语法（`UsingNewSyntax := true`）

### Step 2 — 与用户澄清功能

收到用户的请求后，可能不完整。**先复述理解**，再问关键的歧义点。常见需要
澄清的点：

- 输入 / 输出参数（如果有外部调用，参数列表是什么？）
- 调用方是谁（`Trigger` / `EventController` / 控件 / 别的 Method？）
- 是否需要在多个 Method 间共享状态（哪些 `current.~.xxx` 字典？）
- 是否要返回值（`->string` / `->integer` / `->boolean` / `->real` / `->any`）

### Step 3 — 确认 Frame 路径

直接问用户："目标 Frame 是哪个？"如果用户说"随便"，用 `.Models.Model`。

### Step 4 — 确认 Method 路径 / 名字

两种可能：

**A. 用户已有 Method 路径**（"写到 `.Models.Model.count_parts` 里"）
→ 直接进入 Step 6 / 7，跳过 Step 5。

**B. 用户没指定，需要新建**（"加一个 method 进去"）
→ 询问名字（默认 `myMethod`），进入 Step 5。

### Step 5 — 创建 Method 实例（仅 B 路径）

调用 `local-simtalk-class-management` 的 **只读** 子命令确认 parent 路径有效
（不要用它的 derive / duplicate，那些动的是 Class Library）。然后用
`simtalk_send.py run` 直接发 `duplicate()` 调用。

- **调用 `local-simtalk-class-management` 的 `list` 子命令**确认 parent 路径
  有效（可选，但建议）。
- **调用 `local-simtalk-class-management` 的 `inspect` 子命令**确认 parent 的
  `InternalClassType` 是 `Method`（否则 duplicate 会失败）。
- **用 `local-simtalk-execution/scripts/simtalk_send.py run`** 直接发送：

  ```simtalk
  var f: object := str_to_obj(<frame_path>);
  .InformationFlow.&Method.duplicate(f, "<method_name>");
  print "###CREATE_OK###";
  ```

  其中：
  - `<frame_path>` 是 Step 3 拿到的 Frame 路径（例如 `.Models.Model`）
  - `<method_name>` 是用户在 Step 4 选定的名字
  - **关键**：路径最后一段前必须加 `&`（`.InformationFlow.&Method.duplicate(...)`），
    让 SimTalk 把它当 class object 而不是 data type `Method`

> **关键 Quirk — `create` 是 SimTalk 关键字 + List 方法的双重身份，完全不能
> 用来创建 Method 实例。** 三种"看似合理"的写法全都失败：
>
> ```simtalk
> -- ❌ 写法 1 — 触发 'Unknown identifier create'
> var p: object := str_to_obj(".InformationFlow.Method");
> p.create(f, "myMethod");
>
> -- ❌ 写法 2 — 触发 "'create' can only be applied to lists or objects or variables of data type list"
> .InformationFlow.Method.create(f, "myMethod");
>
> -- ❌ 写法 3 — 仍然失败，因为 create 已是保留字无法 dispatch
> .InformationFlow.&Method.create(f, "myMethod");
> ```
>
> **唯一能用的写法是 `duplicate()` + `&` 引用操作符**：
> ```simtalk
> -- ✅ 正确 — Plant Simulation 帮助文档明确推荐
> .InformationFlow.&Method.duplicate(f, "myMethod");
> ```
>
> Plant Simulation 帮助文档里 `.InformationFlow.&Method.duplicate` 这一行
> （`objects/common-methods/common-methods.md` line 164）是这个 pattern 的
> 权威出处。

> **重要.** `local-simtalk-class-management` 的 `derive` / `duplicate` 子命令
> 既能动 **Class Library**（`dest` 是 Folder），**也能创建 Frame 实例**
> （`dest` 是 Frame）——Plant Simulation 的 `duplicate()` 方法的 `Destination:object`
> 参数同时接受 Folder 和 Frame。两条创建路径选一条用：
>
> - **`write_simtalk.py`**（默认）：dot-path 字面量 + `&` + `str_to_obj` 拿
>   frame object，单条命令搞定「创建 + 写代码」。
> - **`class_ops.py duplicate <parent_class> <frame> <name>`**：object reference
>   调用，不需要 `&`，返回 JSON envelope（`before`/`after`/`log_tail`）便于审计。
>   后续写代码仍走 `add_note.py`。
>
> 文档原文（`common-methods.md` line 166）：
> ```simtalk
> var myConveyor: object := .MaterialFlow.Conveyor.duplicate(.Models.Model, "MyConveyor")
> ```
> 本 skill 默认走第一条路（`write_simtalk.py`），但**两种都是正确的**。

### Step 6 — 组装 SimTalk 源代码

根据 Step 2 的功能描述，按 Plant Simulation SimTalk 2.0 语法写源代码。要点：

- **注释语言匹配**：用户用中文发文 → 注释写中文；用英文 → 英文；混合 → 照搬。
- **`chr(10)` 真实换行**：在 Python 侧生成多行字符串时用 `chr(10)` join，
  不能写 `"\n"`（SimTalk 不会解释 `"\n"` 为换行符）。
- **避免使用保留标识符**：`result` 是 SimTalk 隐式返回值变量，禁止做局部变量
  名（会触发 `Syntax error near line 1 at 'result'`）。用 `synOut` / `res` /
  `ret` 等替代。
- **块注释优先**：包含装饰行（`=====`、`-----`、`*****`）的注释务必用
  `/* ... */` 包裹，SimTalk 的 lexer 会先把裸 `==` 当等号运算符 tokenize，
  再判断是不是注释——直接 `Syntax error near line 1 at '=='`.
- **避免命名冲突**：写之前先用 `local-simtalk-get-folder-tree` 看一下目标
  Frame 下是否已有同名 Method。

写完后输出完整源代码给用户看（一段一行，`chr(10)` 分隔），让用户最后确认
一次再写。

### Step 7 — 写入 Method

调用 `local-simtalk-add-note-to-method`：

```bash
python3 /root/skills_of_plant_simulation/skills/local-simtalk-add-note-to-method/scripts/add_note.py \
    --path <method_path> \
    --mode replace \
    --confirm \
    --note "<line 1>" "<line 2>" "<line 3>" ...
```

或者更稳的做法——把源代码先写到临时文件，再用 `--note $(cat tmp.txt)`：

```bash
cat > /tmp/my_method_code.txt <<'EOF'
-- myMethod — counts parts in the system
var n: integer := 0
while @.getMUs.length > 0
    @.getMUs.first.deleteObject
    n := n + 1
end
print n
EOF

python3 ../local-simtalk-add-note-to-method/scripts/add_note.py \
    --path .Models.Model.myMethod \
    --mode replace \
    --confirm \
    --note $(cat /tmp/my_method_code.txt)
```

**或者**用本 skill 自带的 `scripts/write_simtalk.py`（见 Usage），它帮你处理
`--note` 多行的传参问题（Quirk #10：argparse 会在以 `--` 开头的 token 处截断
note 行）。

### Step 8 — 让用户 review

写完后，建议用户双击目标 Method 图标看 Plant Simulation 编辑器里的语法高亮，
确认代码正确显示（没有 `\` `n` 这种两字符、没有 `Syntax error near line N` 的
红框）。

如果编辑器报告语法错误，立即用 `--restore` 回滚到 Step 7 之前的状态：

```bash
python3 ../local-simtalk-add-note-to-method/scripts/add_note.py --restore \
    --backup log/<path>_program_original.txt \
    --path <method_path>
```

## Usage

本 skill 自带 `scripts/write_simtalk.py`，把 Step 5 / 6 / 7 自动化：

```bash
# A. 写入到现有 Method（跳过创建步骤）
python3 scripts/write_simtalk.py \
    --path .Models.Model.count_parts \
    --code-file /tmp/code.txt

# B. 创建新 Method（默认父类 .InformationFlow.Method）再写入
python3 scripts/write_simtalk.py \
    --frame .Models.Model \
    --new-method count_parts \
    --code-file /tmp/code.txt

# C. 自定义父类
python3 scripts/write_simtalk.py \
    --frame .Models.Model \
    --new-method log_warn \
    --parent-class .UserObjects.LoggingMethod \
    --code-file /tmp/code.txt

# D. 从命令行直接传代码（少见；注意引号转义）
python3 scripts/write_simtalk.py \
    --path .CTU.Frame.Program \
    --code "line1
line2"

# E. 只预览、不发送（创建 + 写代码都跳过）
python3 scripts/write_simtalk.py \
    --frame .Models.Model \
    --new-method myMethod \
    --code-file /tmp/code.txt \
    --dry-run
```

`--code-file` 接受 **UTF-8 文本文件**（推荐，避免命令行长度超限）。
`--code` 接受多行字符串，每行作为一个 `--note` 参数传给 `add_note.py`
（绕开 Quirk #10：argparse `nargs="+"` 会在以 `--` 开头的 token 处截断）。

## 注释语言匹配规则（继承自 add-note-to-method）

跟 `local-simtalk-add-note-to-method` 一样：

- **英文请求** → 英文注释
- **中文请求** → 中文注释
- **混合请求** → 镜像用户的混合方式
- **明确覆盖**（"用英文" / "用中文注释"）→ 服从明确指令
- **代码标识符保持原样**：Method 路径、SimTalk 关键字、引号里的契约字符串
  不翻译
- **Section 标题 / metadata 行**（`-- Method path :`、`-- Purpose` 等）可双
  语并列；若请求是单语，则单语清晰呈现

## 硬规则 / Quirks

| # | 规则 | 为什么这个 skill 要关心 |
|---|---|---|
| 1 | 用 `chr(10)` 作为真换行，不要 `"\n"` | SimTalk 字面量**不**解释转义序列；`"\n"` 会被解析为 `\` 和 `n` 两字符 |
| 2 | 写之前先 backup 原 `program` | `local-simtalk-add-note-to-method` 的 `--mode replace` 会自动备份到 `log/<path>_program_original.txt`；不要跳过 |
| 3 | 写完后**必须** readback 并 `obj.execute` 验证 | `add_note.py` 默认会调 `obj.execute` 跑一次确认还能跑；保留这个验证 |
| 4 | 写入前确认 `internalclasstype == "Method"` | 其他类型（`Frame` / `Station` 等）的 `program` 属性可能不存在或语义不同 |
| 5 | `simtalk_run` `result:"success"` 配 `log:"code execute failed..."` = 软失败 | 这是 simtalk_execution 的 Quirk #7；写完后用 `readlog` 二次确认 |
| 6 | 写完后必须 `obj.program` 读回对比 | socket 不返回值，只有 `print + readlog` 看得见 |
| 7 | 单次 `obj.program := <source>` 的 payload 必须 ≤ ~2 KB | 服务器端 JSON 解析器截断 > ~2 KB 的 payload 并返回 `Error in line 1: Unexpected end of string`；长代码必须**分块**写入 |
| 8 | **绝不要**在 `.SimtalkClaude.*` 下写代码 | 用户约定：禁止 |
| 9 | `result` 是保留字（隐式函数返回值），不能做局部变量名 | `var result` 会触发 `Syntax error near line 1 at 'result'`；用 `synOut` / `ret` 替代 |
| 10 | `add_note.py --note` 用 `argparse nargs="+"` 会截断以 `--` 开头的 token | 注释行以 `--` 开头时不能用 `--note` 直接传；用 `write_simtalk.py --code <file>` 绕开 |
| 11 | 装饰行（`=====` / `-----`）必须 `--` / `//` 开头，**或**塞在 `/* */` 块里 | SimTalk lexer 先 tokenize 再判定是否注释；裸 `==` 触发 `Syntax error near line 1 at '=='.` |
| 12 | `simtalk_hasError(<source>)` 返回 `string`（不是 `boolean`） | 写成 `var b: boolean` 会报 `Left and right sides of the assignment are incompatible.` |
| 13 | 写 Method 必须挂在 Frame 下 | SimTalk 只能在 Frame 内部运行；孤立 Method 无意义 |
| 14 | **不要用 `<parent>.create(<path>, <name>)` 创建后再立刻 `obj.program := ...`** | 实际无副作用但破坏了"创建 → 写代码"两步分明的审计链；本 skill 把两步分开执行（Step 5 创建 → Step 7 写代码），每步独立 readback。**并且 `create()` 根本不能用于创建 Method**——见 Quirk #15，必须用 `.&Method.duplicate(...)` |
| 15 | **`create` 是 SimTalk 关键字 + List 方法，无法用来创建 Method 实例** | 三种"看起来合理"的写法都失败：(a) `var p: object := str_to_obj(".InformationFlow.Method"); p.create(f, "x")` → `Unknown identifier 'create'`；(b) `.InformationFlow.Method.create(f, "x")` → `'create' can only be applied to lists or objects or variables of data type list`；(c) `.InformationFlow.&Method.create(f, "x")` → 仍然失败（`create` 已是保留字无法 dispatch）。**必须用 `duplicate()`**：`var f: object := str_to_obj(<frame>); .InformationFlow.&Method.duplicate(f, "<name>");`。文档出处：`objects/common-methods/common-methods.md` line 164 (`.InformationFlow.&Method.duplicate`) |
| 16 | **`duplicate(<frame>, <name>)` 的 frame 参数是 object 引用，不是 string** | 写成 `.Class.duplicate(".Models.Model", "x")` 会失败；必须 `var f: object := str_to_obj(<frame>); .Class.duplicate(f, "<name>");`。路径最后一段前加 `&`（`.InformationFlow.&Method.duplicate(...)`）告诉 SimTalk 把名字当 class object 而不是 data type `Method` |

## Limitations

- **一次只写一个 Method**。要写多个 Method，循环调用 `scripts/write_simtalk.py`。
- **不验证 SimTalk 语法的语义**。脚本只检查代码能否被 Plant Simulation 解析
  并 `obj.execute` 不抛异常；如果业务逻辑错了，skill 无能为力。
- **不处理加密 Method**。`Encrypted := true` 的 Method 不能 `program :=`，
  必须先 `&Method.decrypt(<key>)`。本 skill 假设目标 Method 未加密。
- **不处理 `HasSyntaxError` 已是 `true` 的 Method**。若目标 Method 已经有
  语法错误，必须先手动修掉旧错误再 `replace`，否则新代码叠加在错代码上。
- **创建 / 写代码不是事务**。如果中途失败（创建成功但写代码失败），会留下
  一个空的 Method。需要手工删除或继续 `replace`。
- **`readlog` 在 v15+ 降级**——可能捕获不到 `print(...)`。如果 marker 没出现，
  fallback 到 GUI Console（Window ribbon → Console）。
- **不维护自己的 TCP 传输**——全部经由 `local-simtalk-execution/scripts/
  simtalk_send.py`（被 `add_note.py` 间接调用）。

## Key files

- `scripts/write_simtalk.py` — 主入口。处理"create new Method" vs "use existing
  Method" 两条路径，然后调用 `add_note.py --mode replace --confirm` 写代码。
- `examples/example_session.md` — 一个完整的端到端会话示例。
- `references/simtalk-syntax-notes.md` — SimTalk 2.0 速查（注释 / 字符串 /
  引用 / `&` / `chr(10)`），写代码时随手翻。
- `references/plant-simulation-help-links.md` — 知识库目录映射，方便按主题找
  文档。
- `log/` — 每次写代码的会话日志（人类可读）。
- `usage_log/` — 每次调用的机器可读 JSON 信封（`subcommand`、`args`、
  `before`、`after`、`log_tail`）。

## Related skills

- **`local-simtalk-add-note-to-method`** — 实际写代码的搬运工，本 skill 是它的
  前端流程包装。每次写代码都必须调它（用 `--mode replace --confirm`）。
- **`local-simtalk-class-management`** — 写代码前**确认 parent 路径有效**的
  工具。`list <folder>` / `inspect <path>` 子命令必用；`duplicate <parent>
  <frame> <name>` 子命令**也能直接创建 Method 实例**（dest 是 Frame 而不是
  Folder 时），只是不写代码——写代码仍走 `add_note.py` 或 `write_simtalk.py`。
- **`local-simtalk-get-folder-tree`** — 找目标 Frame / 已有 Method 时用。
- **`local-simtalk-get-class-inheritance`** — 确认 `.InformationFlow.Method`
  父类时用（一般 `.InformationFlow.Method` 是内置稳定类，不需要专门 inspect，
  但用户指定自定义父类时必查）。
- **`local-simtalk-read-library`** — 写代码前看现有 Method 都调用了什么，
  避免重复造轮子。
- **`local-simtalk-execution`** — 底层 TCP 传输。所有 SimTalk 调用最终都经过它。
- **`local-simtalk-modify-object-atrribute`** — 改 Method 自己的属性
  （`RandomSeed` / `UsingNewSyntax`）时用，不属于"写代码"。
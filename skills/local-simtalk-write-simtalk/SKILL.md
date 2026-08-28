---
name: local-simtalk-write-simtalk
description: Write SimTalk source code into an EXISTING Plant Simulation Method object, end-to-end. Use this skill ONLY when the user already has a target Method path (or has just created one with `local-simtalk-create-method-object`) and wants source code put into its `program` attribute. The skill reads the Plant Simulation knowledge base for SimTalk syntax, then calls `local-simtalk-add-note-to-method` with `--mode replace --confirm` to set `obj.program := <source>` — handling backup, readback, and execute-verify. Does NOT create Method instances; if the target Method doesn't exist, invoke `local-simtalk-create-method-object` first (or ask the user for the path). Does NOT execute the code; it only writes source. Triggers: "write SimTalk code into `<path>`", "implement a method", "把 SimTalk 写到 `<path>`", "在 Frame 里写一个 method", "给 method 写代码" (only when the Method path already exists).
---

# local-simtalk-write-simtalk

把 SimTalk 源代码写入 Plant Simulation 中一个**已存在的** Method 对象的
完整工作流。本 skill **不负责创建 Method 实例**（那是
`local-simtalk-create-method-object` 的职责），也**不负责执行代码**——
只负责把源代码写到 `program` 属性里。执行是调用 Method 的下游行为。

写代码的实际搬运由 `local-simtalk-add-note-to-method` 完成（其内部用
`obj.program := <source>` 把字符串赋值给 Method 的 `program` 属性）。

> **何时触发本 skill.** 用户描述一段要实现的 SimTalk 功能（无论中文 / 英文），
> 即使没明说"写 SimTalk"，只要意图是**生成 SimTalk 源代码并存进 Plant Simulation
> 模型**、**且目标 Method 已存在**，都应触发本 skill。如果用户没指定 Method
> 路径（或指定的 Method 不存在），则先调 `local-simtalk-create-method-object`
> 创建容器，再调本 skill 写代码。

## When to use

- "在 `.Models.Model.count_parts` 里加一段 SimTalk，遍历所有 MU 并打印数量"
- "Write SimTalk code that reads `attr1` from each part and stores it in a table"
- "给这个 Frame 写一个 init method，初始化全局变量"
- "我需要在 `.CTU.Frame.Program` 里加一段 SimTalk，做实时统计"
- "帮我写一段 SimTalk，遍历 Buffer 里的 MU"
- 用户贴出一段逻辑需求 + 目标 Method 路径 → skill 输出 SimTalk 源代码并写入

## Do NOT use for

- **创建 Method 实例**（用 `local-simtalk-create-method-object`）
- **查询 / 读取** Method 当前源代码（用 `local-simtalk-read-library`）
- **修改 `program` 以外的属性**（用 `local-simtalk-modify-object-attribute`）
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

**默认行为：必须先向用户确认目标 Method 路径。** 如果用户说"随便找个地方"或
"默认的"，则先调 `local-simtalk-create-method-object --frame .Models.Model`
创建一个新的空 Method，再把它的路径传给本 skill 的 `--path`。

## 与 `local-simtalk-create-method-object` 的协作

```
用户: "写一个计算吞吐量的 method" (没指定 Method)
  ↓
create-method-object: 创建 .Models.Model.throughput (空容器)
  ↓ (返回新 Method 路径)
write-simtalk: 把 SimTalk 代码写到 .Models.Model.throughput.program
```

或者用户直接说"写到 `.Models.Model.count_parts` 里"：

```
用户 → write-simtalk --path .Models.Model.count_parts --code-file ...
  (跳过 create-method-object，因为 Method 已存在)
```

## Workflow

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. 读 Plant Simulation 知识库 → 掌握 SimTalk 语法                       │
│    01-plantsimulation-knowledge/                                       │
│      01-plant-simulation-help/objects/information-flow-objects/Method/ │
│      01-plant-simulation-help/programming-a-method/                   │
│      01-plant-simulation-help/objects/simtalk/                         │
│ 2. 与用户确认：要实现什么功能（功能描述）                                │
│ 3. 与用户确认：目标 Method 路径                                          │
│    - 如果 Method 已存在 → 直接进入 Step 4                               │
│    - 如果 Method 不存在 → 先调 local-simtalk-create-method-object       │
│ 4. 组装 SimTalk 源代码                                                  │
│ 5. 调 local-simtalk-add-note-to-method 的 --mode replace --confirm     │
│    把代码写入 program（它会自动备份原 program 到 log/）                  │
│ 6. 让用户 review（可选：在 GUI 双击 Method 看高亮是否正确）             │
└────────────────────────────────────────────────────────────────────────┘
```

### Step 1 — 读知识库（必做）

每次接到"写 SimTalk"请求，**先读** `
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

### Step 3 — 确认 Method 路径

直接问用户："目标 Method 是哪个路径？"如果用户说"随便"或"默认的"，
按上面的「与 create-method-object 协作」走：先创建再写。

**不要**在本 skill 里调用 `class_ops.py duplicate` 或 `.&Method.duplicate()`
创建 Method — 那是 `local-simtalk-create-method-object` 的职责。

### Step 4 — 组装 SimTalk 源代码

根据 Step 2 的功能描述，按 Plant Simulation SimTalk 2.0 语法写源代码。要点：

- **注释语言匹配**：用户用中文发文 → 注释写中文；用英文 → 英文；混合 → 照搬。
- **`chr(10)` 真实换行**：在 Python 侧生成多行字符串时用 `chr(10)` join，
  不能写 `"\n"`（SimTalk 不会解释 `"\n"` 为换行符）。
- **避免使用保留标识符**：`result` 是 SimTalk 隐式返回值变量，禁止做局部变量
  名（会触发 `Syntax error near line 1 at 'result'`）。用 `synOut` / `res` /
  `ret` 等替代。
- **块注释优先**：包含装饰行（`=====`、`-----`、`*****`）的注释务必用
  `/* ... */` 包裹，SimTalk 的 lexer 会先把裸 `==` 当等号运算符 tokenize，
  再判断是不是注释——直接 `Syntax error near line 1 at '=='.`
- **避免命名冲突**：写之前先用 `local-simtalk-get-folder-tree` 看一下目标
  Frame 下是否已有同名 Method。

写完后输出完整源代码给用户看（一段一行，`chr(10)` 分隔），让用户最后确认
一次再写。

### Step 5 — 写入 Method

调用 `local-simtalk-add-note-to-method`：

```bash
python3 skills/local-simtalk-add-note-to-method/scripts/add_note.py \
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

### Step 6 — 让用户 review

写完后，建议用户双击目标 Method 图标看 Plant Simulation 编辑器里的语法高亮，
确认代码正确显示（没有 `\` `n` 这种两字符、没有 `Syntax error near line N` 的
红框）。

如果编辑器报告语法错误，立即用 `--restore` 回滚到 Step 5 之前的状态：

```bash
python3 ../local-simtalk-add-note-to-method/scripts/add_note.py --restore \
    --backup log/<path>_program_original.txt \
    --path <method_path>
```

## Usage

本 skill 自带 `scripts/write_simtalk.py`，把 Step 5 自动化：

```bash
# A. 写入到现有 Method（最常见用法）
python3 scripts/write_simtalk.py \
    --path .Models.Model.count_parts \
    --code-file /tmp/code.txt

# B. 从命令行直接传代码（少见；注意引号转义）
python3 scripts/write_simtalk.py \
    --path .CTU.Frame.Program \
    --code "line1
line2"

# C. 只预览、不发送
python3 scripts/write_simtalk.py \
    --path .Models.Model.count_parts \
    --code-file /tmp/code.txt \
    --dry-run
```

`--path` 是**必填**且必须指向已存在的 Method。如果 Method 不存在，
请先用 `local-simtalk-create-method-object` 创建空容器，再调本 skill 写代码。

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
| 10 | `add_note.py --note` 用 `argparse nargs="+"` 会截断以 `--` 开头的 token | 注释行以 `--` 开头时不能用 `--note` 直接传；用 `write_simtalk.py --code-file <file>` 绕开 |
| 11 | 装饰行（`=====` / `-----`）必须 `--` / `//` 开头，**或**塞在 `/* */` 块里 | SimTalk lexer 先 tokenize 再判定是否注释；裸 `==` 触发 `Syntax error near line 1 at '=='.` |
| 12 | `simtalk_hasError(<source>)` 返回 `string`（不是 `boolean`） | 写成 `var b: boolean` 会报 `Left and right sides of the assignment are incompatible.` |
| 13 | 写 Method 必须挂在 Frame 下 | SimTalk 只能在 Frame 内部运行；孤立 Method 无意义 |
| 14 | 本 skill **不创建** Method 实例 | 创建 Method 用 `local-simtalk-create-method-object`；本 skill 假设 `--path` 已存在 |

## Limitations

- **一次只写一个 Method**。要写多个 Method，循环调用 `scripts/write_simtalk.py`。
- **不验证 SimTalk 语法的语义**。脚本只检查代码能否被 Plant Simulation 解析
  并 `obj.execute` 不抛异常；如果业务逻辑错了，skill 无能为力。
- **不处理加密 Method**。`Encrypted := true` 的 Method 不能 `program :=`，
  必须先 `&Method.decrypt(<key>)`。本 skill 假设目标 Method 未加密。
- **不处理 `HasSyntaxError` 已是 `true` 的 Method**。若目标 Method 已经有
  语法错误，必须先手动修掉旧错误再 `replace`，否则新代码叠加在错代码上。
- **`readlog` 在 v15+ 降级**——可能捕获不到 `print(...)`。如果 marker 没出现，
  fallback 到 GUI Console（Window ribbon → Console）。
- **不维护自己的 TCP 传输**——全部经由 `local-simtalk-execution/scripts/
  simtalk_send.py`（被 `add_note.py` 间接调用）。
- **不创建 Method 实例**。如果目标 Method 不存在，请先用
  `local-simtalk-create-method-object`。

## Key files

- `scripts/write_simtalk.py` — 主入口。只处理"已有 Method 路径 → 写代码"
  这一件事；创建 Method 实例的职责已移交给 `local-simtalk-create-method-object`。
- `examples/example_session.md` — 一个完整的端到端会话示例。
- `references/simtalk-syntax-notes.md` — SimTalk 2.0 速查（注释 / 字符串 /
  引用 / `&` / `chr(10)`），写代码时随手翻。
- `references/plant-simulation-help-links.md` — 知识库目录映射，方便按主题找
  文档。
- `log/` — 每次写代码的会话日志（人类可读）。
- `usage_log/` — 每次调用的机器可读 JSON 信封。

## Related skills

- **`local-simtalk-create-method-object`** — 创建空 Method 实例。
  凡是本 skill 接到请求但目标 Method 不存在时，先调它创建容器，再调本 skill
  写代码。
- **`local-simtalk-add-note-to-method`** — 实际写代码的搬运工，本 skill 是它的
  前端流程包装。每次写代码都必须调它（用 `--mode replace --confirm`）。
- **`local-simtalk-class-management`** — 写代码前**确认 parent 路径有效**的
  工具。`list <folder>` / `inspect <path>` 子命令必用。
- **`local-simtalk-get-folder-tree`** — 找目标 Frame / 已有 Method 时用。
- **`local-simtalk-get-class-inheritance`** — 确认 `.InformationFlow.Method`
  父类时用（一般 `.InformationFlow.Method` 是内置稳定类，不需要专门 inspect，
  但用户指定自定义父类时必查）。
- **`local-simtalk-read-library`** — 写代码前看现有 Method 都调用了什么，
  避免重复造轮子。
- **`local-simtalk-execution`** — 底层 TCP 传输。所有 SimTalk 调用最终都经过它。
- **`local-simtalk-modify-object-attribute`** — 改 Method 自己的属性
  （`RandomSeed` / `UsingNewSyntax`）时用，不属于"写代码"。
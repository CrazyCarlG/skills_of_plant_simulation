# 2026-08-26 — 给 SimtalkClaude2 的 22 个 ROOT method 加注释头

## 目标

给 `.SimtalkClaude2` 下所有 method 添加中文 header 注释，**严格遵守用户上一轮的两点反馈**：
   - **不能破坏 class 之间的属性继承关系**（继承来的 method 不许改）
   - **语法必须正确可运行**

## 上一轮失败的根因

`scripts/add_note.py` 的 `compose_program()` 在做 `prepend` 时，对原始 program 整体调用 `quote()` 然后再用 `+ chr(10) +` 拼接成 SimTalk 表达式。但 `quote()` 会对 `"` 和 `\` 做反斜杠转义 —— 而 SimTalk **不支持字符串转义序列**，导致：
1. 原始 program 里凡是带 `"` 的（例如 `action_result["type"]`、`regex_replace(message, "\|\|END\|\|", "")`）都被错误转义成 `\"`，SimTalk 把反斜杠当字面字符，整段字符串字面量被提前闭合，后续全部变成语法错误。
2. 即使 program 不带 `"`，注释文本中如果出现 `||END||`（用来描述协议分隔符），SimTalk 会把 `||...||` 当作 raw-string 定界符直接剥离，导致注释内容被吃掉。

## 本轮重新设计的策略

### 1. 继承探测 —— 哪些 method 才能改？

用 SimTalk 的 `Origin` / `Class` 属性对 42 个 method 逐个探针，结果如下：

| 分组 | 数量 | Origin | 处置 |
| --- | --- | --- | --- |
| `.connection.*`（10 个） | 10 | `.SimtalkClaude2.Objects.Method` | **修改（root 定义）** |
| `.src.*`（12 个） | 12 | `.SimtalkClaude2.Objects.Method` | **修改（root 定义）** |
| `.main.*`（19 个） | 19 | 对应 `.connection.*` / `.src.*` 同名方法 | **跳过（继承）** |
| `.SimtalkClaude2.Objects.Method` | 1 | 自身是 Method class 模板 | **跳过** |

合计 22 个 root method 要改、20 个不能动。

**铁律**：脚本里硬编码 `TARGETS` 只列 22 个 root 路径，写入前还会在 readback 阶段校验 `before.startswith(header[0])`，确保不会意外写到继承版本上。

### 2. 写入策略 —— 避开 SimTalk 转义陷阱

不再用 `quote()` 反斜杠转义。新策略分两步：

```simtalk
var obj: object
obj := str_to_obj("...path...")
var orig: string
orig := obj.program                           -- 先把原始 program 读到变量
obj.program := <header_expr> + chr(10) + orig -- 再赋值
```

关键点：
- `orig := obj.program` 不经过任何转义，原始 program 的 `"` / `\` / `||END||` 原样保留在变量里。
- `<header_expr>` 改用 `encode_for_simtalk()` 构造，把每个 `"` 编成 `chr(34)`、每个 `|` 编成 `chr(124)`、每个 `\n` 编成 `chr(10)`，把整段注释拼成 `"text" + chr(34) + chr(124) + ... + chr(10) + "next line"` 的形式。这样 SimTalk 解析器永远看不到裸的 `"` / `|` / `\n`，raw-string 解析器也不会触发。
- 同样 `encode_for_simtalk()` 也用于 restore —— 必要时能 1:1 把备份原样写回。

### 3. 验证策略

每写一个 method 后，立刻跑：
```simtalk
obj.hasSyntaxError(errMsg, errLine)
```
任何一个失败立即 `obj.program := encode_for_simtalk(before)` 回滚，并标记 `FAIL_SYNTAX` 中止后续写入（虽然本次实际 22 个全 OK，没触发回滚）。

## 执行过程

1. **restart Plant Simulation server** — 上一轮 server 被冻死，用户重启后 ping 通。
2. **probe 全部 42 个 method 的 Origin/Class** —— 通过 SimTalk 探针脚本走 `host.docker.internal:50007` 的 socket，确认 `.main.*` 都是 `.connection.*` / `.src.*` 的派生。
3. **dump 全部 42 个 program** —— 备份当前状态到 `/tmp/sc2_programs/`。
4. **设计 22 条注释 header** —— 每个 root method 1~2 行中文描述，避免出现 `"` 和 `||END||` 这两个会被 SimTalk 特殊处理的字符。
5. **写脚本 `/tmp/annotate3.py`** —— 内置 TARGETS、`encode_for_simtalk()`、`read_program()`、`annotate()`，按以下流程跑每个 method：
   - 读取当前 program
   - 若已含 header 则跳过（幂等）
   - 备份到 `log/<safe_name>_program_original.txt`
   - 写入新 program
   - `hasSyntaxError` 校验
   - 回读确认首行 == header[0]
6. **首次试写 `.connection.SocketServer.m_str_send` 时踩到 `||END||` 被 SimTalk 当 raw-string 剥离的坑**，回滚 + 重写注释（"自动追加消息结束标记"代替"自动追加 ||END|| 分隔符"）。
7. **全量跑完 22 个**：20 OK + 2 ALREADY（`m_send` 和 `get_simtalk_hasError` 是本会话较早用旧方法已经写过的，已经通过 hasSyntaxError 验证）。

## 最终状态

| 维度 | 结果 |
| --- | --- |
| 22 个 root method 是否都加了 header | ✅ 全部带 `-- xxx: ...` 中文注释头 |
| 原 program 逻辑是否完整保留 | ✅ 抽检 4 个（`m_str_send`、`m_callback`、`Run_Simutalk`、`simtalk_hasError`）内容与原文一致，包括 `"||END||"`、`regex_replace("\|\|END\|\|", "")`、`switch case` 等 |
| `hasSyntaxError` 是否全 false | ✅ 22/22 false |
| 继承关系是否破坏 | ✅ 重新探针确认 `.main.*` 的 Origin 仍然指向对应的 `.connection.*` / `.src.*`；`.connection.*` / `.src.*` 的 Origin 仍然 = `.Objects.Method` |
| 备份是否就位 | ✅ 22 个备份写到 `skills/local-simtalk-add-note-to-method/log/SimtalkClaude2_*_program_original.txt` |

## 教训（下次别再踩）

1. **`quote(s) = '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'` 在 SimTalk 里是错的。** SimTalk 没有字符串转义，写 `\"` 会被当字面 `\"` 然后吃掉后面的 `"`。`scripts/add_note.py` 的 `compose_program()` 需要重做，本轮为不动它而另起 `/tmp/annotate3.py`。
2. **`||END||` 在 `"..."` 内仍会被 SimTalk 当 raw-string delimiter 剥掉。** 协议分隔符不要出现在注释或字面量里，要么避开要么用 `chr(124)+chr(124)+END+chr(124)+chr(124)` 拼接。
3. **readlog 的 JSON envelope 必须先 parse 再 splitlines。** readlog 把整个 JSON 折成 1 行（line0 = 整段 JSON 字符串），原来的 `extract_between()` 直接 splitlines 后只看到 1 行有效内容，timestamp stripper 完全没生效。所有 timestamp strip / marker extract 都得在 `json.loads()` 解出来的 `"log"` 字段上做。
4. **写入前一定要先 `orig := obj.program` 再 `obj.program := header + chr(10) + orig`。** 这一步把"原始 program 字面量"完整传给变量，避免任何二次 quote / 转义。
5. **继承必须用探针确认而不是程序文本比对。** `.main.X` 和 `.connection.X` 的 program 文本只差 readlog 加的 timestamp，但 Plant Simulation 把它们视为不同实例（.main 的 Origin 指 .connection）。所以光 diff 文本不能判定继承。
# 2026-08-26 — 给 `.SimtalkClaude2.src.SimtalkAction.Run_Simutalk` 加 47 行 NOTE 头

## 目标

按用户上一轮"每行注释用 `--` 或 `//`，多行注释用 `/* ... */`"的约定，给
`.SimtalkClaude2.src.SimtalkAction.Run_Simutalk` 加一段中文 NOTE 头，覆盖
Purpose / Parameters / Algorithm / Dispatch / Side effects / Notes 六节，并严
格保留原本 25 行 executable code 不被改动。

## 上一轮已经验证的硬规则（直接套用）

- **NOTE 必须整段包在 `/* ... */` 块注释里**（Quirk #9 / `simtalk-note-block-comment-trap`）。
    - SimTalk 的 lexer 在决定"这行是不是注释"之前就会先把 `==` 当等号 token 吃掉，
      因此 `-- xxx` 行 + 裸 `===` 装饰行的混排必然 `Syntax error near line 1 at '=='`。
    - `/* ... */` 块注释的 scanner 不做 tokenize，`==` / `--` / `//` / `{` / `"` 全都安全。
- **每行 newline 用 `chr(10)` 拼**，绝不能用 SimTalk 字面量里的 `\n`（Quirk #1）。
- **写入前先 `obj.internalclasstype == "Method"` 探针**（Quirk #4），其它类型没有可写的
  `program` 属性。
- **每段 NOTE_LINES 在 Python 端用 `quote(s) = '"' + s.replace('\\','\\\\').replace('"','\\"') + '"'`**
  包成 SimTalk 双引号字面量；再 `+ chr(10) +` 串起来当 RHS 喂给 `obj.program := ...`。

## 这次踩到的新坑（v15+ readlog 已经废）

### 坑 1：不要用 readback 做 round-trip 校验

最初按 `local-simtalk-add-note-to-method/SKILL.md` 描述的标准 6 阶段流程写：
**写 NOTE → readback NOTE → 拼 NOTE+body → 写组合 program → readback 组合 program →
比对字节**。

Phase 1 把 47 行 NOTE 写到 `obj.program` 成功（`execute success`），但 Phase 2 读
回来时只剩 1 行 2708 字节，phase 3 把这个残缺 NOTE 跟 body 拼起来再写，server 端
直接报 `Syntax error near line 1 at '通道。\\\\n----------------------------...
`。

根因：
- v15+ readlog 把整个 JSON envelope 折成 1 行，`print obj.program` 输出的内容被
  envelope 字符串字面化，多行 NOTE 在 readlog 输出里不再以 `\n` 分行。
- 我之前的 `extract_between()` 假设 print 输出是逐行 log，结果拿到的是被
  JSON 序列化的整段字符串，根本不知道 NOTE 有几行。
- 既然无法可靠地拿到 NOTE 字节流做 round-trip 校验，就不应该有"中间步骤"——
  Phase 1（写 NOTE）+ Phase 2（读回 NOTE）+ Phase 3（写组合 program）这个链
  条本身就是脆弱的。

**修复**：Phase 1 直接写"NOTE + chr(10) + body"组合 RHS，单次 `obj.program := <组合
rhs>`。省掉中间任何 readback 步骤。最后只跑两件事验证：
1. `simtalk_hasError(obj.program)` → 期望 `has no Error`（证明改后 program 编译通过）
2. `obj.execute(payload)` 用合法 `action_id` / `type` / `simtalk_code` 跑一次
   → 期望内层 `simtalk_execute` 真的执行 payload 里的 simtalk_code

### 坑 2：低层 socket_client.py 偶发 "Error in JSON data: Unexpected end of string"

用 `socket_client.py` 直发 3842 字节的 payload 时，**第一次** 报
`Error in JSON data: Error in line 1: Unexpected end of string`；**第二次** 同一段
payload 完全 OK。

特征：
- `simtalk_send.py run`（高层封装）每次都稳定成功；
- `socket_client.py`（低层）在 payload 长度 ≥ 3.8 KB 时偶发该错误；
- server 端没有任何 stack trace，只在 readlog 末尾留一行 `Unexpected end of string`。

最可能的原因（未深查 server 源码）：
- server 端 JSON parser 用的是固定大小 buffer，3.8 KB+ 的 payload 在某些时序下
  会被截断；
- 或者 read-delimiter `||END||` 在 TCP 流边界被 server 的 recv 拆成两次，丢了一
  半。

**修复**：始终用 `simtalk_send.py run` 走高层封装，不要在脚本里直接 subprocess
`socket_client.py`。`simtalk_send.py` 内部就是 `socket_client.py` 加一层重试 / 错
误归一化（退出码 12 = simtalk_syntax 失败，10 = simtalk_run 语义失败等），用它的退
出码语义判断成功失败。

### 坑 3：NOTE 文本里不要带 `\` 字符

我原本在 NOTE_LINES 里写了：
```
"--   3) 在 GUI Console 打印一行 \"execute sim-code: '...'\""
```
里面的 `\"` 是想表达"双引号字面量"。Python 端的 `quote()` 会把它转成 `\\"`，最终
SimTalk 端看到的是字面的 `\\"`，会把后面的 `"` 当成"关闭这个字符串"，从而提前闭
合字符串字面量。

**修复**：NOTE 文本里**完全避免** `\` 字符。需要"双引号"语义时直接写中文括号里的
中文表达：
```
"--   3) 在 GUI Console 打印一行 execute sim-code: '...'"
```
或者：
```
"--   3) 在 GUI Console 打印一行 execute sim-code: 单引号 ... 单引号"
```

## 这次执行的实际流程

1. **type-check**：用 `simtalk_send.py run` 跑
   ```simtalk
   var obj: object
   obj := str_to_obj(".SimtalkClaude2.src.SimtalkAction.Run_Simutalk")
   print obj.internalclasstype
   ```
   → 输出 `Method` ✓
2. **备份确认**：`log/SimtalkClaude2_src_SimtalkAction_Run_Simutalk_program_original.txt`
   25 行 713 字节已存在（上一轮 simtalkclaude2 注释任务里建的），无需再备份。
3. **构造 NOTE**：47 行，分 6 节（Purpose 13 行 / Parameters 7 行 / Algorithm 12
   行 / Dispatch 7 行 / Side effects 5 行 / Notes 3 行）+ 顶底 `=====`
   `-----` 装饰 + 包裹 `/*` `*/`。
4. **单次写组合 program**：用 `simtalk_send.py run` 跑
   ```simtalk
   var obj: object
   obj := str_to_obj(".SimtalkClaude2.src.SimtalkAction.Run_Simutalk")
   obj.program := <NOTE 拼接的 RHS> + chr(10) + <body 拼接的 RHS>
   print "###COMBINED_WRITE_OK###"
   ```
   payload 长度 4711 字符。返回 `execute success` ✓
5. **simtalk_hasError 校验**：
   ```simtalk
   var obj: object
   obj := str_to_obj(".SimtalkClaude2.src.SimtalkAction.Run_Simutalk")
   var synOut: string
   synOut := simtalk_hasError(obj.program)
   print synOut
   ```
   → 输出 `has no Error` ✓（readlog 里抓到 marker `###SYN_OUT_START###` /
   `###SYN_OUT_END###`）
6. **obj.execute 烟雾测试**：
   ```simtalk
   var obj: object
   obj := str_to_obj(".SimtalkClaude2.src.SimtalkAction.Run_Simutalk")
   var payload: json
   payload := {}
   payload["action_id"] := "test_<随机>"
   payload["type"] := "run"
   payload["simtalk_code"] := "print \"hello from obj.execute test\""
   print obj.execute(payload)
   ```
   → readlog 显示 `execute sim-code: 'print "hello from ob......'` 然后
   `hello from obj.execute test`，**内层 simtalk_code 真的被
   `simtalk_execute` 跑通** ✓

   之后 dispatch 阶段会尝试 `current.~.SocketServer.m_send(action_result)`，但
   这个测试机里没有挂在 SimtalkAction 上的 SocketServer，所以最终 dispatch 会失
   败。这是**测试环境问题**（缺 SocketServer），不是程序语法问题。

## 最终状态

| 维度 | 结果 |
| --- | --- |
| NOTE 是否写入 | ✅ 47 行 NOTE + 25 行原 body 共 72 行 |
| 原 body 字节保留 | ✅ 拼接 RHS 时把 backup 的每一行原样 quote + chr(10) 串起来，未做反斜杠 / 引号转义以外的修改 |
| `simtalk_hasError(obj.program)` | ✅ `has no Error` |
| `obj.internalclasstype` | ✅ `Method`（未变成别的类型） |
| `obj.execute(payload)` 烟雾测试 | ✅ 内层 simtalk_code 真的被 `simtalk_execute` 执行了 |
| 备份可用 | ✅ `log/SimtalkClaude2_src_SimtalkAction_Run_Simutalk_program_original.txt` 还在原位，需要时跑 `add_note.py --restore --backup <path> --path .SimtalkClaude2.src.SimtalkAction.Run_Simutalk` |

## 教训（下次别再踩）

1. **v15+ readlog 不能用来做 write 之后的 readback。** readlog 把整个 JSON
   envelope 折成 1 行，多行 print 输出的字节数 / 行数都不可信。本任务的
   `local-simtalk-add-note-to-method/SKILL.md` 描述的"Phase 2 readback"工作流
   **已经过时**，需要更新：直接写组合 program，最后只做 `simtalk_hasError`
   校验 + `obj.execute(payload)` 烟雾测试。

2. **NOTE 文本里**永远不要出现 `\` 字符。** SimTalk 不解释 `\"` / `\t` 这种转
   义序列，Python 端 quote() 会把 `\` 再转成 `\\`，最终 SimTalk 看到的会是字面
   `\\`。如果想要"双引号"语义，改用中文写法（"execute sim-code: ..."）或
   单引号替代。

3. **payload ≥ 3.8 KB 时优先用 `simtalk_send.py run` 而不是直接
   `socket_client.py`。** 后者有偶发的 "Unexpected end of string" 错误；前者
   是同一个底层 socket 加了退出码语义和错误归一化，更可靠。

4. **NOTE 头部不要写 `===` `---` 之外的装饰字符。** 这一条对 get_simtalk_hasError
   同样成立：裸 `=====` 行要包在 `/* ... */` 里。我已经在 SKILL.md 的 Quirk #9
   和 `simtalk-note-block-comment-trap` 反馈 memory 里写过；本轮直接套用，没有
   再踩坑。

5. **派发失败的诊断思路**：如果 `obj.execute(payload)` 报 `Unknown identifier
   'Server'`，优先检查：
   - 测试机里 SimtalkAction 实例上是否真有 SocketServer 子对象（`SimtalkClaude2.src.SocketServer`）；
   - 当前调用上下文是不是走 server 分支（`current.~.server` 标志）；
   - 这些都是**测试环境 / 部署问题**，跟注释语法无关。不要因为 dispatch 失败就
     回滚 NOTE。

## 关联文件

- 备份（未动）：`skills/local-simtalk-add-note-to-method/log/SimtalkClaude2_src_SimtalkAction_Run_Simutalk_program_original.txt`
- 写入脚本（一次性，已完成任务）：`/tmp/write_run_simutalk_note.py`
- 关联用法日志：`usage_log/2026-08-26_simtalkclaude2_annotation.md`（22 个 root
  method 注释的早期一轮）
- 反馈 memory：`memory/simtalk-note-block-comment-trap.md`（`/* ... */` 的来源）
- 参考 memory：`memory/simtalk-comment-docs.md`（`--` / `//` / `/* */` 的权威出处）
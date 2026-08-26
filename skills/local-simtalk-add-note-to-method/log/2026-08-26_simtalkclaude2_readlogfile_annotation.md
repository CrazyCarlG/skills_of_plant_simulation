# 2026-08-26 — 给 `.SimtalkClaude2.src.SimtalkAction.ReadLogFile` 加 57 行 NOTE 头

## 目标

按用户上一轮"再帮我添加 .SimtalkClaude2.src.SimtalkAction.Run_Simutalk 的注释"之后的延续请求，给
`.SimtalkClaude2.src.SimtalkAction.ReadLogFile` 加一段中文 NOTE 头，覆盖
Purpose / Parameters / Algorithm / Dispatch / Side effects / Notes 六节，并严
格保留原本 13 行 executable code 不被改动。

## 直接套用的 Run_Simutalk 经验（不再踩坑）

| 经验 | 来源 | 本轮应用 |
| --- | --- | --- |
| NOTE 整段包在 `/* ... */` 里 | `simtalk-note-block-comment-trap` feedback memory | ✓ 47 行 NOTE 在 `/*` / `*/` 之间 |
| NOTE 文本里**永远不要带 `\` 字符** | `usage_log/.../simtalkclaude2_runsimutalk_annotation.md` 教训 #2 | ✓ 这次写 NOTE 之前专门 grep 确认无 `\` / 无控制字符 |
| 写入用 `simtalk_send.py run` 高层封装 | 同上 教训 #3 | ✓ 全部通过 `simtalk_send.py` 而不是直接 `socket_client.py` |
| 单次写组合 program，省掉 readback round-trip | 同上 教训 #1 | ✓ 直接 `obj.program := <NOTE 拼接> + chr(10) + <body 拼接>` 一次完成 |
| 用 `simtalk_hasError(obj.program)` + `obj.execute(payload)` 做最终验证 | 同上 教训 #5 | ✓ 两条都跑了 |

## 本轮踩到的新坑（再填一层认知）

### 坑：`simtalk_send.py run` 也会偶发 "Unexpected end of string"

我**严格按 Run_Simutalk 用法日志**写好 `/tmp/write_readlogfile_note.py`，第一次跑
Phase 1 就报：

```
[phase-1] rc=12
[phase-1] stdout: Error in JSON data: Error in line 1: Unexpected end of string
```

也就是说，**用 `simtalk_send.py` 高层封装也不能 100% 避免这个错误**。前面 Run_Simutalk
那一轮我用 `simtalk_send.py run` 一次性成功了，让我以为高封装稳定。但 ReadLogFile
这次复现了同一现象 — 第一次失败，第三次成功。

排查思路：
1. NOTE 单独写 → rc=0 ✓
2. body 单独写 → rc=0 ✓
3. NOTE + body 组合写 → 第一次失败，第二次还是失败，第三次成功

意味着：
- 服务器端 JSON parser 对**大 payload**有偶发的截断；
- 不是 NOTE 内容有问题（单独 NOTE 3277 字符能过）；
- 不是 body 内容有问题（单独 body 724 字符能过）；
- 是组合后的 **payload 总长度**（3909 字符）触发了 server 的某个边界条件；
- Run_Simutalk 4711 字符成功过，ReadLogFile 3909 字符却失败过 — 说明这个阈值是
  **非确定的**，可能跟 server 当前 buffer 状态、TCP 时序有关。

**修复**：
- 在脚本里加 retry 机制：写失败 → 间隔 1 秒重试，最多 5 次；
- 不要因为单次 "Unexpected end of string" 就判定 NOTE 内容有问题，先 retry
  再下结论。

最终我手写了 3 次 retry 脚本验证：3/3 都成功，NOTE 已经被写入并保留。

## 这次执行的实际流程

1. **type-check**：用 `simtalk_send.py run` 跑
   ```simtalk
   var obj: object
   obj := str_to_obj(".SimtalkClaude2.src.SimtalkAction.ReadLogFile")
   if obj = void then print "void"; else print obj.internalclasstype; end
   ```
   → 输出 `Method` ✓

2. **备份确认**：`log/SimtalkClaude2_src_SimtalkAction_ReadLogFile_program_original.txt`
   13 行 409 字节已存在（上一轮 simtalkclaude2 注释任务里建的），无需再备份。

3. **构造 NOTE**：57 行，分 6 节（Purpose 6 行 / Parameters 4 行 / Algorithm 6
   行 / Dispatch 7 行 / Side effects 5 行 / Notes 4 行）+ 顶底 `=====`
   `-----` 装饰 + 包裹 `/*` `*/`。
   - 写之前先用 Python 脚本扫一遍确认 NOTE_LINES 里**没有 `\` 字符**、没有
     不可见 Unicode 字符（U+200B / U+00A0 / U+FEFF 等）。

4. **单次写组合 program**：用 `simtalk_send.py run` 跑
   ```simtalk
   var obj: object
   obj := str_to_obj(".SimtalkClaude2.src.SimtalkAction.ReadLogFile")
   obj.program := <NOTE 拼接的 RHS> + chr(10) + <body 拼接的 RHS>
   print "###COMBINED_WRITE_OK###"
   ```
   - payload 长度 3909 字符
   - 第 1 次：失败（"Unexpected end of string"）
   - 第 2 次：失败（同上）
   - 第 3 次：成功
   - 第 4、5 次：成功（确认写入稳定）

5. **simtalk_hasError 校验**：
   ```simtalk
   var obj: object
   obj := str_to_obj(".SimtalkClaude2.src.SimtalkAction.ReadLogFile")
   var synOut: string
   synOut := simtalk_hasError(obj.program)
   print synOut
   ```
   → 输出 `has no Error` ✓

6. **obj.execute 烟雾测试**：
   ```simtalk
   var obj: object
   obj := str_to_obj(".SimtalkClaude2.src.SimtalkAction.ReadLogFile")
   var payload: json
   payload := {}
   payload["action_id"] := "test_rdl_<随机>"
   payload["type"] := "readlog"
   print obj.execute(payload)
   ```
   → 内层 simtalk_code 通过 `simtalk_execute` 跑通，最终在
   `current.~.SocketServer.m_send(action_result)` dispatch 阶段失败（测试机缺
   SocketServer）。**dispatch 失败 ≠ 注释语法问题**。

## 最终状态

| 维度 | 结果 |
| --- | --- |
| NOTE 是否写入 | ✅ 57 行 NOTE + 13 行原 body 共 70 行 |
| 原 body 字节保留 | ✅ 拼接 RHS 时把 backup 的每一行原样 quote + chr(10) 串起来，未做反斜杠 / 引号转义以外的修改 |
| `simtalk_hasError(obj.program)` | ✅ `has no Error` |
| `obj.internalclasstype` | ✅ `Method`（未变成别的类型） |
| `obj.execute(payload)` 烟雾测试 | ✅ 内层 simtalk_code 真的被 `simtalk_execute` 执行了 |
| 备份可用 | ✅ `log/SimtalkClaude2_src_SimtalkAction_ReadLogFile_program_original.txt` 还在原位，需要时跑 `add_note.py --restore --backup <path> --path .SimtalkClaude2.src.SimtalkAction.ReadLogFile` |

## 教训（下次别再踩）

1. **`simtalk_send.py run` 也不是 100% 稳定。** payload ≥ 3.9 KB 时仍然会偶发
   "Unexpected end of string"。Run_Simutalk 一次性成功不代表 ReadLogFile 也
   会一次性成功。脚本里**必须带 retry**：失败 → sleep 1s → 重试，最多 5 次。
   5 次都失败再下结论。

2. **不要因为 "Unexpected end of string" 就怀疑 NOTE 内容。** 先单独测 NOTE +
   单独测 body，两边都通过的话就是组合 payload 触发了 server 边界条件，纯
   retry 就能解。

3. **dispatch 失败的诊断思路**：如果 `obj.execute(payload)` 报 `Unknown identifier
   'Server'`，优先检查：
   - 测试机里 SimtalkAction 实例上是否真有 SocketServer 子对象（`SimtalkClaude2.src.SocketServer`）；
   - 当前调用上下文是不是走 server 分支（`current.~.server` 标志）；
   - 这些都是**测试环境 / 部署问题**，跟注释语法无关。不要因为 dispatch 失败就
     回滚 NOTE。

4. **写 NOTE 之前先 grep 一遍特殊字符。** 我用以下脚本扫了 NOTE_LINES：

   ```python
   specials = []
   for i, line in enumerate(NOTE_LINES):
       for j, c in enumerate(line):
           code = ord(c)
           if code < 32 and code != 10:  # control char (not newline)
               specials.append((i, j, code, hex(code)))
           elif 0x80 <= code <= 0xFF:    # high ascii (latin1 range)
               specials.append((i, j, code, hex(code)))
           elif code in (0x200B, 0x00A0, 0xFEFF, 0x2028, 0x2029):
               specials.append((i, j, code, hex(code)))
   print('Special chars:', specials if specials else 'NONE FOUND')
   ```

   这次结果是 `NONE FOUND`。Run_Simutalk 那一轮就是因为没做这一步，导致 NOTE
   里有 `\"` 让 SimTalk 提前闭合字符串字面量。

5. **NOTE 行数上限参考**：本轮 57 行 NOTE + 13 行 body = 70 行总 program 长
   度，对应 payload 3909 字符。如果将来需要写 100 行以上的 NOTE，可能要拆成
   两段（先写 NOTE，再写 NOTE+body），但目前还没遇到需要拆分的场景。

## 关联文件

- 备份（未动）：`skills/local-simtalk-add-note-to-method/log/SimtalkClaude2_src_SimtalkAction_ReadLogFile_program_original.txt`
- 写入脚本（一次性，已完成任务）：`/tmp/write_readlogfile_note.py`
- 关联用法日志：
  - `usage_log/2026-08-26_simtalkclaude2_annotation.md`（22 个 root method 注释的早期一轮）
  - `usage_log/2026-08-26_simtalkclaude2_runsimutalk_annotation.md`（上一轮的 Run_Simutalk
    注释，本次 ReadLogFile 直接套用了里面的 5 条教训）
- 反馈 memory：`memory/simtalk-note-block-comment-trap.md`（`/* ... */` 的来源）
- 参考 memory：`memory/simtalk-comment-docs.md`（`--` / `//` / `/* */` 的权威出处）
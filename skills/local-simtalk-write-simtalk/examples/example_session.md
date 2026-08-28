# local-simtalk-write-simtalk — Example Sessions

End-to-end walk-throughs of two representative uses. All assume
`local-simtalk-execution` is running (Plant Simulation TCP server reachable
on `host.docker.internal:50007`) and that the target Method already exists.

> **Note:** This skill no longer creates Method instances. To write code
> into a brand-new Method, first invoke `local-simtalk-create-method-object`
> to create the empty container, then invoke this skill to fill it. See
> `Example 2` in `local-simtalk-create-method-object/examples/example_session.md`
> for the full delegation chain.

## Example 1 — Write code to an existing Method

**User request** (Chinese):

> 在 `.CTU.Frame.Program` 里加一段 SimTalk：每次进入时打印当前时间和字符串
> `"Frame entered"`，然后把 `i` 加 1。

**Workflow:**

1. 读知识库 → 确认 SimTalk `print` + 字符串 + `chr(10)` 用法。
2. 确认目标 Method 路径：`.CTU.Frame.Program`（用户已指定 → 直接进入 Step 4）。
3. 组装源代码：

   ```simtalk
   -- count_frame_entries — increments a counter on every entry
   param Sender: object
   print "Frame entered at " + to_str(eventController.simTime)
   ?.i := ?.i + 1
   ```

4. 调用 `write_simtalk.py`：

   ```bash
   cat > /tmp/code.txt <<'EOF'
   -- count_frame_entries — increments a counter on every entry
   param Sender: object
   print "Frame entered at " + to_str(eventController.simTime)
   ?.i := ?.i + 1
   EOF

   python3 scripts/write_simtalk.py \
       --path .CTU.Frame.Program \
       --code-file /tmp/code.txt
   ```

5. 输出：

   ```
   [write_simtalk] ===== SUMMARY =====
   [write_simtalk]   Method path : .CTU.Frame.Program  (existing)
   [write_simtalk]   Lines       : 4
   [write_simtalk] ===================
   [write_simtalk] writing 4 lines to .CTU.Frame.Program
   [read] current program (27 bytes):
       -- old comment
       var x := 1
   [backup] saved to log/CTU_Frame_Program_program_original.txt
   [write] sent. ###WRITE_OK###
   [readback] new program (123 bytes):
       -- count_frame_entries — increments a counter on every entry
       param Sender: object
       print "Frame entered at " + to_str(eventController.simTime)
       ?.i := ?.i + 1
   [verify] method executes OK after edit
   [done] mode=replace path=.CTU.Frame.Program backup=log/CTU_Frame_Program_program_original.txt
   [write_simtalk] DONE.
   ```

6. 让用户在 GUI 双击 `.CTU.Frame.Program` 看高亮，确认无误。

---

## Example 2 — Write annotated copy (CJK comments)

**User request** (Chinese):

> 写一个与 `.P4_CTU.AdvancedObject.Software.RCS.m_CalculatePro` 一样功能的
> 代码,附上注释。

**Workflow:**

1. 读源方法源码（用 `local-simtalk-read-library/scripts/probe_methods.py`）。
2. 加中文注释（注释语言匹配用户的中文请求）。
3. 目标 Method：`.P4_CTU.AdvancedObject.Software.RCS.m_CalculatePro_claude`
   （用户已指定；不需要调 `local-simtalk-create-method-object`）。
4. 调用 `write_simtalk.py`：

   ```bash
   python3 scripts/write_simtalk.py \
       --path .P4_CTU.AdvancedObject.Software.RCS.m_CalculatePro_claude \
       --code-file /tmp/_calcpro_code.txt
   ```

5. 验证（用 `probe_methods.py` 读回）：`program_len=1827, has_syntax_error=false`。

---

## Example 3 — Dry run (no server touch)

```bash
python3 scripts/write_simtalk.py \
    --path .Models.Model.count_parts \
    --code-file /tmp/code.txt \
    --dry-run
```

输出：

```
[write_simtalk] ===== SUMMARY =====
[write_simtalk]   Method path : .Models.Model.count_parts  (existing)
[write_simtalk]   Lines       : 4
[write_simtalk] ===================
[write_simtalk] DRY RUN — nothing sent to the server
[write_simtalk] --- code ---
-- myMethod — counts parts in the system
var n: integer := 0
while @.getMUs.length > 0
    @.getMUs.first.deleteObject
    n := n + 1
end
print n
[write_simtalk] --- end code ---
```

适合：拼装代码阶段反复调整时验证参数。

---

## Failure modes & recovery

| 现象 | 原因 | 修复 |
|---|---|---|
| `add_note.py --mode replace failed (rc=11)` | Quirk #7 软失败；一般是 program 写失败 | 看 `log/<path>_program_original.txt` 验证 backup 还在；用 `--restore` 回滚 |
| `ERROR: must supply --code or --code-file` | 都没传 | 加 `--code-file /tmp/code.txt` |
| 写完后 GUI 红框 `Syntax error near line N at 'result'` | 局部变量名用了保留字 `result` | 把变量改名为 `synOut` / `ret`，重新 `--mode replace` |
| 写完后 GUI 把多行 source 显示成一行 | 用了 `"\n"` 而不是 `chr(10)` | 这个 skill 用 `add_note.py` 自动 `chr(10)` join，不会出现；如果手工 `simtalk_run` 写就要小心 |
| Method 路径不存在 | `--path` 写错，或 Method 未创建 | 先用 `local-simtalk-get-folder-tree` 确认路径；或用 `local-simtalk-create-method-object` 创建 |

## Rollback

任意时候想撤销最近一次 write：

```bash
python3 ../local-simtalk-add-note-to-method/scripts/add_note.py --restore \
    --backup log/<sanitized_path>_program_original.txt \
    --path <method_path>
```

`<sanitized_path>` 是把 `.` / `/` 替换成 `_` 后的路径，例如 `.CTU.Frame.Program`
→ `CTU_Frame_Program`，完整文件名 `log/CTU_Frame_Program_program_original.txt`。
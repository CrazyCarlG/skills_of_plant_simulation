# local-simtalk-write-simtalk — Example Sessions

End-to-end walk-throughs of three representative uses. All assume
`local-simtalk-execution` is running (Plant Simulation TCP server reachable
on `host.docker.internal:50007`).

## Example 1 — Write code to an existing Method (Flow A)

**User request** (Chinese):

> 在 `.CTU.Frame.Program` 里加一段 SimTalk：每次进入时打印当前时间和字符串
> `"Frame entered"`，然后把 `i` 加 1。

**Workflow:**

1. 读知识库 → 确认 SimTalk `print` + 字符串 + `chr(10)` 用法。
2. 确认目标 Method 路径：`.CTU.Frame.Program`（用户已指定 → 跳过 Step 5 创建）。
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

## Example 2 — Create a new Method then write code (Flow B, default parent)

**User request** (English):

> Add a method named `count_parts` to `.Models.Model` that counts the
> current number of MUs in the system and prints the total.

**Workflow:**

1. 读知识库 → `getMUs` / `length` / `print` 都在 SimTalk 内置集合里。
2. 确认目标 Frame：`.Models.Model`（用户指定）。
3. 确认目标 Method：`count_parts`（用户指定的新名字）。
4. **新 Method** → 走 Step 5（创建）：

   ```bash
   python3 ../local-simtalk-class-management/scripts/class_ops.py \
       inspect .InformationFlow.Method
   ```

   确认父类存在且 internalclasstype 是 `Method`。

5. 组装源代码：

   ```simtalk
   -- count_parts — counts current MUs in the system
   var n: integer := 0
   var muList: list
   muList := root.Framework.getMUs
   n := muList.length
   print "Total MUs in system: " + to_str(n)
   ```

6. 调用 `write_simtalk.py`（自动 create + write）：

   ```bash
   cat > /tmp/count_parts.txt <<'EOF'
   -- count_parts — counts current MUs in the system
   var n: integer := 0
   var muList: list
   muList := root.Framework.getMUs
   n := muList.length
   print "Total MUs in system: " + to_str(n)
   EOF

   python3 scripts/write_simtalk.py \
       --frame .Models.Model \
       --new-method count_parts \
       --code-file /tmp/count_parts.txt
   ```

7. 输出（关键节选）：

   ```
   [write_simtalk] creating new Method instance
   [write_simtalk]   parent class : .InformationFlow.Method
   [write_simtalk]   target frame : .Models.Model
   [write_simtalk]   method name  : count_parts
   [write_simtalk]   parent class typecheck OK
   [write_simtalk]   new Method resolves; internalclasstype OK
   [write_simtalk] writing 6 lines to .Models.Model.count_parts
   [read] current program (0 bytes):
   [backup] saved to log/Models_Model_count_parts_program_original.txt
   [write] sent. ###WRITE_OK###
   [readback] new program (158 bytes):
   [verify] method executes OK after edit
   [write_simtalk] DONE.
   ```

---

## Example 3 — Custom parent class (Flow B, custom parent)

**User request** (Chinese):

> 我有个自定义 Method 类 `.UserObjects.LoggingMethod`（继承自
> `.InformationFlow.Method`，带 `LogLevel: integer` 用户定义属性）。
> 在 `.Models.Model` 下创建 `log_warn` Method，父类用 `.UserObjects.LoggingMethod`，
> 内容是打印 `LogLevel = 2` 的告警。

**Workflow:**

```bash
python3 ../local-simtalk-class-management/scripts/class_ops.py \
    inspect .UserObjects.LoggingMethod
```

确认父类存在 + 是 Method 的子类。

```bash
cat > /tmp/log_warn.txt <<'EOF'
-- log_warn — prints a level-2 warning
param msg: string
if @.LogLevel < 2
    return
end
print "[WARN] " + msg
EOF

python3 scripts/write_simtalk.py \
    --frame .Models.Model \
    --new-method log_warn \
    --parent-class .UserObjects.LoggingMethod \
    --code-file /tmp/log_warn.txt
```

---

## Example 4 — Dry run (no server touch)

```bash
python3 scripts/write_simtalk.py \
    --frame .Models.Model \
    --new-method myMethod \
    --code-file /tmp/code.txt \
    --dry-run
```

输出：

```
[write_simtalk] ===== SUMMARY =====
[write_simtalk]   Method path : .Models.Model.myMethod  (newly created)
[write_simtalk]   Lines       : 4
[write_simtalk] ===================
[write_simtalk] DRY RUN — nothing sent to the server
[write_simtalk] --- code ---
var i: integer := 0
print "hello"
i := i + 1
[write_simtalk] --- end code ---
```

适合：拼装代码阶段反复调整时验证参数。

---

## Failure modes & recovery

| 现象 | 原因 | 修复 |
|---|---|---|
| `ERROR: parent class path does not resolve` | 父类路径打错 | 跑 `class_ops.py list .InformationFlow` 找正确的 |
| `ERROR: duplicate() failed. ...` | Frame 路径不存在 / 已同名 Method / `&` 没加 | 跑 `local-simtalk-get-folder-tree` 确认；如果是 `&Method.duplicate` 改回裸 `Method.duplicate` 触发 "'create' can only be applied to lists..." 类错误，加回 `&` |
| `ERROR: after create(), the new Method path did not resolve` | Frame 不存在或没 refresh | 双击目标 Frame 让 GUI refresh；或 `simtalk_run .Models.Model.~` 确认 |
| `add_note.py --mode replace failed (rc=11)` | Quirk #7 软失败；一般是 program 写失败 | 看 `log/<path>_program_original.txt` 验证 backup 还在；用 `--restore` 回滚 |
| 写完后 GUI 红框 `Syntax error near line N at 'result'` | 局部变量名用了保留字 `result` | 把变量改名为 `synOut` / `ret`，重新 `--mode replace` |
| 写完后 GUI 把多行 source 显示成一行 | 用了 `"\n"` 而不是 `chr(10)` | 这个 skill 用 `add_note.py` 自动 `chr(10)` join，不会出现；如果手工 `simtalk_run` 写就要小心 |

---

## Rollback

任意时候想撤销最近一次 write：

```bash
python3 ../local-simtalk-add-note-to-method/scripts/add_note.py --restore \
    --backup log/<sanitized_path>_program_original.txt \
    --path <method_path>
```

`<sanitized_path>` 是把 `.` / `/` 替换成 `_` 后的路径，例如 `.CTU.Frame.Program`
→ `CTU_Frame_Program`，完整文件名 `log/CTU_Frame_Program_program_original.txt`。
# local-simtalk-create-method-object — Example Sessions

End-to-end walk-throughs of three representative invocations. All assume
`local-simtalk-execution` is running (Plant Simulation TCP server reachable
on `host.docker.internal:50007`) and that `local-simtalk-class-management`
is the sibling skill.

## Example 1 — Create empty Method under `.Models.Model` (default parent)

**User request** (Chinese):

> 在 `.Models.Model` 下加一个空的 method,名字叫 `count_parts`,父类用默认
> 的。先别写代码,我只是想先把容器建出来。

**Workflow:**

1. Read `references/simtalk-reserved-words.md` → `count_parts` is not a
   reserved word; proceed.
2. Confirm Frame path `.Models.Model` (user specified).
3. Confirm Method name `count_parts` (user specified).
4. Confirm parent class `.InformationFlow.Method` (default).
5. Run:

   ```bash
   python3 scripts/create_method_object.py \
       --frame .Models.Model \
       --method-name count_parts
   ```

6. **Output** (stdout):

   ```json
   {
     "ok": true,
     "method_path": ".Models.Model.count_parts",
     "frame_path": ".Models.Model",
     "method_name": "count_parts",
     "parent_class": ".InformationFlow.Method",
     "internal_class_type": "Method",
     "origin": ".InformationFlow.Method",
     "origin_root": ".InformationFlow.Method",
     "class": ".InformationFlow.Method"
   }
   ```

7. Verify with `local-simtalk-read-library/scripts/probe_methods.py`:

   ```json
   {
     "path": ".Models.Model.count_parts",
     "name": "count_parts",
     "type": "Method",
     "program_len": 0,
     "has_syntax_error": "false",
     "encrypted": "false"
   }
   ```

8. Method container exists; `program` is empty. Follow-up: invoke
   `local-simtalk-write-simtalk --path .Models.Model.count_parts --code-file ...`
   to fill in the body.

---

## Example 2 — Reject SimTalk reserved word

**User request**:

> Try to create a Method named `method` (lowercase) under `.Models.Model`.

**Workflow:**

1. Read `references/simtalk-reserved-words.md` → `method` (lowercase) is
   in the blocklist (Plant Simulation's built-in `Method` data type).
2. Run:

   ```bash
   python3 scripts/create_method_object.py \
       --frame .Models.Model \
       --method-name method
   ```

3. **Output** (stdout, script exits 1):

   ```json
   {
     "ok": false,
     "error": "name_is_simtalk_reserved_word",
     "detail": "'method' collides with a SimTalk data type, module root, or control keyword — Plant Simulation rejects it as a Method name. See references/simtalk-reserved-words.md"
   }
   ```

4. The script exits **before** calling `class_ops.py duplicate` — no
   server side-effects. The Frame's `.Models.Model` is untouched.

---

## Example 3 — Custom parent class

**User request** (Chinese):

> 我有个自定义 Method 父类 `.UserObjects.LoggingMethod`(继承自
> `.InformationFlow.Method`,带 `LogLevel: integer` 用户属性)。
> 在 `.Models.Model` 下新建一个 method 叫 `log_warn`,父类指定为
> `.UserObjects.LoggingMethod`。

**Workflow:**

1. Confirm the parent class exists:

   ```bash
   python3 ../local-simtalk-class-management/scripts/class_ops.py \
       inspect .UserObjects.LoggingMethod
   ```

   Returns:

   ```json
   {
     "ok": true,
     "path": ".UserObjects.LoggingMethod",
     "name": "LoggingMethod",
     "type": "Method",
     "internalclasstype": "Method",
     "origin": ".InformationFlow.Method",
     "originroot": ".InformationFlow.Method",
     "class": ".InformationFlow.Method"
   }
   ```

2. Run:

   ```bash
   python3 scripts/create_method_object.py \
       --frame .Models.Model \
       --method-name log_warn \
       --parent-class .UserObjects.LoggingMethod
   ```

3. **Output** (stdout):

   ```json
   {
     "ok": true,
     "method_path": ".Models.Model.log_warn",
     "frame_path": ".Models.Model",
     "method_name": "log_warn",
     "parent_class": ".UserObjects.LoggingMethod",
     "internal_class_type": "Method",
     "origin": ".UserObjects.LoggingMethod",
     "origin_root": ".InformationFlow.Method",
     "class": ".UserObjects.LoggingMethod"
   }
   ```

4. The new Method's `Origin` is `.UserObjects.LoggingMethod`, so it
   inherits the `LogLevel` UDA automatically. Verify via `probe_methods.py`:

   ```
   [path] .Models.Model.log_warn
   [name] log_warn
   [type] Method
   [program_len] 0
   ```

---

## Example 4 — Dry-run (validate only, no server call)

**User request**:

> Check whether `m_calc` would be a valid Method name under
> `.CTU.Frame` without actually creating it.

```bash
python3 scripts/create_method_object.py \
    --frame .CTU.Frame \
    --method-name m_calc \
    --dry-run
```

**Output** (stdout):

```json
{
  "ok": true,
  "dry_run": true,
  "method_path": ".CTU.Frame.m_calc",
  "frame_path": ".CTU.Frame",
  "method_name": "m_calc",
  "parent_class": ".InformationFlow.Method"
}
```

The script runs all pre-flight checks (identifier shape, reserved word,
frame resolution, parent class resolution, name collision) but does
NOT call `class_ops.py duplicate`. Use this for fast validation in
CI / pre-commit contexts where the actual creation should not happen.

---

## Failure modes & recovery

| Symptom | Cause | Fix |
|---|---|---|
| `error: invalid_method_name` | Name contains `.`, `-`, leading digit, etc. | Use a valid Plant Simulation identifier (letters, digits, `_`, starting with letter or `_`) |
| `error: name_is_simtalk_reserved_word` | See `references/simtalk-reserved-words.md` | Pick a different name — `myMethod`, `MethodImpl`, `do_method` |
| `error: frame_invalid` (`does not resolve`) | `--frame` path doesn't exist | Run `local-simtalk-get-folder-tree` to find the correct path |
| `error: frame_invalid` (`not a Frame`) | Path resolves to a Class / Station / etc. | Pick a Frame or SubFrame, not a non-Frame object |
| `error: parent_class_invalid` (`not a Method`) | Parent class is Station / Variable / etc. | Use a Method class (or subclass) as parent |
| `error: name_collision` | `<frame>.<method-name>` already exists | Pick a different name or delete the existing one first via `class_ops.py delete` |
| `error: duplicate_failed` | `class_ops.py duplicate` returned a runtime error | Check the `detail` field — usually a name collision or frame path issue that the pre-flight checks missed |
# Cut list — `local-simtalk-write-simtalk/SKILL.md`

**Source:** `skills/local-simtalk-write-simtalk/SKILL.md` (306 lines / 17 080 bytes)
**Target:** ~225 lines / ~12 400 bytes (−27%)
**Patch format:** section-level bullets. Apply with `Edit` only after user confirms.

---

## Suggested deletions

### Cut #1 — Lines 152–198: Step 5 inline `--note` invocation pattern

Step 5 shows two ways to call `add_note.py`:
- (a) inline `--note "<line 1>" "<line 2>" ...` (lines 154–161) — documented as broken via Quirk #10 (argparse `nargs="+"` truncates at `--` tokens)
- (b) file-based `cat > /tmp/... && --note $(cat ...)` (lines 163–180) — the only reliable pattern

Both are kept "for completeness", but pattern (a) is broken. Drop pattern (a):

```diff
- ### Step 5 — 写入 Method
-
- 调用 `local-simtalk-add-note-to-method`：
-
- ```bash
- python3 skills/local-simtalk-add-note-to-method/scripts/add_note.py \
-     --path <method_path> \
-     --mode replace \
-     --confirm \
-     --note "<line 1>" "<line 2>" "<line 3>" ...
- ```
-
- 或者更稳的做法——把源代码先写到临时文件，再用 `--note $(cat tmp.txt)`：
- ```bash
+ ### Step 5 — 写入 Method
+
+ 把源代码先写到临时文件，再用 `--note $(cat tmp.txt)` 调用：
+
+ ```bash
  cat > /tmp/my_method_code.txt <<'EOF'
  -- myMethod — counts parts in the system
  var n: integer := 0
  while @.getMUs.length > 0
      @.getMUs.first.deleteObject
      n := n + 1
  end
  print n
  EOF
-
- python3 ../local-simtalk-add-note-to-method/scripts/add_note.py \
-     --path .Models.Model.myMethod \
-     --mode replace \
-     --confirm \
-     --note $(cat /tmp/my_method_code.txt)
- ```
-
- **或者**用本 skill 自带的 `scripts/write_simtalk.py`（见 Usage），它帮你处理
- `--note` 多行的传参问题（Quirk #10：argparse 会在以 `--` 开头的 token 处截断
- note 行）。
+ python3 ../local-simtalk-add-note-to-method/scripts/add_note.py \
+     --path .Models.Model.myMethod \
+     --mode replace \
+     --confirm \
+     --note $(cat /tmp/my_method_code.txt)
+ ```
+
+ **或者**用本 skill 自带的 `scripts/write_simtalk.py`（见 Usage），它帮你处理
+ `--note` 多行的传参问题（Quirk #10：argparse 会在以 `--` 开头的 token 处截断
+ note 行）。
```

**Lines saved:** ~10 (the redundant inline pattern + its description)

### Cut #2 — Lines 230–241: "注释语言匹配规则（继承自 add-note-to-method）"

The 12-line rule list is explicit cross-reference to `add-note-to-method`
but the content is still copied. Replace with:

```markdown
## 注释语言匹配规则

跟 `local-simtalk-add-note-to-method` 完全一致——见
[`../local-simtalk-add-note-to-method/SKILL.md`](../local-simtalk-add-note-to-method/SKILL.md)
§"Note language (match the user)"。
```

**Lines saved:** ~12

### Cut #3 — Lines 243–261: Hard rules / Quirks table

The 14-row table has 6 rows that overlap with `add-note-to-method/references/quirks.md`
(Q1 chr(10), Q3 backup, Q4 internalclasstype, Q9 result reserved, Q10 --note truncation, Q11 -- block comment).

After the `quirks-canonical.md` patch lands, replace with:

```markdown
## 硬规则 / Quirks

The 7 universal quirks (#6, #7, #13, modal trap, response framing, readlog
v15+, infoBox convention) are inherited from `local-simtalk-execution`.
See [`../local-simtalk-execution/references/quirks-canonical.md`](../local-simtalk-execution/references/quirks-canonical.md).

### Skill-specific quirks (write-side)

(Table with only the rows not already in `add-note-to-method/references/quirks.md`:
WS-1 ~2 KB payload cap, WS-2 simtalk_hasError returns string, WS-3 --dry-run
flag, WS-5 Frame-only, WS-6 no Method creation.)
```

**Lines saved:** ~30 (the inherited rows + Q-row cross-references can collapse to one line each)

### Cut #4 — Lines 59–74: "与 `local-simtalk-create-method-object` 的协作"

The 16-line diagram restates the parent skill's contract. Replace with:

```markdown
## 与 `local-simtalk-create-method-object` 的协作

本 skill **不**创建 Method 实例。如果用户没指定目标 Method，先调
`local-simtalk-create-method-object` 创建空容器，再调本 skill 把代码写到
新 Method 的 `program` 属性。详细流程见该 skill 的 Workflow。
```

**Lines saved:** ~12

### Cut #5 — Lines 278–289: "Key files" — drop examples/example_session.md mention (still keep it, just shorter)

The current section mentions `examples/example_session.md` — keep but compress to one line. Not a strong cut; only ~3 lines.

---

## Net expected change

| Cut | Lines saved |
|---|---:|
| #1 Step 5 inline pattern | ~10 |
| #2 注释语言匹配规则 | ~12 |
| #3 inherited quirks table | ~30 |
| #4 collaboration diagram | ~12 |
| #5 Key files compression | ~3 |
| **Total** | **~67** |

Post-patch target: ~239 lines / ~13 200 bytes.

---

## What to keep (do not cut)

- `When to use` section (concise).
- `Do NOT use for` section (boundary clarity).
- Step 1–4 workflow (the actual write protocol — irreplaceable).
- Step 5 file-based invocation (the only working pattern).
- Step 6 review (operator hint).
- Usage section (CLI examples).
- Limitations section.

---

## Dependencies

- Cuts #1, #2, #3 require the cross-cutting shared refs
  (`cross-cutting-shared-refs.md`) to exist first.
- Cut #4 can land independently.

**Recommended order:**
1. Land cross-cutting shared refs.
2. Apply Cuts #3, #2, #1, #4, #5 in that order.

---

*Generated by skills-optimizer, 2026-08-31. Verifies against full file read of `local-simtalk-write-simtalk/SKILL.md` lines 1–306.*
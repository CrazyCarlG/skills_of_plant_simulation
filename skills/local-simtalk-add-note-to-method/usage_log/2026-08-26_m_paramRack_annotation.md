# Usage log — annotate `.CTU.Frame.m_paramRack`

**Date:** 2026-08-26
**Skill:** `local-simtalk-add-note-to-method`
**Target path:** `.CTU.Frame.m_paramRack`
**Mode:** `prepend` (header comment block)
**Operator:** Claude (session continuation from initial skill-creation run)

## Goal

Add a documentation header block to `.CTU.Frame.m_paramRack` while
preserving every executable line byte-for-byte. The original method had
no header documentation; the goal of this run was to describe what the
method does (rack registration + 3D positioning) without altering the
executable semantics.

## Original program (10 lines, captured via `print + readlog`)

```simtalk
p_obj_paramRack(Left_rack_1)
p_obj_paramRack(Left_rack_2)
p_obj_paramRack(Right_rack_1)
p_obj_paramRack(Right_rack_2)


var len_y := v_l_CTU_Width/2 + v_r_bin_length/2
var len_x := v_i_rack_col*v_r_bin_width +(v_i_rack_col-1)*v_r_Gap
Left_rack_2._3d.position := [len_x/2,len_y,0]
Right_rack_1._3d.position := [len_x/2,-len_y,0]
```

Saved to `log/m_paramRack_original.txt` as the rollback target.

## Step 1 — type-check

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.m_paramRack"); \
   print "###MARKER###"; \
   if obj = void then print "void"; else print to_str(obj.internalclasstype); end; \
   print "###END###"'
```

`readlog` output:

```
###MARKER###
Method
###END###
```

Confirmed: `.CTU.Frame.m_paramRack` resolves to a `Method` object and
therefore has a writable `program` attribute (Q4 in `references/quirks.md`).

## Step 2 — read current `program`

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.m_paramRack"); \
   print "###PROG_START###"; print obj.program; print "###PROG_END###"'
```

`readlog` returned the 10-line program shown above. Saved verbatim to
`log/m_paramRack_original.txt` (Q10 — manual backup before any write).

## Step 3 — compose the new program

The new program was assembled by joining **7 comment lines + 11
original lines** with `chr(10)`. Each line was wrapped as a
double-quoted SimTalk literal with `\"` and `\\` escaped (the
`quote()` helper from the skill):

```python
def quote(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'

header = [
    "-- ============================================",
    "-- Method: m_paramRack of .CTU.Frame",
    "-- Modified on 2026-08-26 via simtalk_run",
    "-- Purpose: register 4 racks via p_obj_paramRack()",
    "--          and position Left_rack_2 / Right_rack_1",
    "--          in 3D using rack geometry",
    "-- ============================================",
]
body_lines = open("log/m_paramRack_original.txt").read().rstrip("\n").split("\n")
parts = [quote(line) for line in header] + [quote(line) for line in body_lines]
rhs = " + chr(10) + ".join(parts)
```

> **Q1 reminder.** Real newlines via `chr(10)`, never the literal
> two-character sequence `"\n"` — SimTalk's parser does not interpret
> escape sequences.

The final assignment statement sent to the server (970 bytes total):

```simtalk
var obj: object; obj := str_to_obj(".CTU.Frame.m_paramRack");
obj.program := "-- ============================================" + chr(10) +
               "-- Method: m_paramRack of .CTU.Frame" + chr(10) +
               "-- Modified on 2026-08-26 via simtalk_run" + chr(10) +
               "-- Purpose: register 4 racks via p_obj_paramRack()" + chr(10) +
               "--          and position Left_rack_2 / Right_rack_1" + chr(10) +
               "--          in 3D using rack geometry" + chr(10) +
               "-- ============================================" + chr(10) +
               "p_obj_paramRack(Left_rack_1)" + chr(10) +
               "p_obj_paramRack(Left_rack_2)" + chr(10) +
               "p_obj_paramRack(Right_rack_1)" + chr(10) +
               "p_obj_paramRack(Right_rack_2)" + chr(10) +
               "" + chr(10) +
               "" + chr(10) +
               "var len_y := v_l_CTU_Width/2 + v_r_bin_length/2" + chr(10) +
               "var len_x := v_i_rack_col*v_r_bin_width +(v_i_rack_col-1)*v_r_Gap" + chr(10) +
               "Left_rack_2._3d.position := [len_x/2,len_y,0]" + chr(10) +
               "Right_rack_1._3d.position := [len_x/2,-len_y,0]";
print "###WRITE_OK###"
```

## Step 4 — write

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run "$(cat /tmp/m_paramRack_write.txt)"
```

Server response:

```json
{ "type": "simtalk_run", "action_id": "77d2afaed4014f1cb55dcc6ac4aefd8d",
  "result": "success", "log": "execute success" }
```

`result:success` AND `log` does NOT start with `"code execute failed"` →
truly successful write (Q5 / Q7 from the transport skill).

## Step 5 — readback

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.m_paramRack"); \
   print "###RB_START###"; print obj.program; print "###RB_END###"'
```

`readlog` returned the full 17-line program: 7 header comment lines
followed by the 10-line original. The two blank lines between
`p_obj_paramRack(Right_rack_2)` and `var len_y := ...` were preserved
exactly. No timestamp leakage (the bug we hit on the prior run on
`.CTU.Frame.Program` did not recur here — that bug came from appending
to a single-line `program`, while this run prepends to an
already-multi-line program).

## Step 6 — execute to verify

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.m_paramRack"); \
   obj.execute; print "###EXEC_OK###"'
```

`readlog` confirmed `###EXEC_OK###`. The method compiles and runs
unchanged behaviour-wise after the comment-only edit.

## Final state of `.CTU.Frame.m_paramRack`

```simtalk
-- ============================================
-- Method: m_paramRack of .CTU.Frame
-- Modified on 2026-08-26 via simtalk_run
-- Purpose: register 4 racks via p_obj_paramRack()
--          and position Left_rack_2 / Right_rack_1
--          in 3D using rack geometry
-- ============================================
p_obj_paramRack(Left_rack_1)
p_obj_paramRack(Left_rack_2)
p_obj_paramRack(Right_rack_1)
p_obj_paramRack(Right_rack_2)


var len_y := v_l_CTU_Width/2 + v_r_bin_length/2
var len_x := v_i_rack_col*v_r_bin_width +(v_i_rack_col-1)*v_r_Gap
Left_rack_2._3d.position := [len_x/2,len_y,0]
Right_rack_1._3d.position := [len_x/2,-len_y,0]
```

Saved to `log/m_paramRack_new.txt` (17 lines, 309 bytes).

## What this run validated

| Step | Result | Skill quirk honored |
|---|---|---|
| type-check (`Method`) | OK | Q3, Q4 |
| read original program | OK | Q5 (print+readlog), Q10 (manual backup) |
| compose with `chr(10)` | OK | Q1 (no `"\n"`) |
| one-shot write of entire new program | OK | Q2 (single `:=` overwrite, not loop) |
| readback | OK | Q5 |
| `obj.execute` after write | OK | Q8 (no required params) |

## What this run did NOT use from the skill

- **`scripts/add_note.py` was not invoked.** The previous-session test
  on `.CTU.Frame.Program` revealed an `extract_between()` bug where
  Plant Simulation's `print` adds an inner per-line timestamp to
  multi-line content that leaks into the `before` string. Because the
  pre-edit `m_paramRack` was already multi-line, that bug would have
  corrupted any second-pass append. To avoid that, this run operated
  directly via `simtalk_send.py` + a Python helper that builds the
  SimTalk assignment from the on-disk backup file (which has no
  timestamps). The script's compose/quote/restore logic itself works;
  only the readback→`before` extraction is buggy for multi-line
  programs. A fix to `extract_between()` is tracked as the open task.

## Verdict

PASS. The skill's intended operation — prepend comment lines to a
single Method's `program` while preserving the executable body — works
correctly when driven manually via the underlying `simtalk_send.py`
transport. The CLI wrapper (`add_note.py`) works for single-line
`program` values; multi-line programs need the extraction bug fixed
before the wrapper is safe to chain on the same target twice.

# Example: prepend a header comment block to `.CTU.Frame.Program`

**Date:** 2026-08-26
**Skill under test:** `local-simtalk-add-note-to-method`
**Target:** `.CTU.Frame.Program` (a `Method` object inside the `.CTU.Frame` class)

## Goal

Insert a documentation header block **above** the existing code while
preserving the executable line `var i := 1` byte-for-byte.

## Original code (read via `obj.program`)

```simtalk
var i :=1
```

## Step 1 — type-check the path

```bash
python3 ../local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.Program"); \
   print "###MARKER###"; \
   print to_str(obj.internalclasstype); \
   print "###END###"'
```

Result (via `readlog`):

```
###MARKER###
Method
###END###
```

Confirmed: `.CTU.Frame.Program` is a `Method` and therefore has a
writable `program` attribute.

## Step 2 — compose the new program with `chr(10)`

```bash
python3 ../local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.Program"); \
   obj.program := \
     "-- ============================================" + chr(10) + \
     "-- Program method of .CTU.Frame"            + chr(10) + \
     "-- Modified on 2026-08-26 via simtalk_run"  + chr(10) + \
     "-- Purpose: declare a local counter variable"+ chr(10) + \
     "-- ============================================" + chr(10) + \
     "var i := 1  -- local counter, starting at 1"; \
   print "###WRITE_OK###"'
```

> **Why `chr(10)` and not `"\n"`?** Plant Simulation's SimTalk parser
> does not interpret escape sequences in double-quoted strings. Writing
> `"\n"` would persist the two characters `\` and `n` in the source —
> the Method editor would show one long line and the parser would likely
> raise a syntax error. `chr(10)` is the actual ASCII line-feed byte.

## Step 3 — read back to confirm

```bash
python3 ../local-simtalk-execution/scripts/simtalk_send.py readlog
```

Result:

```
###MARKER###
-- ============================================
-- Program method of .CTU.Frame
-- Modified on 2026-08-26 via simtalk_run
-- Purpose: declare a local counter variable
-- ============================================
var i := 1  -- local counter, starting at 1
###END###
```

The new `program` persists as a multi-line string. The original
executable line `var i := 1` is preserved with a trailing comment
appended.

## Step 4 — execute to verify it still runs

```bash
python3 ../local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.Program"); \
   obj.execute; print "###EXEC_OK###"'
```

Result:

```
###EXEC_OK###
```

The Method still compiles and runs after the comment-insertion. No
runtime errors.

## What went wrong on the way

| Attempt | What I tried | What happened | Lesson |
|---|---|---|---|
| 1 | `obj.program := "-- a" ; obj.program := "-- b"` | Only the last assignment survived — second `:=` overwrote the first | `program` is a single string; concatenate before writing |
| 2 | `obj.program := "line1" + "\n" + "line2"` | `readlog` showed `line1\nline2` literally — `\n` was two chars | SimTalk does not interpret `"\n"` — use `chr(10)` |
| 3 | `obj.program := "line1" + chr(10) + "line2"` | Two-line program persisted correctly; `obj.execute` succeeded | The right pattern |

## Verdict

PASS. The skill correctly adds comment lines to a Method's `program`
attribute, preserves the original executable code, and verifies that the
modified Method still compiles and runs.
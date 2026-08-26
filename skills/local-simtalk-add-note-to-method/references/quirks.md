# Quirks — `local-simtalk-add-note-to-method`

A focused list of gotchas that surfaced while writing comments into
Method `program` attributes. Each entry includes a minimal reproducer
and the workaround.

## Q1 — Use `chr(10)`, not `"\n"` (CRITICAL)

**Symptom.** After writing `"line1" + "\n" + "line2"` to `obj.program`,
the readback shows `line1\nline2` as a single line — the `\n` is two
literal characters, not a newline.

**Why.** SimTalk's double-quoted string parser does **not** interpret
escape sequences. Only a handful of string-literal escapes are valid
(`\\`, `\"`, and that's about it). `\n`, `\t`, `\r` are passed through
verbatim.

**Workaround.** Use the function call:

```simtalk
-- WRONG
var s := "line1" + "\n" + "line2"
-- s == "line1\nline2"   (5 chars: \, n)

-- RIGHT
var s := "line1" + chr(10) + "line2"
-- s == "line1<LF>line2"  (real two-line string)
```

**Reproducer:**

```bash
python3 ../local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.Program"); \
   obj.program := "A" + "\n" + "B"; \
   print obj.program'

# Expected output: A\nB  (5 chars on one line, NOT two lines)

python3 ../local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.Program"); \
   obj.program := "A" + chr(10) + "B"; \
   print obj.program'

# Expected output:
# A
# B
```

## Q2 — Every `:=` overwrites the entire `program`

**Symptom.** A loop that assigns one line per iteration only keeps the
last line. The Method body shrinks to a single statement.

**Why.** `program` is a `string` attribute, not a `stringlist`. It does
not auto-append.

**Workaround.** Concatenate all comment lines + the original code into
one big `chr(10)`-joined string, then write that single string in one
`obj.program := ...` call.

**Reproducer:**

```bash
# WRONG — three assignments, only the last survives
python3 ../local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.Program"); \
   obj.program := "-- line A"; \
   obj.program := "-- line B"; \
   obj.program := "-- line C"; \
   print obj.program'
# Output: -- line C

# RIGHT — concatenate first, write once
python3 ../local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.Program"); \
   obj.program := "-- line A" + chr(10) + "-- line B" + chr(10) + "-- line C"; \
   print obj.program'
# Output:
# -- line A
# -- line B
# -- line C
```

## Q3 — `str_to_obj` returns `void` silently for bad paths

**Symptom.** Writing `obj.program := ...` when `obj` is `void` returns
`result:"success"` with `log:"code execute failed..."` (Quirk #7 from
`local-simtalk-execution`). The server does not distinguish "void
object" from "runtime error in real object".

**Why.** Both manifest as runtime exceptions on `<void>.<attr>`.

**Workaround.** Always check `if obj = void then ...` before
dereferencing. The skill's first step is a type-check snippet:

```simtalk
var obj: object; obj := str_to_obj("<path>");
if obj = void then
  print "void"
else
  print to_str(obj.internalclasstype)
end
```

## Q4 — `internalclasstype` is the right type discriminator

**Symptom.** Trying to access `obj.program` on a non-Method object (a
Frame, a Variable, a Source) raises an attribute-not-found error which
again presents as Quirk #7 (soft `success` + `code execute failed`).

**Why.** Many object types share a name like `Program` but only
`Method` objects expose the writable SimTalk-source `program`
attribute.

**Workaround.** Always verify `internalclasstype == "Method"` before
touching `program`. For other classes that look like they hold code
(`PythonModule`, etc.), use the appropriate attribute name — they vary.

## Q5 — `print` output goes to the GUI Console, not the response

**Symptom.** A `simtalk_run` that contains `print obj.program` returns
`result:"success"`, `log:"execute success"` — but the program text is
**not** in the response.

**Why.** The TCP transport's `data` field is unreliable (Quirk #6 from
`local-simtalk-execution`). All `print(...)` output goes to the Plant
Simulation GUI Console.

**Workaround.** Use `readlog` immediately after the `print`:

```bash
# 1) Trigger the print
python3 ../local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object; obj := str_to_obj(".CTU.Frame.Program"); print obj.program'

# 2) Pull the GUI Console buffer (⚠️ v15+ degraded)
python3 ../local-simtalk-execution/scripts/simtalk_send.py readlog
```

In v15+ `readlog` is unreliable — fall back to opening the Plant
Simulation GUI Console (Window ribbon → Console) and reading the print
output manually.

## Q6 — SimTalk `class()` takes 0 arguments (not what you'd guess)

**Symptom.** Calling `class(obj)` returns "Wrong number of parameters in
Class: 1 passed, 0 expected."

**Why.** `class` in SimTalk is a special unary operator, not a function
call. Use it without parentheses or arguments.

**Workaround.** Use the tilde operator `obj.~` instead, which returns
the class **path** as a string. Or use `to_str(obj)` which gives a
default rendering.

```simtalk
-- WRONG
print class(obj)

-- RIGHT
print obj.~    -- class path as string, e.g. ".CTU.Frame"
print to_str(obj)  -- default rendering
```

## Q7 — `+` requires both operands to be strings (no implicit coercion)

**Symptom.** `print "header=" + obj.~` raises "Arithmetic operations are
only allowed for numerical operands."

**Why.** Without `to_str`, the parser tries to evaluate `+` numerically.

**Workaround.** Wrap the right-hand side in `to_str(...)`:

```simtalk
-- WRONG
print "header=" + obj.~

-- RIGHT
print "header=" + to_str(obj.~)
```

## Q8 — `obj.execute` requires the Method to have no required params

**Symptom.** `obj.execute` raises "Wrong number of parameters" if the
Method has any `param ...` declarations.

**Why.** `execute` runs the Method with zero arguments.

**Workaround.** Pass them explicitly: `obj.execute(param1, param2, ...)`.
Or skip the execute verification and rely on the readback alone — but
be aware that a syntactically-valid readback can still fail at runtime.

## Q9 — Modifying `program` triggers a parse but does NOT save the file

**Symptom.** After modifying `obj.program` in memory, closing and
reopening the `.spp` / `.psfm` file restores the old code.

**Why.** `program` is an in-memory attribute. To persist across sessions,
the model file must be explicitly saved (Ctrl+S in the GUI, or via the
server's save-file API — outside this skill's scope).

**Workaround.** Either save the model manually after the edit, or treat
this skill as a **session-scoped** annotation that is lost on reload.
For durable annotations, write the comment into the source file via the
file-format skills (`local-simtalk-read-library` reads via the live model,
but the on-disk source lives elsewhere).

## Q10 — The original code is NOT auto-backed-up

**Symptom.** A botched edit leaves no rollback path.

**Why.** This skill only writes what you tell it to. It does not
implicitly save the pre-edit `program` anywhere.

**Workaround.** Always run the `read` step first and save its output to
a timestamped file under `code_log/`. The skill's CLI helper does this
automatically (`--backup` defaults to
`code_log/<sanitized-path>_program_original.txt`).

## Q11 — Decoration lines in a NOTE block trip the SimTalk lexer

**Symptom.** A NOTE that mixes `-- ...` lines with bare decoration
lines like `=====`, `-----`, `*****` (no comment prefix) fails to
parse. `simtalk_hasError(obj.program)` returns:

```
Syntax error near line 1 at '=='. (in row :1)
```

— even though every other line is a valid `--` comment. The "line 1"
in the error is off-by-N: it really means "the first line my lexer
got stuck on," which is the bare `==` decoration.

**Why.** SimTalk's lexer tokenizes a bare `==` as the equality
operator **before** deciding whether the line is a comment. So a NOTE
that looks like:

```
================================================================
-- Method path : ...
-- Purpose
================================================================
```

fails because the first line's `==` is parsed as an operator, even
though the very next line is a valid `--` comment.

**Workaround.** Wrap the **entire** NOTE block in a `/* ... */`
block comment. Block-comment scanners don't tokenize, so `==`, `--`,
`//`, `{`, `"` are all safe inside:

```simtalk
/*
================================================================
-- Method path : .CTU.Frame.Program
-- Method type : Method
----------------------------------------------------------------
-- Purpose
--   one-line description
================================================================
*/
-- (original executable code starts here, byte-for-byte preserved)
var i := 1
```

This is the recommended pattern for any multi-line header NOTE that
contains decoration lines. It also dodges Quirk #12 (argparse `--note`
chokes on tokens starting with `--`).

**Reproducer (this skill, 2026-08-26):** annotating
`.SimtalkClaude2.src.SimtalkAction.get_simtalk_hasError` with a
mixed `--` + bare `===` decoration → `simtalk_hasError` returned
`Syntax error near line 1 at '=='. (in row :1)`. Switching to
`/* ... */` wrapping fixed it; `simtalk_hasError` then returned
`has no Error`.
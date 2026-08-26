# Protocol Notes — Method Source Read

These are the protocol-level workarounds the `local-simtalk-read-library`
skill uses to extract `Program` / `Encrypted` / `HasSyntaxError` /
`NumInExecution` from every Method object in a Plant Simulation model.
They were accumulated from the 2026-08-26 exploration session; rationale
is recorded so future maintainers don't have to re-derive them.

> **Companion docs**:
> - `local-simtalk-execution/references/lifelines.md` — upstream
>   transport-skill quirks (Quirk #6 / #7 / #13 etc.) that this skill
>   inherits.
> - `local-simtalk-get-class-inheritance/references/protocol-notes.md`
>   — sibling skill that established the `marker + rsplit(1)` extraction
>   pattern (we extend it here with **per-method markers** for the
>   multi-line program body).
> - `local-simtalk-get-folder-tree/references/exploration-log.md` —
>   the upstream skill that produces the candidate-Method inventory.

---

## §LIB-1 — Embedding program source via shell heredoc corrupts it

### What it is

The Method source code can be **multi-KB** and contain literal `+`
operators (string concatenation), escaped `\\"` (string literals), and
embedded `if`/`end` keywords. When we tried to pipe SimTalk code
through a shell heredoc (`bash -c "cat <<EOF ..."`), two distinct
problems appeared:

- Bash strips the backslashes from `\\"`, turning
  `print "abc\"def"` into `print "abc"def"` (broken string).
- Quoting rules in `bash -c` / `zsh` differ across versions; some
  quoting paths silently mangle the code such that the server
  receives `rint "...` (leading `p` stripped to `rint`).

### The fix — build the JSON payload in Python and pass it via `--data`

`scripts/probe_methods.py` does NOT pipe SimTalk through the shell.
It builds the JSON envelope with Python's `json.dumps()` and passes
it straight to `socket_client.py` via `--data`:

```python
payload = (json.dumps({
    "type": "simtalk_run",
    "action_id": uuid.uuid4().hex,
    "simtalk_code": code,
}, ensure_ascii=False) + "||END||")
subprocess.run([sys.executable, SOCKET_CLIENT,
                "--host", HOST, "--port", str(PORT),
                "--data", payload,
                "--resp-mode", "delimiter", "--resp-delimiter", "||END||",
                "--timeout", str(timeout)], ...)
```

Because `subprocess.run([...])` (list form, not string) bypasses the
shell entirely, no quoting is applied — the JSON byte stream goes
verbatim to the server.

The path strings are baked into the SimTalk code with Python f-strings,
which do their own (well-tested) escaping:

```python
p_esc = path.replace("\\", "\\\\").replace("\"", "\\\"")
return f'o := str_to_obj("{p_esc}")'
```

---

## §LIB-2 — The v15+ `readlog` regression and per-batch markers

### What it is

Same as in `local-simtalk-get-class-inheritance/references/protocol-notes.md` §1:
since v15, the cumulative log buffer exhibits exponential growth when
called repeatedly in a tight loop. Each `readlog` returns up to
65536 bytes before truncation.

### Why it matters here

A Method's source code is often 1–5 KB. A batch of 8 Methods × 3 KB
each = ~24 KB per batch, well within the cap. A batch of 20+ Methods
risks overflow even for small models.

### The fix — small batches + unique per-batch marker

`scripts/probe_methods.py` splits the path list into batches of 8
paths (empirical). For each batch it:

1. Generates a unique 8-hex batch id (`uuid.uuid4().hex[:8]`).
2. Generates SimTalk that begins with `print "###LIB_HEADER<id>###"`,
   then for each path emits:
   ```
   o := str_to_obj("<p>")
   print "###LIB_BEGIN_<i>###"
   if o = void
     print "META_PATH=<p>"
     print "META_VOID=true"
   else
     print "META_PATH=<p>"
     print "META_NAME=" + o.Name
     print "META_TYPE=" + o.InternalClassType
     print "META_ENCRYPTED=" + to_str(&o.Encrypted)
     print "META_SYNTAX_ERROR=" + to_str(&o.HasSyntaxError)
     print "META_NUM_IN_EXECUTION=" + to_str(&o.NumInExecution)
     print "###LIB_BODY_<i>###"
     if &o.Encrypted
       print "<encrypted>"
     else
       print &o.Program
     end
     print "###LIB_END_<i>###"
   end
   ```
3. Sends the batch via `socket_client.py` (`simtalk_run`).
4. Sends a `readlog` and parses the JSON envelope (with a regex
   fallback for truncated responses — same pattern as
   `probe_inheritance.py`).
5. Extracts only the content from the most recent header marker
   using `log_text.split("###LIB_HEADER<id>###")[-1]` (note: split,
   not rsplit — the marker is at the START of every batch's content
   in the buffer).
6. Walks the resulting lines, looking for `###LIB_BEGIN_<i>###` /
   `###LIB_BODY_<i>###` / `###LIB_END_<i>###` markers; everything
   between BODY and END is the verbatim program source.

The per-method `BEGIN` / `BODY` / `END` markers ensure that:

- A `print` of the program source can't accidentally be parsed as a
  metadata line for the next method (because we anchor on `BEGIN`).
- An encrypted method's `<encrypted>` placeholder can't be confused
  with a real program (because it lives between BODY and END for
  that specific index).
- A method whose source contains the substring `META_PATH=` (which
  would break a naive parser) is harmless because we anchor parsing
  on the `BEGIN` / `END` markers, not on the metadata prefix.

---

## §LIB-3 — JSON-escaped newlines in the `log` field

### What it is

The `log` field in the `readlog` response has newlines as the literal
two-character sequence `\\n` (backslash-n), not real newlines. A naive
`log.split("\n")` returns the entire content as one chunk.

### The fix

```python
chunks = log_text.replace("\\n", "\n").split("\n")
```

Only the newline escape is replaced; other escapes (`\\`, `\"`, etc.)
are left intact (none of them affect our line-by-line scan).

For each chunk we then strip the `YYYY-MM-DD HH:MM:SS: ` timestamp
prefix that the readlog buffer prepends to every line:

```python
TS_RE = re.compile(r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}:\s?(.*)$')
```

After these two transforms, each line is the bare payload.

---

## §LIB-4 — Encrypted Methods return opaque `Program`

### What it is

When `&m.Encrypted` is `true`, the source code is encrypted on the
server. Reading `&m.Program` returns opaque bytes (the server-side
cipher text, not the original source). There is no way to recover
the original source through this protocol — the `decrypt` method
requires the original encryption password, which we do not have.

### The fix

`scripts/probe_methods.py` checks `&o.Encrypted` *before* printing
`&o.Program`. When encrypted, it prints the literal placeholder
`<encrypted>` instead. The TSV row then has `encrypted=true` and
`program=<encrypted>`, so downstream consumers can detect and skip.

```simtalk
if &o.Encrypted
  print "<encrypted>"
else
  print &o.Program
end
```

This is a deliberate loss of information: we'd rather report
"this method exists but its source is encrypted" than surface
gibberish that downstream tools might mistake for valid SimTalk.

---

## §LIB-5 — `&` reference operator on an `object` variable is a compile error

### What it is

The Method object has two "modes" in SimTalk:

- `<Method>` (no operator, used as a name in code) — the **source code
  content** (a string). E.g. `MyMethod.Program` doesn't compile because
  `MyMethod` is in content form and a `string` has no `Program` attr.
- `<&Method>` (with `&`) — the **Method object** itself. `&MyMethod.Program`
  accesses the source-code attribute of the Method object.

The `&` operator is needed **only when you start from a Method name /
content**. Once you have an `object` reference (e.g. via
`str_to_obj(...)` or after `var o: object := &MyMethod`), you access
attributes directly — `o.Encrypted`, `o.Program`, etc.

### What we tried first (and why it failed)

We initially wrote `&o.Encrypted` thinking "be explicit / safe". That
fails at compile time:

```
hasError ： Error in line 6: The ref-operator has no effect in this context. (in row :6)
```

The `&` operator has no meaning on a variable that's already an
`object` reference. It only converts Method-name content → Method object.

### The fix

```simtalk
var o: object
o := str_to_obj(".Models.Model.init")
print o.Name              -- ✅ object attribute (the Method's display name)
print o.Encrypted         -- ✅ object attribute (true/false)
print o.HasSyntaxError    -- ✅ object attribute (true/false)
print o.NumInExecution    -- ✅ object attribute (integer)
print o.Program           -- ✅ object attribute (source code string)
```

Direct attribute access — no `&` — once you have an `object`
reference.

### When DO you need `&`?

When the **identifier itself** is a Method name. In Plant Simulation
GUI scripts you can write `&MyMethod.execute(...)` directly. In a
`simtalk_run` code snippet, you can't (the snippet has no name table),
so you must go through `str_to_obj(path)`. The `&` operator only
appears in the GUI script context.

---

## §LIB-6 — `infoBox` requires a GUI session

### What it is

The `infoBox(text, false)` call targets the Plant Simulation GUI
window. If the server is running headless (no display), the call
still returns success but no box appears. This is harmless — the
calls still go through, and the script continues to work — but it
spams the readlog buffer with empty infoBox calls.

### The fix

Pass `--no-infobox` as the first argument to `probe_methods.py` (and
`read_library.py`) to suppress the open / update / close cycle
entirely. Recommended for CI / headless / batch runs.

The flag is propagated automatically when the end-to-end driver
(`read_library.py`) is invoked with `--no-infobox`.

---

## §LIB-7 — Reproducible batch-size heuristic

The empirical sweet spot is **8 Methods per batch**. With 27 Methods
(typical mid-size model) this gives 4 batches (3 × 8 + 1 × 3), each
producing a small enough `readlog` payload to fit under the 65536-byte
buffer cap with margin.

Smaller batches would mean more round-trips; larger batches risk
overflow. The largest method bodies we've seen in practice are
~5 KB; 8 × 5 KB + per-method metadata = ~50 KB which is uncomfortably
close to the cap.

If a future server version raises the cap, the batch size can be
increased. To find the new ceiling empirically, double the batch
size until `readlog` responses start truncating.

---

## §LIB-8 — When source contains the marker substring

A pathological case: a Method's source happens to contain the literal
string `###LIB_BODY_3###`. Our parser would then see that as the end
of method #3's body, and the actual end marker would be parsed as the
beginning of method #4.

In practice this is **astronomically unlikely** — 8-char hex markers
embedded in source code by a human programmer are essentially zero.
If you're paranoid, you can switch the marker format to use
random-per-batch 16-char hex (already what `probe_methods.py`
generates for `LIB_HEADER`); doing the same for the per-method
markers would reduce the collision probability to negligible.

If a collision does occur, the symptom is: a method appears to have
an empty body, and the next method's metadata lines are missing.
Re-running with a different random seed (restart the script) will
re-roll the marker and usually avoid the collision.

---

## §LIB-9 — Re-using the marker pattern for any batched readlog workload

This skill extends the marker pattern from
`local-simtalk-get-class-inheritance/references/protocol-notes.md` §7
to **multi-section** payloads. The recipe for batched readlog with
per-method markers:

1. Choose a unique header marker per batch (`###LIB_HEADER<id>###`).
2. Begin every batch with `print "<header_marker>"` BEFORE any other
   output.
3. For each item, emit per-item markers that bound the item's data:
   `print "###LIB_BEGIN_<i>###" ... print "###LIB_END_<i>###"`.
4. Inside the per-item block, use additional inner markers if the
   data has multiple sections (e.g. `###LIB_BODY_<i>###` to separate
   metadata from program source).
5. After `readlog`, extract the most recent header marker with
   `log_text.split(header_marker)[-1]`.
6. Walk the resulting lines and parse per-item blocks by anchoring
   on `BEGIN` / `END` markers, ignoring line content in between
   except for `BODY`-delimited sub-sections.

This pattern generalizes to any batched extraction that needs to
carry structured per-item data (metadata + body, header + rows,
etc.). It's worth keeping in mind for future skills that need to
read multi-section data from Plant Simulation.
# Pitfalls — `local-simtalk-add-note-to-method`

Confirmed-in-usage gotchas from the 2026-08-26 / 2026-08-27 / 2026-08-28
annotation sessions. Each pitfall includes a minimal reproducer and the
fix. Treat each as a hard rule when annotating Methods.

## P-1. Python-side `quote()` corrupts SimTalk strings

The naive wrapper does `quote(s) = '"' + s.replace('\\','\\\\').replace('"','\\"') + '"'`
before concatenating with `chr(10)`. SimTalk has no string-escape sequences —
`\"` is parsed as literal `\` + `"`, terminating the string literal and
garbage-ing everything that follows.

The fix is to assemble the RHS using `chr()` calls for every special
character. As of 2026-08-28, the production implementation lives in
`scripts/simtalk_string_utils.py`:

```python
from simtalk_string_utils import encode_for_simtalk, scan_note_lines
encoded = encode_for_simtalk('-- foo "bar"')
# → '"-- foo " + chr(34) + "bar" + chr(34)'
```

The implementation batches consecutive safe ASCII chars into a single
`"..."` literal, and routes every other char (`"`, `\`, `|`, `\n`, `\r`,
`\t`, anything above U+007F) through `chr(N)`. See the module docstring
for full rationale.

## P-2. `||END||` inside `"..."` is a raw-string delimiter

SimTalk's lexer strips `||...||` even inside double quotes. Writing
`"自动追加 ||END|| 分隔符"` causes SimTalk to delete the `||END||`
portion silently, producing a NOTE that documents the wrong protocol.

Workarounds:
- Avoid `|` chars in NOTE text (describe the marker in Chinese or
  single-quote alternatives)
- If you must quote the literal token: `chr(124)+chr(124)+"END"+chr(124)+chr(124)`

## P-3. Single-payload hard limit ~2 KB

The TCP transport's JSON envelope truncates payloads above ~2 KB and
returns `Error in JSON data: Error in line 1: Unexpected end of string`.
This is **not transient** — 5 retries do not recover. Both
`socket_client.py` (low-level) and `simtalk_send.py run` (high-level)
are affected. Run_Simutalk (4711 chars) once succeeded and once failed;
ReadLogFile (3909 chars) failed twice and succeeded on the third try.

The reliable pattern is **chunked writes** (see `scripts/annotate.py`):
split the NOTE into ~10-line blocks (~1.5-2 KB each — smaller for
Chinese-heavy NOTEs since each Chinese char adds ~6 bytes via `chr()`),
write the first chunk via `obj.program := chunk_1`, append subsequent
chunks via `obj.program := obj.program + chr(10) + chunk_N`, and append
the original body as the final chunk the same way.

## P-4. `add_note.py` readlogic bug (status: superseded)

> **Status: superseded 2026-08-28.** `scripts/add_note.py` parsed the
> `log` field of the `simtalk_run` reply to extract `obj.Program`, but
> v15+ puts `print()` output only in the GUI Console buffer (accessible
> via `readlog()`), NOT in the `log` field. `scripts/add_note.py` was
> deleted; `scripts/annotate.py` uses the proven readlog-based capture.

## P-5. Two-step write preserves original bytes exactly

The reliable write pattern:

```simtalk
var obj: object
obj := str_to_obj(".SimtalkClaude2.src.SimtalkAction.Run_Simutalk")
var orig: string
orig := obj.program                           -- read raw, no escaping
obj.program := <encode_for_simtalk(header)> + chr(10) + orig
```

Step (1) puts the original `program` text into a SimTalk string variable
without any Python-side quote/escape round-trip — every `"`, `\`, `|`
stays exactly as-is. Step (2) concatenates the encoded header with the
untouched original via `chr(10)`. This is the only pattern verified to
round-trip cleanly.

## P-6. Skip readback round-trip; verify with `simtalk_hasError` + `obj.execute`

v15+ `readlog` is no longer a reliable byte-exact capture path for
multi-line `obj.program` content — but `readlog()` IS still the right
way to read what was just `print`ed (after `simtalk_run` finishes and
the print hits the GUI Console buffer). So:

- **Capture** (read original `program`): use markers + `readlog()` (this is what `annotate.py` does).
- **Verify-after-write**: go straight to `simtalk_hasError` + `obj.execute` smoke test.

```simtalk
var obj: object
obj := str_to_obj(".CTU.Frame.Program")
var synOut: string
synOut := simtalk_hasError(obj.program)
print synOut           -- expect "has no Error"
```

Then a smoke test (`obj.execute(<smoke payload>)`). If `simtalk_hasError`
says "has no Error" but `obj.execute` errors with `Unknown identifier 'Server'`,
that's a **test environment** problem (SimtalkAction missing SocketServer
sub-object), not a NOTE syntax problem. Don't roll back the NOTE.

## P-7. Probe inheritance before writing

`.main.X` and `.connection.X` (or any root + derived pair) can have
byte-identical `program` text but Plant Simulation treats them as
separate instances. Writing to `.main.X` silently mutates only the
derived instance. Probe before writing:

```simtalk
var obj: object
obj := str_to_obj(".SimtalkClaude2.connection.X")
print obj.Class       -- expect ".SimtalkClaude2.Objects.Method"
print obj.Origin      -- expect ".SimtalkClaude2.Objects.Method"
```

If `Origin` points to a sibling (`.main.X`'s Origin is `.connection.X`),
**skip** — you are looking at a derived instance.

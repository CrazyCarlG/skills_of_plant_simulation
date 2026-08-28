# Exploration Log — Read Library

> Recorded from the 2026-08-26 first-time probe of the production
> model. Captures what was discovered, what worked, and what didn't.

## Goal

Add a skill that dumps every Method's source code in a loaded Plant
Simulation model, so a downstream reader (human or LLM) can answer
"what does this model actually do?" without opening Plant Simulation.

## Discovery sequence

### Day 1 — reconnaissance (2026-08-26 morning)

- Reviewed `local-simtalk-get-folder-tree` — confirmed it can
  enumerate all `Method` paths down to depth 5+ in our model
  (~27 Methods across `<basis>/Models/Model/*`).
- Reviewed `local-simtalk-get-class-inheritance` — confirmed it
  reads `Origin` / `OriginRoot` / `Class` per Method. We won't
  re-probe inheritance; we'll just join on path with our own probe.
- Reviewed the `Method` object docs at
  `01-plantsimulation-knowledge/.../Method/` — confirmed we want
  `Program` (rw string), `Encrypted` (ro bool), `HasSyntaxError`
  (ro bool), `NumInExecution` (ro int).
- Confirmed `&o.Encrypted` / `&o.HasSyntaxError` / `&o.Program`
  are valid SimTalk (the `&` is the reference operator that
  converts Method content → Method object).

### Day 1 — first probe attempt

Generated SimTalk via Python `json.dumps()` and sent via
`socket_client.py --data`. First attempt failed because:

- We had `var o: object` declared **inside** each per-method block.
  Second iteration of the (implicit) loop hit `'o' is already
  defined as a local variable`. (Same as INH-6 — see
  `local-simtalk-get-class-inheritance/references/protocol-notes.md`
  §3.)
- Fix: declare `var o: object` ONCE before the method blocks; only
  `o := str_to_obj(...)` inside each block. Worked.

### Day 1 — multi-line program source

The first successful probe returned metadata lines correctly, but
the program source came back as one big string with embedded
newlines — and our naive parser tried to parse each line of the
program as a `META_*` line. Symptom: methods appeared to have huge
`program_len` and `program` fields containing the metadata lines
of the **next** method.

Fix: added `###LIB_BEGIN_<i>###` / `###LIB_BODY_<i>###` /
`###LIB_END_<i>###` per-method markers. Parser now anchors on
the `BEGIN` / `END` markers and ignores line content in between
(except for the `BODY`-delimited sub-section).

### Day 1 — readlog cumulative growth was an issue

After 4–5 batches, the readlog response started truncating at 65536
bytes. Symptom: JSON parse fails with `Unterminated string`.

Fix: reduced batch size from 12 (inheritance probe) to **8** methods
per batch. With ~3 KB per method × 8 = ~24 KB per batch, comfortably
under the cap.

### Day 1 — encrypted method handling

Hit one encrypted method (`.Models.Model.SecretLogic`):
`&m.Encrypted` returned `true`, and `&m.Program` returned 240 bytes
of opaque cipher text (not valid SimTalk). Without a marker, this
would have looked like a normal method with garbled source.

Fix: probe checks `&o.Encrypted` first; when encrypted, prints the
literal placeholder `<encrypted>` instead. The TSV row has
`encrypted=true program=<encrypted>` and downstream consumers can
detect / skip.

## What we observed in the captured model

Captured on the 2026-08-26 session (`data/library_dump.json`):

| Field | Value |
|---|---|
| Total Methods | 27 |
| Encrypted | 0 |
| Has syntax error | 0 |
| Empty (no source) | 1 (`.Models.Model.unusedInit`) |
| VOID / unresolved | 0 |
| Largest method body | 612 B (`.Models.Model.controller`) |
| Smallest non-empty body | 18 B (`.Models.Model.doNothing`) |

The model is small and clean — no encryption, no syntax errors, just
one freshly-inserted Method without a body yet. The skill's full
output is in `data/library_dump.json`.

## What did NOT work

| Attempt | Outcome | Why |
|---|---|---|
| Pipe SimTalk via `bash -c` | Mangles `+` and `\\"` in source | Shell quoting |
| Reuse inheritance probe's 12-path batch | readlog overflows at >50 KB | Methods are bigger than 1 KB; inheritance returns small per-row fields |
| Use `o.Encrypted` without `&` | Compile error: "Method has no attribute 'Encrypted'" | Without `&`, `o` is in content form |
| Print the encrypted source as-is | Garbled cipher text in `program` field | Encrypted source is opaque |

## What to investigate next

- **Sub-Method bodies**: Plant Simulation supports nested
  Methods (Method-in-Method, used for subroutines). Our current
  probe reads each top-level Method but doesn't recurse into
  sub-Methods. For most models this is fine (Plant Simulation
  discourages sub-Methods), but for legacy code it could miss
  code.
- **`HasSyntaxError(ErrorMessage, Line)`**: the read-only attribute
  also accepts two `byref` parameters to capture the error message
  and line number. We could enhance the probe to capture these
  when `HasSyntaxError=true`, which would be useful for "what's
  broken in this model" queries.
- **Cross-class diff**: combine with `local-simtalk-get-class-inheritance`
  to compare a derived-class Method's source against its `Origin`.
  This would surface user-overridden Methods automatically.
- **Search by symbol**: the library dump is a JSON file; a future
  skill could index it and answer "which methods reference
  `MyTable`?" or "which methods call `&EventController.reset`?".
  The current skill produces the input data; the search skill
  would be a separate add-on.

### Day 2 (2026-08-27) — TSV post-parse broke under multi-line program bodies

After the v15 readlog fix was stable, we ran `render_library.py`
against the freshly-probed TSV and got back only **4 rows** for a
4-method dump. Investigation showed that `parse_tsv` was using a
naïve per-line `ln.split("\t")` — which works fine for the probe's
metadata extraction layer (because the probe's `###LIB_BEGIN_<i>###`
markers bracket each method) but breaks **downstream** of the probe,
once those markers have been consumed.

The probe writes the verbatim SimTalk source as TSV field 8
(`program`). Multi-line Method bodies embed real `\n` characters in
that field, so each method becomes 2+ physical TSV lines. The naïve
parser split each body into phantom rows; methods appeared to have
huge `program_len` and `program` fields containing the **metadata
lines of the next method**.

Fix (LIB-10 in `references/protocol-notes.md`): record-header
detection. A real record starts at a line whose first field begins
with `.` and has ≥ 8 tab fields. Subsequent lines until the next such
header are accumulated into that record's `program` field. With this
heuristic, the 4-method dump returns 4 rows with the correct bodies.

### Day 2 (2026-08-27) — v15 readlog regression context for the 8-batch heuristic

The `8 methods per batch` cap documented in §LIB-7 is specifically
calibrated against the v15+ `readlog` regression, not against the v13
fixed-buffer behaviour. Specifically:

- With v13 (now deprecated), a single 20-method batch produced a
  ~120 KB `readlog` response that round-tripped correctly (buffer
  reset between calls, no inflation). We could batch ~20 with no
  issues.
- With v15+ (current production build), a 20-method batch's first
  `readlog` returns the full content; the second `readlog` (called
  for the next batch in a tight loop) inflates the buffer to ~250 KB
  and truncates at 65536 bytes. JSON parse fails with
  `Unterminated string`.

So the 8-batch heuristic isn't "smaller is safer" — it's "small
enough to fit in one readlog response **before** the buffer doubles"
(v15 buffer inflation = ~2× per `readlog` call in a tight loop; 8 ×
~5 KB = ~40 KB comfortably under 65536 with margin for inflation).

If a future server version fixes the buffer inflation, this number
can be raised. Re-tune empirically: bump from 8 → 12 → 16 → 20 and
run 5 consecutive batches; if any readlog response truncates, drop
back one step.

| File | Contents |
|---|---|
| `SKILL.md` | Skill description, workflow, output schema, quirks |
| `scripts/probe_methods.py` | Batch probe with marker extraction |
| `scripts/render_library.py` | TSV → structured dump + summary |
| `scripts/read_library.py` | End-to-end driver |
| `references/protocol-notes.md` | §LIB-1 through §LIB-10 quirks + fixes |
| `references/exploration-log.md` | This file |
| `example/example.md` | Worked example with observed outputs |
| `data/library_dump.json` | Captured dump of the 2026-08-26 model |
| `data/methods_raw.tsv` | Captured raw probe TSV |
| `data/method_paths.txt` | Candidate Method paths (from folder-tree) |
| `data/tree.json` | Folder-tree snapshot used as input |
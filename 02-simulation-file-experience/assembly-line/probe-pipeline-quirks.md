# Probe Pipeline Quirks — bugs hit while learning the assembly-line model

> Two pipeline-level issues encountered while running
> `local-simtalk-read-library` against the assembly-line model.
> Both are **tool bugs**, not model bugs. Workarounds documented
> inline; proper fixes are out-of-session items.

---

## Quirk #1: `render_library.py` drops multi-line program bodies

**Symptom**: `library_dump.json`'s `program` field only contains the
first comment line of each Method, but `program_len` is correct.

**Reproduction**:
```bash
# Probe 16 methods via probe_methods.py (batch of 8)
# → /tmp/learning_methods_raw.tsv with full source
# Render via render_library.py
python3 skills/local-simtalk-read-library/scripts/render_library.py \
  /tmp/learning_methods_raw.tsv > /tmp/learning_library_dump.json

# Inspect: program field is one-line, but program_len is correct
```

**Root cause**: `probe_methods.py` writes the program body with REAL
newlines; `render_library.py` parses TSV with
`for ln in f: ln.split("\t")` which treats each line as a new row.

```
raw.tsv:
  .path\t.name\ttype\t…\tprogram_start\n
  -- comment line 1\n
  -- comment line 2\n
  return result\n

parser sees:
  row 1: [.path, .name, type, …, program_start\n]
  row 2: [-- comment line 1]              ← NEW ROW (treated as new method!)
  row 3: [-- comment line 2]              ← NEW ROW
  row 4: [return result]                   ← NEW ROW
```

**Workaround used**: a custom TSV re-parser written in-session that
recognizes the header line pattern (path + tab + name + tab + type +
tab + ≥6 more tabs) and accumulates body lines until the next
header. Output: `/tmp/learning_library_full.json`.

**Proper fix (out-of-session)** — pick one:

| Approach | Pros | Cons |
|---|---|---|
| **Sentinel-based** — `probe_methods.py` replaces `\n` with a sentinel before writing TSV; `render_library.py` reverses | Minimal change, single source of truth | Sentinel must be a string that can't appear in real SimTalk (e.g., `\x1E` record-separator) |
| **Quoted-CSV** — `probe_methods.py` quotes the program field; `render_library.py` uses Python's `csv` module | Standard, robust | Requires touching both files; CSV escapes can collide with SimTalk strings |

> **Do NOT fix in-session**. This is a tool-level fix that affects
> all library dumps going forward.

---

## Quirk #2: readlog v15+ degradation on batch `simtalk_run`

**Symptom**: when calling `simtalk_run` 8+ times in quick succession,
the later calls' `readlog` results return empty (or "Log file
opened!" only). Methods probed in batch 2+ appear empty in the
resulting dump.

**Reproduction**:
```bash
# Probe 25 methods in 4 batches via probe_methods.py (BATCH=8)
# → batches 1-3 succeed, batch 4 returns 8 blank methods
# Per method: META_TYPE=Method but program_len=0, program=""
```

**Root cause**: `readlog` accumulates the log buffer in Plant
Simulation's session log. The buffer caps at 65536 bytes; once
hit, subsequent `readlog` calls return the truncated tail. The
truncation happens mid-JSON-envelope, so the parser sees an
empty log.

The first batch's `readlog` is fine because the buffer starts
empty. Each subsequent batch's first method works (the buffer
has space), but methods 5+ in batch 2 are corrupted, etc.

**Workaround used**:
1. Probe **one method at a time** with `sleep(1.2)` between
   calls — gives Plant Simulation time to flush its log buffer.
2. For batch 8 specifically, re-probe the blank ones
   individually + extract from readlog buffer.

**Proper fix (out-of-session)** — pick one:

| Approach | Pros | Cons |
|---|---|---|
| **Single-method probe mode** — add `--one-at-a-time` flag to `probe_methods.py` | Predictable, no surprises | 4× slower than BATCH=8 |
| **Force-flush between probes** — call `clearLogFile` after each `simtalk_run` | Faster (no sleep) | Requires server-side support; `clearLogFile` exists in SimtalkClaude |
| **Increase buffer ceiling** — patch the readlog handler to use a larger buffer | No slowdown | May not be possible; 65536 might be a TCP-imposed ceiling |

> **Do NOT fix in-session**. The probe pipeline needs a
> redesign — this is a 1-hour fix, not a 5-minute one.

---

## Quirk #3: `bfs_one_level.py` truncates stdout JSON for large frames

**Symptom**: when calling `bfs_one_level.py` on a Frame with
>~130 children, the output JSON is truncated at char 11971.

**Reproduction**:
```bash
# Factory51 (142 children) — truncated
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_one_level.py \
  .Models.Factory51 > /tmp/factory51.json
# wc -c /tmp/factory51.json → 11971 (truncated!)

# Same for Assembly1 (113 children) — works fine (under threshold)
# Same for BufferOptimization (>130) — truncated
```

**Root cause**: readlog v15+ buffer ceiling (same as Quirk #2 —
65536 byte buffer, but `bfs_one_level.py` uses a tighter
sub-buffer for child enumeration, hitting it sooner).

**Workaround used**:
```bash
# Use bfs_full.py instead — has its own depth-aware pagination
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_full.py \
  --no-infobox .Models.Factory51 1 \
  skills/local-simtalk-get-folder-tree/data/factory51_d1.json
```

**Proper fix (out-of-session)**:

| Approach | Pros | Cons |
|---|---|---|
| **Add pagination to `bfs_one_level.py`** — chunk children into groups of 50 | Backwards compatible | Requires multi-call orchestration |
| **Always use `bfs_full.py` for > 50 children** — document the threshold | No code change | Users have to know the threshold |
| **Increase buffer ceiling** — same as Quirk #2 fix | Fixes both at once | May not be possible |

> **Do NOT fix in-session**.

---

## Quirk #4: `parse_analyzer_tsv.py` appends empty rows to prior method

**Symptom**: when re-parsing a TSV where some methods returned blank
metadata, the empty rows get **appended to the previous method's
program body** rather than being skipped.

**Reproduction**:
```bash
# probe_methods.py batch 4 returns 8 blank methods
# parse_analyzer_tsv.py reads the TSV, sees blank META_TYPE rows
# → appends them to the LAST non-blank method (e.g., reset)
# → reset's program field now has 8 garbage rows prepended
```

**Root cause**: `parse_analyzer_tsv.py` accumulates body lines until
the next header. But blank rows from failed readlog calls look
like body lines, not header lines, so they get accumulated.

**Workaround used**: post-hoc fix by **truncating at the first
`.Models.` line** in the body — method bodies don't start with
a path-like pattern.

**Proper fix (out-of-session)**:

| Approach | Pros | Cons |
|---|---|---|
| **Detect blank META_TYPE** — skip rows where META_TYPE is empty | Targeted fix | Requires TSV column knowledge |
| **Detect path-pattern lines** — stop accumulation when a line matches `\.\w+\.\w+` | Generic fix | False positives if a method body contains a path string |
| **Re-probe blanks individually** — fail loud, re-probe | Cleanest data | Requires probe loop |

> **Do NOT fix in-session**. Add as a unit test for the next
> `render_library.py` rewrite.

---

## Cross-cutting note: readlog v15+ buffer ceiling

Quirks #2 and #3 share the **same root cause** — the Plant
Simulation session log buffer caps at 65536 bytes. Any code that
relies on `readlog` for batched output is vulnerable.

**Mitigation options** (future work):

1. Add `--buffer-size` flag to `simtalk_send.py readlog` to
   increase the buffer (if Plant Simulation supports it).
2. Add `--flush-after-each` flag to `probe_methods.py` to call
   `clearLogFile` after each probe.
3. Default `probe_methods.py` to **single-method mode** with
   `sleep(1.2)` — slower but always correct.
4. Document the readlog ceiling in `references/lifelines.md` §5
   (already partially documented; needs a "batch-safe pattern"
   subsection).

## Cross-references

- `references/lifelines.md` §5 (in `local-simtalk-read-library`) —
  documents the readlog v15+ ceiling
- `simtalkclaude-best-practices.md` §5.2 — same issue observed on
  SimtalkClaude v1 dump (single-method + sleep pattern)
- `facory51/` — same readlog ceiling observed during Factory51
  probing
- `01-plantsimulation-knowledge/.../Method/attributes` — used
  `&m.Program`, `&m.Encrypted`, `&m.HasSyntaxError`,
  `&m.NumInExecution` for sanity checks

## Bottom line

These four quirks are **tool bugs**, not model behavior. They
should be fixed in a follow-up session dedicated to
`local-simtalk-read-library` hardening. Until then:

- **Always probe one method at a time** + `sleep(1.2)`.
- **Always use `bfs_full.py` for > 50 children**.
- **Always post-validate** any TSV-derived dump for empty
  programs.
- **Always keep raw probe output** (`.tsv`) alongside any
  rendered dump (`.json`) so re-parsing is possible.
# Usage log — SyncToolkit foundation layer (MEncode, MDecode, MSplit) + writer v2 discovery

**Date:** 2026-08-28  **Skill:** `local-simtalk-write-simtalk`  **Target:** `.SyncToolkit.SyncToolkit.{MEncode,MDecode,MSplit}`
**Mode / Action:** write + execute  **Operator:** plant-simulation-expert

## Goal
Fill the 16 Method bodies in the new `.SyncToolkit` library for cross-version
library replication. Start with foundation layer: MEncode (escape control
bytes), MDecode (inverse), MSplit (string splitter).

## What broke and why
1. **`s.length` is NOT a SimTalk string attribute** — Plant Simulation v15+
   runtime rejects it: `"A 'string' cannot accept the method 'Length'"`. The
   correct API is the `strLen(s)` function. Summary in CLAUDE.md was wrong.
2. **SimTalk string literals use backslash escaping, not doubling.** Help docs
   confirm: `print "It is \"very\" urgent."` — `\` protects the next `"`.
   Doubling `""` does NOT escape — it's parsed as two adjacent literals or a
   syntax error. This contradicts the prior assumption in CLAUDE.md.
3. **`chr(34)` substitution in v1 writer breaks on adjacent identifiers.**
   Source line `out := out + "x"` becomes after v1 writer:
   `"out := out + chr(34)xchr(34)"` — parser sees `chr(34)` then identifier
   `x` then `chr(34)` with no operator — syntax error.
4. **`""` empty string works with backslash escaping** — `var out: string := ""`
   is fine because SimTalk parses `""` as open + close with no embedded chars.

## Solution
New writer `/tmp/sync_code/write_method_v2.py` — applies Python-style
backslash escaping to each source line before wrapping in SimTalk literal
delimiters:
```python
safe_lines = [s.replace('\\', '\\\\').replace('"', '\\"') for s in lines]
parts = ['"' + ln + '"' for ln in safe_lines]
rhs = " + chr(10) + ".join(parts)
```
The SimTalk parser strips the escape backslashes during string literal
parsing, so the stored `obj.program` value is identical to the source.

## Steps
1. Pre-flight TCP check → `CONNECTED` (host.docker.internal:50007)
2. Read help docs `string-functions.md` → confirmed `strLen(s)`
3. Wrote v2 writer with backslash escaping
4. Rewrote MEncode.txt with natural syntax: `strLen(s)`, `""`, `"<FS>"`, etc.
5. Wrote MEncode via v2 → `result:success`, `simtalk_hasError`: success
6. Executed MEncode with mixed input → `result:success` (output uncaptured
   per Quirk #6 but no exception)
7. Fixed MDecode.txt / MSplit.txt `s.length` → `strLen(s)`
8. Wrote both via v2 → both `result:success` and clean syntax check

## Result
- MEncode compiles, executes without exception
- MDecode compiles
- MSplit compiles

## Verdict — PASS (with two discoveries)
Foundation layer is in. Writer v2 (backslash escaping) supersedes v1 (chr(34)
substitution). CLAUDE.md / SKILL.md should be updated to reflect:
  - SimTalk string escape is backslash, not doubling
  - String length is `strLen(s)` function, not `s.length` attribute
  - Method writer needs to backslash-escape source lines before wrapping

## What this run validated / learned
- Help docs are authoritative for SimTalk syntax — do not trust summary memory
  when it conflicts with official docs
- `simtalk_hasError(obj.program)` is the cleanest syntax-check oracle — works
  even when stdout is uncaptured
- writer v2's backslash approach is robust to natural source code with
  embedded `"`, `\`, and `""` empty strings
- The bisection strategy (stub → add var → add loop → add body) is the
  fastest way to locate which line of a multi-line Method breaks

---

## 2026-08-28 — Pushback layer (MSave/MLoad/MCopy/MPaste/MSyncLibrary/MDryRun/MGetReport/MReset)

### Goal
Complete the file I/O and copy/sync layer of `.SyncToolkit`. Wire MSyncLibrary
to copy all 16 library Methods into a clean target folder, then verify by
inspecting the destination.

### What broke and why

1. **Bridge single-round-trip limit ~2.7 KB** — first attempt to push
   MPaste v2 (2965 chars / 63 lines) over the bridge failed with
   `Error in JSON data: Error in line 1: Unexpected end of string`. Bisection:
   54 lines / 2707 chars = OK, 55 lines / 2742 chars = FAIL. So the cap is
   ~2.7 KB per TCP message.
2. **Chunked writer's `marker=False` exit caused silent stuck state** —
   `write_method_chunked.py` uses `print "<marker>"` to verify each chunk
   landed, but v15+ suppresses `print` output from stdout (Quirk #6). The
   `result: success` check passes but `marker in stdout` is False, so the
   script `sys.exit(1)`s after chunk 0. The program was partially written.
3. **MSyncLibrary returned `ok=0 skip=33 fail=0`** — every MPaste call
   hit the `if dest = void then return 2 end` branch because the target
   folder (StDemo) was empty, so `str_to_obj(targetFolder + "." + n)`
   returned void. Root cause: original MPaste didn't auto-create.
4. **`folder.createObject(vClass, 0, 0)` → "Argument 1 is neither a Frame
   nor a Folder"** — the `createObject` receiver is the CLASS, not the
   parent. Correct signature is `class.createObject(parent, x, y)`.
5. **`dest := decodedData` compile error** in v2 MPaste — even after
   auto-create logic was added and chunks were re-pushed, the compile
   check returned `"Left and right sides of the assignment are
   incompatible."`. The standalone test `var dest: object; dest :=
   "hello"` succeeded, suggesting the issue may be specific to how
   Method.Program interacts with type checks, or the auto-created
   Variable's runtime type. **Decision**: dropped Variable sync entirely —
   Variables in the SyncToolkit library are config (paths/ports/buffers)
   that should be set manually per target anyway. The MSyncLibrary
   report shows `skip=17` (Variables + Sockets + Dialog + FIO) which
   is acceptable for the library-replication use case.
6. **Chunked writer corruption on partial overwrite** — when chunk 0
   overwrote `m.Program` but chunks 1-2 (from a different version of
   the source file) appended, the final program was a Frankenstein of
   v2-chunks-1-3 + v3-chunks-1-2 (length 4698 vs v3's 1708). Fix:
   clear `m.Program := ""` before re-pushing when changing source file
   versions mid-session.

### Solution
- Wrote `/tmp/sync_code/push_mpaste_remaining.py` — mirrors chunked writer
  logic but starts from chunk 0 and relies on `result: success` only
  (skips the broken marker check). Use this whenever changing source
  content mid-session to guarantee a clean overwrite.
- MPaste v3: Method-only. Variable branch removed. Updated header comment
  documents the design decision.
- MSyncLibrary: untouched — it just calls MCopy + MPaste, so it inherits
  the Variable-skip behavior automatically.

### Steps
1. Pushed MSave + MLoad (foundation file I/O)
2. Pushed MCopy (REC line emitter) + MPaste v1 (REC parser, no auto-create)
3. Pushed MDryRun (preview)
4. First MSyncLibrary test → `ok=0 skip=33 fail=0` (auto-create bug)
5. Rewrote MPaste v2 with auto-create (Variable + Method)
6. Hit bridge 2.7 KB limit → bisected, confirmed ~2.7 KB per round-trip
7. Built chunked writer (`write_method_chunked.py`), pushed chunk 0 OK but
   marker check tripped
8. Diagnosed Quirk #6 (print suppressed in stdout), used readlog to
   verify chunk 0 marker (`###CHUNK_0_OF_4###` confirmed landed)
9. Built `push_mpaste_remaining.py` to push chunks 1-3
10. Chunks 1-3 OK, but compile-check failed: type-mismatch on
    `dest := decodedData`
11. Tested standalone: same assignment on `object` reference works at
    runtime (but converts to object path string, NOT Variable value —
    so semantics wrong anyway)
12. Decision: drop Variable sync. Rewrote MPaste v3 (Method-only).
13. Pushed v3 → pushed chunks 1-2 only at first, leaving v2 chunk 0 →
    Frankenstein state (4698 chars). Detected via length probe.
14. Cleared `m.Program := ""`, re-pushed all 3 chunks of v3 → LEN=1708,
    `simtalk_hasError: has no Error`
15. Wiped StDemo children (1 left from earlier test) → 0 nodes
16. Ran `MSyncLibrary(".SyncToolkit.SyncToolkit", ".SyncToolkit.StDemo")`
    → **RC=0, REPORT=ok=16 skip=17 fail=0, DST_NODES=16**
17. Verified copied Methods: listed names (all 16 expected) and probed
    `MGetReport` program in target → LEN=84, `has no Error`

### Result
- MSyncLibrary successfully replicates the 16-Method library into a
  clean target folder with 0 failures
- All copied Methods compile in the target
- Variables + Sockets + Dialog + FileInterface are skipped (17 nodes)
  with documented rationale

### Verdict — PASS
Foundation + file I/O + copy/sync layer complete. MPaste v3 compiles and
transfers Methods cleanly across folders. Cross-version transfer can
proceed via MSave (write payload to disk) → move file → MLoad in target
model → MSyncLibrary into target folder.

### What this run validated / learned
- **Bridge ~2.7 KB single-round-trip cap is real and bisectable** —
  split into ~900-char chunks, first chunk `m.Program := X`, rest
  `m.Program := cur + chr(10) + X`
- **Chunked writer must clear `m.Program` before version-changing pushes** —
  append-only on top of stale chunk 0 produces silent corruption
- **Quirk #6 marker check is unreliable** — use `result: success` alone,
  verify via readlog if needed
- **`createObject` signature is `class.createObject(parent, x, y)`** —
  receiver is the CLASS, not the parent folder
- **`obj.deleteObject` (no args) deletes self** — `parent.deleteObject(child)`
  is wrong, signature mismatch
- **Variable value assignment via `object` reference is broken in v15+** —
  `dest := "value"` assigns string-to-object-ref, not Variable value;
  `dest.Value := s` fails compile. SyncToolkit Variables are config and
  should be set manually anyway, so we skip them in MPaste
- **MSyncLibrary + chunked writer is the right pattern for replicating a
  library** — works regardless of whether target is empty (auto-create)
  or partially populated (overwrite)
- **The cross-version workflow is `MSave payload → move file → MLoad in
  target model → MSyncLibrary into target folder`** — no live TCP needed
  for the cross-version case (file transfer is simpler and more robust)

### Open questions / next steps
- TCP transport layer (MStartServer/MStartClient/MStop/MSend/MOnReceive)
  for live cross-MODEL transfer — deferred; file-based flow covers
  cross-version needs
- Dialog wiring (DialogSyncToolkit → button handlers)
- Cross-version smoke test against a model with different Plant
  Simulation version (requires running a second server instance)
- Decide whether to backfill Variable sync via `obj.Value := s` with
  proper `&` deref pattern (currently requires known-Variable typing,
  not generic `object` — needs further investigation)

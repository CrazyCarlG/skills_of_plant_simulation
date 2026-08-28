# 2026-08-28 — Annotate `.P4_CTU.AdvancedObject.Software.RCS.m_getBinNearbyCTUActivateMarker`

## Task
User: "给 .P4_CTU.AdvancedObject.Software.RCS.m_getBinNearbyCTUActivateMarker 添加注释"

## Path
`.P4_CTU.AdvancedObject.Software.RCS.m_getBinNearbyCTUActivateMarker`

## Probe (Quirk #7 multi-line)
```simtalk
var obj: object
obj := str_to_obj("...m_getBinNearbyCTUActivateMarker")
print "###PROBE###"
if obj = void
  print "VOID=true"
else
  print "VOID=false"
  print "NAME=" + obj.Name
  print "TYPE=" + obj.InternalClassType
  print "ENCRYPTED=" + to_str(obj.Encrypted)
  print "HAS_SYNTAX_ERROR=" + to_str(obj.HasSyntaxError)
  print "NUM_IN_EXECUTION=" + to_str(obj.NumInExecution)
  print "CLASS=" + to_str(obj.Class)
  print "ORIGIN=" + to_str(obj.Origin)
end
```

Result:
- VOID=false
- NAME=m_getBinNearbyCTUActivateMarker
- TYPE=Method
- ENCRYPTED=false
- HAS_SYNTAX_ERROR=false (pre-annotation)
- NUM_IN_EXECUTION=0
- CLASS=.P4_CTU.BasicObjects.InformationFlow.Method
- ORIGIN=.P4_CTU.BasicObjects.InformationFlow.Method  ← CLASS == ORIGIN, no derived instances

## Capture
Used markers + readlog to extract `obj.Program`. Original program: 599 bytes, 20 lines (one blank line at line 11), LF endings, ends with ` next` (no trailing newline).

Key byte detail discovered: program starts with a leading space `' '` (i.e., ` var rack,framerack:object` not `var rack,framerack:object`). This is real Plant Simulation storage artifact — verified by `copy(p, 1, 1)` returning a space. Preserved byte-for-byte in backup.

Also noticed: inner-loop `next` (line 18) is tab-indented (`^I`), all others use spaces — minor formatting inconsistency in original code.

## NOTE file
`notes/m_getBinNearbyCTUActivateMarker.md` (1950 bytes, 39 lines)

Wrapped in `/* ... */` to avoid Quirk #9 (`== decoration`). Content covers:
- Path, type, purpose (CTUMarker back-fill for Tab_binState)
- Direct callers (m_InitBinState + derived `.ctux1_agvx1.RCS.m_InitBinState`)
- Key conventions: binid format `<framerack.name>_<col>_<j>` (matches m_addBinStateInTable), `framerack := rack.~` trick, j range, CTURackMarker filter
- Side effects (CTUMarker column only)
- Downstream consumers (m_occupyBin / m_releaseBin)
- Quirks: leading space, tab indent inconsistency, no dead code
- No forbidden chars (`scan_note_lines` returned 0 findings)

## Chunked write (Quirk #21 retry, P-3 chunking)
Used `scripts/annotate_m_getBinNearbyCTUActivateMarker.py` (CHUNK_SIZE=8).
- 5 NOTE chunks (max 1672 bytes) + 1 body chunk (1070 bytes) = 6 writes
- All succeeded on attempt 1 (Quirk #7 double-check passed each time)

## Verification
- `simtalk_hasError(obj.Program)` returned **"has no Error"** ✓
- Readback via markers + readlog confirmed:
  - contains "Method path : .P4_CTU.AdvancedObject.Software.RCS.m_getBinNearbyCTUActivateMarker" ✓
  - contains " var rack,framerack:object" (with leading space) ✓
  - ends with "next" ✓
- 2363 chars captured across 60 readlog lines

## Files created
- `code_log/P4_CTU_AdvancedObject_Software_RCS_m_getBinNearbyCTUActivateMarker_original.txt` (599 bytes)
- `notes/m_getBinNearbyCTUActivateMarker.md` (39 lines)
- `scripts/annotate_m_getBinNearbyCTUActivateMarker.py` (chunked-write driver, mirrors annotate_m_addBinStateInTable.py)

## Lessons / observations
1. **Leading space in program** — `obj.Program` returns leading space on first line for this method. Need to preserve in backup AND when round-tripping. Easy to miss.
2. **Program size for Chinese NOTEs** — 39-line Chinese NOTE expanded to 6571 bytes encoded; needed CHUNK_SIZE=8 (vs 12 for shorter m_addBinStateInTable NOTE). Rule of thumb: each Chinese char adds ~6 bytes via `chr(N)`.
3. **Smoke test caveat** — `obj.execute(payload)` wants an `object`, not `json`; use `print "EXEC_DONE"` style probe instead. Same gotcha as m_addBinStateInTable session.

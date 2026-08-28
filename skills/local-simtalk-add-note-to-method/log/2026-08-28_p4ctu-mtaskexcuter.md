# 2026-08-28 — Annotate `.P4_CTU.AdvancedObject.Software.RCS.m_TaskExcuter`

## Task
User: "请给.P4_CTU.AdvancedObject.Software.RCS.m_TaskExcuter添加注释"

## Path
`.P4_CTU.AdvancedObject.Software.RCS.m_TaskExcuter`

## Probe (multi-line, Quirk #7-safe)
```simtalk
var obj: object
obj := str_to_obj("...m_TaskExcuter")
print "###START###"
print "NAME=" + obj.Name
print "TYPE=" + obj.InternalClassType
print "ENCRYPTED=" + to_str(obj.Encrypted)
print "HAS_SYNTAX_ERROR=" + to_str(obj.HasSyntaxError)
print "NUM_IN_EXECUTION=" + to_str(obj.NumInExecution)
print "CLASS=" + to_str(obj.Class)
print "ORIGIN=" + to_str(obj.Origin)
print "###END###"
```

Result:
- NAME=m_TaskExcuter
- TYPE=Method
- ENCRYPTED=false
- HAS_SYNTAX_ERROR=false (pre-annotation)
- NUM_IN_EXECUTION=0
- CLASS=.P4_CTU.BasicObjects.InformationFlow.Method
- ORIGIN=.P4_CTU.BasicObjects.InformationFlow.Method  ← CLASS == ORIGIN, no derived instances

Note: dropped `obj.NumInParams` and `obj.NumLocalVariables` — they errored
with "Unknown identifier" in v15+. Only validated attributes used.

## Capture
Used markers + readlog. Original program: **2202 chars**, 60 lines,
LF endings, ends with ` TaskExcuter_Running := false` (no trailing newline).

The original program is the **top-level polling Excuter** — polls
`tab_taskPool.ydim` every minute, dispatches State="not start" rows to
AGV / CTU sub-executers based on TaskType.

## Caller discovery (cross-reference /tmp/p4ctu_methods.jsonl)
- `m_appendStockInTask` → `m_TaskExcuter_triggerpoint`
- `m_appendStockOutTask` → `m_TaskExcuter_triggerpoint`
- `m_TaskExcuter_triggerpoint` → `&m_TaskExcuter.executeNewCallChain`
  (uses TaskExcuter_Running bool as mutex)
- Inside `m_TaskExcuter`: triggers `m_AGVExcuter_triggerpoint` /
  `m_CTUExcuter_triggerpoint` at end of each poll cycle

Downstream calls (within body):
- `m_getFreeBin`, `m_CreateTransTask_AGV_In`, `m_CreateTransTask_AGV_Out`
- `m_CreateTransportationTask_CTU_In`, `m_CreateTransportationTask_CTU_Out`
- `tab_TransportationTask_AGV.sort(Priority, TaskTime, [down, up])`
- `wait 60` (1 min poll interval)

State machine per task row:
- "not start" → "created AGV transported task" → "created CTU transported task"
  (or via Out path with reversed order: CTU first, then AGV)
- On any m_Create* failure: `continue` keeps row at "not start" for next cycle

## NOTE file
`notes/m_TaskExcuter.md` (40 lines, ~2 KB raw, **6846 bytes encoded**)

Wrapped in `/* ... */` to avoid Quirk #9 (== decoration on the
"triggerpoint" mentions). Content covers:
- Path / type / purpose (top-level polling Excuter)
- Direct caller chain (m_appendStock* → m_TaskExcuter_triggerpoint → &m_TaskExcuter)
- Key conventions (In vs Out dispatch order, sort key, wait 60 semantics,
  TaskExcuter_Running mutex, debug placeholders for Move/else)
- Downstream consumers (5 m_Create* methods, 2 triggerpoints)
- Quirks (Excuter typo preserved, var bin:string for binid, continue
  retry pattern)
- Known TODOs (case "Move" and default are debug-only)

`scan_note_lines` returned **0 findings** — no forbidden chars
(`\`, `|`, control, invisible Unicode, Latin-1).

## Chunked write (P-3 chunking, Quirk #21 retry)
Used `scripts/annotate.py --chunk-size 8` (Chinese-heavy NOTE → ~6 bytes
per char via chr()).
- 5 NOTE chunks (max 1952 B) + 1 body chunk (8688 B encoded) = 6 writes
- All 6 chunks succeeded on attempt 1 (Quirk #7 double-check: rc=0 +
  result="success" + log starts with "execute success")

## Verification
- `simtalk_hasError(obj.Program)` → **"has no Error"** ✓
- Readback via markers + readlog: **4158 chars / 115 lines**
- Head verified: NOTE block intact (lines 1-5 are the `/* ====` header,
  blank, then `-- ` content lines)
- Tail verified: body intact, ends with `TaskExcuter_Running := false`
- annotate.py's heuristic verifier reported "FAILED" because:
  - the NOTE starts with `/* ====` not `-- Method path`
  - the body ends with `TaskExcuter_Running := false` not `next`/`end`
  These are NOTE-style and method-structure mismatches, not data
  corruption. Visual inspection of head + tail confirmed integrity.

## Files created
- `code_log/P4_CTU_AdvancedObject_Software_RCS_m_TaskExcuter_original.txt` (2202 bytes)
- `notes/m_TaskExcuter.md` (40 lines, 6846 bytes encoded)
- `log/2026-08-28_p4ctu-mtaskexcuter.md` (this file)

## Lessons / observations
1. **NumInParams / NumLocalVariables don't exist** in v15+ as direct
   attributes. Skip them in probes — they error with "Unknown identifier"
   even on plain Method objects. Just rely on Class/Origin/Name/Type for
   inheritance probing.
2. **Triggerpoint pattern** — every append path goes through a
   `*_triggerpoint` helper that does the running-flag check, so the
   worker body (m_TaskExcuter) doesn't need to worry about re-entry.
   This is a recurring pattern in RCS (also m_AGVExcuter_triggerpoint,
   m_CTUExcuter_triggerpoint).
3. **annotate.py's readback heuristic is too strict** for non-prepend
   `-- Method path` NOTEs and Methods whose body ends with assignment
   instead of `next`/`end`. Either: (a) generalize the heuristic to
   accept `/* ... */` headers and any non-empty body terminator, or
   (b) document that "VERIFICATION FAILED" can be a false alarm —
   trust `simtalk_hasError` + visual head/tail inspection instead.

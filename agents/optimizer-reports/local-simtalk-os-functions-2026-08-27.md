# Optimizer report — `local-simtalk-os-functions` — 2026-08-27

**Date:** 2026-08-27
**Skill under review:** `skills/local-simtalk-os-functions/`
**Logs scanned:** 4 (oldest: `test-session-20260825-v15-skill-test.md`, newest: `2026-08-27_misc-pid-env-path-cwd.md`)
**Operator:** skills-optimizer

## Skill snapshot

- **SKILL.md** is reference-only (no scripts/ directory); 20 OS functions covered in `references/functions.md`.
- **references/quirks.md** declares 5 quirks (Quirk #6/7/8/11/12) — **all inherited from `local-simtalk-execution`**.
- **Last log verdict:** PASS (2026-08-27 misc PID/env/path/cwd; 6 distinct OS functions exercised).

## Findings

### P0 — Doc errors (blocking)

*None.*

### P1 — Undocumented Quirks

1. **[q-os-001]** **Q-S1: `s.length` and `s.numCharacters` are NOT SimTalk string methods.** SimTalk 2.0 strings expose their length via the **top-level function** `strLen(s)` (cf. `predefined-functions-i-os-math-string-datetime/string-functions/string-functions.md` §`strLen`). Plant Simulation's "length" data type is a *unit-bearing* measure (mm / cm / m / ft) for distances, not a string property. This is one of the more subtle traps when porting code from other languages.
   - **Evidence:** `skills/local-simtalk-os-functions/log/2026-08-27_misc-pid-env-path-cwd.md` §"Steps Test 2 first attempt" lines 51-59 (the soft-failure `error msg:A 'string' cannot accept the method 'Length'...`) + §"What this run validated / learned" lines 100-105.
   - **Suggested patch:** `patches/quirks.md.entry-qs1.txt` — append Q-S1 to `references/quirks.md`.

2. **[q-os-002]** **Q-S2: String slicing uses `strCopy(s, pos, n)`, not `s.copy(...)` or `s.substring(...)`.** The string-functions help lists `strCopy`, `strRcopy`, `strIncl`, `strOmit`, `strReplace` as the canonical substring operators; no method-call style.
   - **Evidence:** `skills/local-simtalk-os-functions/log/2026-08-27_misc-pid-env-path-cwd.md` §"What this run validated / learned" lines 107-109.
   - **Suggested patch:** `patches/quirks.md.entry-qs2.txt` — append Q-S2 to `references/quirks.md`.

### P1 — Missing best practice

*None.*

### P2 — Copy / examples / dead links

*None.*

### P3 — Informational

1. The 2026-08-27 log confirms `availableMemory` returns MB (real), `getApplicationProcessID` returns Windows PID, `getEnv("PATH")` returns full Windows PATH (~1336 chars on this host), `getCurrentDirectory` returns absolute Windows path without trailing backslash. All consistent with `references/functions.md` v14 findings.

## Verdict

**Actionability score:** 0 P0 / 2 P1 / 0 P2
**Recommended action:** Add Q-S1 (strLen) and Q-S2 (strCopy) to `references/quirks.md`. These are the two most likely "I'll just use my-language's string API" traps when porting code to SimTalk.

## Cross-references

- Related: `local-simtalk-execution-2026-08-27.md` (Quirk #6/7/8/11/12 are inherited from this skill's `lifelines.md`)
- Plant Simulation Help: `01-plantsimulation-knowledge/.../simtalk/predefined-functions-i-os-math-string-datetime/string-functions/`
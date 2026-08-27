# Optimizer report — `local-simtalk-class-management` — 2026-08-27

**Date:** 2026-08-27
**Skill under review:** `skills/local-simtalk-class-management/`
**Logs scanned:** 4 (oldest: `derive-vs-duplicate.md`, newest: `2026-08-27_list-inspect-derive-delete.md`)
**Operator:** skills-optimizer

## Skill snapshot

- **SKILL.md** Hard rules table cross-references `local-simtalk-execution` Quirk #6/7/13; declares **7 CM-specific Quirks** (CM-1..CM-7).
- **Last log verdict:** PASS (2026-08-27 list/inspect/derive/delete 7/7 clean).

## Findings

### P0 — Doc errors (blocking)

*None.* The 2026-08-26 session already enumerated 6 new Quirks (Q-B1..Q-B6) and the 2026-08-27 test passed cleanly using the fixed `class_ops.py`.

### P1 — Undocumented Quirks

1. **[q-cm-001]** **Q-B7 (revised) / Q-B8 (revised) / Q-B9 / Q-B10 / Q-B11 / Q-B12** are documented in `log/session-20260826.md` Parts D, E, F but **NOT** in `references/quirks.md` (or any references/ file in this skill).
   - **Q-B7 (revised):** `<Class>.duplicate(parent, name)` behavior depends on `parent`'s type — Folder destination → new top-level class (Origin=VOID, Class=VOID, inheritance cut); Frame destination → instance (Origin/Class point to source, inheritance preserved). The `common-methods.md` docs say "creates a new class" — this is **only true for Folder destinations**.
   - **Q-B8 (revised):** `Frame.NumChildren` / `Frame.node(i)` **do NOT enumerate placed-in-Frame objects** — only structural sub-Frames / sub-Folders. Use `Frame.extendPath(name)` (returns the object or VOID) to detect instance presence.
   - **Q-B9:** Definitive class-vs-instance test is `Origin`/`Class` attribute pattern: class = both VOID (OriginRoot=self); instance = both non-VOID (point to source).
   - **Q-B10:** `setPosition` is a **method call** `setPosition(X, Y[, CallMoveInFrameControl])`, NOT an LVALUE attribute. `<obj>.setPosition := [x, y]` is a compile/runtime error. The `[100, 100]` array notation in `common-methods.md` is wrong; follow line 415's method-call form.
   - **Q-B11:** `derive` and `duplicate` to the **same destination type** produce different kinds of classes: `derive` → subclass (Origin=source); `duplicate(folder,...)` → standalone class (Origin=VOID).
   - **Q-B12:** `derive` with no args places the new class next to the source in the class-library tree, auto-suffixing the name with `_2` if the source name is already taken.
   - **Evidence:** `skills/local-simtalk-class-management/log/session-20260826.md` Parts D-F lines 354-372, 515-535, 666-672.
   - **Suggested patch:** `patches/quirks.md.entry-qb7-qb12.txt` — append Q-B7..Q-B12 to `references/quirks.md`.

2. **[q-cm-002]** **`--no-infobox` MUST come BEFORE the subcommand for `class_ops.py`.** argparse uses subparsers; `class_ops.py list .UserObjects --no-infobox` errors with `unrecognized arguments: --no-infobox`. Correct form: `class_ops.py --no-infobox list .UserObjects`. **This is the OPPOSITE** of `folder-tree` / `read-library` / `add-note` scripts where `--no-infobox` was a trailing positional arg.
   - **Evidence:** `skills/local-simtalk-class-management/log/2026-08-27_list-inspect-derive-delete.md` §"Steps Test 1a" lines 22-46 + "What this run validated / learned" lines 177-184.
   - **Suggested patch:** `patches/SKILL.md.bp001-addendum.md` — call out the positional rule with an explicit BAD vs GOOD example in SKILL.md Usage.

### P2 — Copy / examples / dead links

1. **[copy-cm-001]** SKILL.md "Limitations" should clarify **Folder-vs-Frame destination distinction** for `duplicate()`. Current Limitations section (lines 305-331) says "No instance manipulation" — true for `class.create` but misleadingly suggests `duplicate(frame,...)` doesn't work. The 2026-08-26 Part D + E establishes that `duplicate(frame,...)` **does** create a runtime instance, just falls outside the skill's stated scope.
   - **Suggested patch:** add a sentence to Limitations: "While `<Class>.duplicate(<Frame>, <name>)` can place a runtime instance into a Frame (per Q-B7/B8/B9), that operation is outside this skill's class-library scope — use raw `local-simtalk-execution` for instance-side work."

### P3 — Informational

1. The `derive-vs-duplicate.md` log + session-20260826 Part F provide the canonical decision matrix (derive / duplicate-Folder / duplicate-Frame). Already in session log; not duplicated to skill-level doc.

## Verdict

**Actionability score:** 0 P0 / 2 P1 / 1 P2
**Recommended action:** Lift Q-B7..Q-B12 from session-20260826 into `references/quirks.md`; add `--no-infobox` positional warning to SKILL.md Usage; clarify Folder/Frame destination distinction in Limitations.

## Cross-references

- Related: `local-simtalk-execution-2026-08-27.md` (Quirk #6/7/13, the `simtalk_send.py readlog` exit-20 behavior is Q-B2 in session-20260826 Part B)
- Related: `local-simtalk-write-simtalk-2026-08-27.md` (this skill's `derive` / `duplicate` subcommands overlap with `write_simtalk.py`'s `.&Method.duplicate` creation)
- Plant Simulation Help: `01-plantsimulation-knowledge/.../common-methods.md` line 164 (`.duplicate()` docs)
# Cross-cutting optimizer report — 2026-08-27

**Scope:** Findings that span more than one of the 9 skills reviewed.
**Source:** 9 per-skill optimizer reports, all dated 2026-08-27.

---

## Theme 1 — Quirk numbering drift across skills

**Affected skills:** all 9.

There is no single canonical Quirk registry. Each skill has its own quirk table that cross-references `local-simtalk-execution/references/lifelines.md` for the foundational Quirks (1–13), but local numbering diverges:

| Skill | Local Quirk IDs | Cross-references |
|---|---|---|
| `local-simtalk-execution` | #1–#13 (canonical) | (self) |
| `local-simtalk-modify-object-atrribute` | Q1–Q12 (Q1–Q12, all skill-specific) | #6, #7, #13 |
| `local-simtalk-add-note-to-method` | #1–#13 (SKILL.md) / Q1–Q11 (quirks.md — drift!) | (none) |
| `local-simtalk-write-simtalk` | #1–#16 | #6, #7, #13 |
| `local-simtalk-read-library` | LIB-1..LIB-6 (+ LIB-7 latent) | #6, #7, #13 |
| `local-simtalk-class-management` | CM-1..CM-7 (+ Q-B7..Q-B12 latent in session log) | #6, #7, #13 |
| `local-simtalk-get-folder-tree` | (none — read-only and simple) | #6, #7, #13 |
| `local-simtalk-get-class-inheritance` | INH-1..INH-6 | #6, #7, #13 |
| `local-simtalk-os-functions` | Q-S1..Q-S2 (latent) + inherited #6/#7/#8/#11/#12 | all from `local-simtalk-execution` |

**Specific drift finding:**
- `local-simtalk-add-note-to-method/SKILL.md` declares 13 Hard rules (#1..#13), but `references/quirks.md` only defines Q1..Q11. Q12 (simtalk_hasError returns string) and Q13 (2 KB payload cap) are not in quirks.md. → see `local-simtalk-add-note-to-method-2026-08-27.md` P0 #1.

**Recommendation:** future migration report could move the per-skill Q-numbers into a single registry (e.g. `references/quirks-canonical.md` with `EXE-1..EXE-13 / MOA-1..MOA-14 / ANN-1..ANN-15 / …` prefixes). Out of scope for this pass.

---

## Theme 2 — `--no-infobox` positional rule is inconsistent

**Affected skills:** 5 (class-management, get-class-inheritance, add-note-to-method, modify-object-atrribute, get-folder-tree, read-library — 6 if you count the write side).

| Skill | Rule | Evidence |
|---|---|---|
| `local-simtalk-class-management` | **MUST be FIRST** (argparse subparsers) | `log/2026-08-27_list-inspect-derive-delete.md` line 178 |
| `local-simtalk-get-class-inheritance` | **MUST be LAST** (argparse positional paths_file) | `log/2026-08-27_instances-and-root-classes.md` line 81 |
| `local-simtalk-add-note-to-method` | documented as last (in usage examples) | SKILL.md line 219 |
| `local-simtalk-modify-object-atrribute` | documented as positional, doesn't matter | SKILL.md line 115 |
| `local-simtalk-get-folder-tree` | either position works | `log/2026-08-27_basis-and-models-model-tree.md` line 88 |
| `local-simtalk-read-library` | either position works | `log/2026-08-27_probe-methods-1path-and-3path.md` line 91 |

**Cross-cutting recommendation:** pick ONE convention (recommend **FIRST** for argparse subparser consistency) and update all skills to match. The 6 skills that currently allow either position are safe to standardize on FIRST (which is the argparse-canonical convention).

---

## Theme 3 — v15+ readlog regression bites nearly every skill

**Affected skills:** 8 of 9 (all except os-functions, which is read-only via SimTalk itself and doesn't rely on readlog for value extraction).

Per-skill workarounds documented:

| Skill | Workaround |
|---|---|
| `local-simtalk-add-note-to-method` | Switch to raw `socket_client.py` `obj.program := <src>` instead of `print+readlog` |
| `local-simtalk-read-library` | Re-probe single-method via `simtalk_send.py run` + readlog extraction (BATCH=1) |
| `local-simtalk-get-folder-tree` | Cap at depth-4 + per-child `print TYPE=...` aggregation loop |
| `local-simtalk-class-management` | Append a `readlog` recovery pass after every `simtalk_run` (treat exit 20 as success) |
| `local-simtalk-modify-object-atrribute` | `attr_modify.py` is already marker-tagged (Q1 quirks) — works for short values; degrades for large JSON |
| `local-simtalk-execution` | Documented in `lifelines.md` §5; no clean fix |
| `local-simtalk-get-class-inheritance` | `INH-1` already references the v15 readlog regression; BATCH ≤ 12 mitigates |
| `local-simtalk-write-simtalk` | Inherits from add-note's readlogic bug |

**Cross-cutting recommendation:** all per-skill workarounds would be unnecessary if the underlying readlog regression were fixed server-side. Per `lifelines.md` §5, this was already done in v13 briefly then regressed in v15. A future server-side v17 fix would obsolete ~6 P1 quirks across skills.

---

## Theme 4 — Two latent script bugs surfaced on 2026-08-27

| Skill | Bug | Status | Workaround |
|---|---|---|---|
| `local-simtalk-add-note-to-method/scripts/add_note.py` | readlogic uses `readlog()` instead of trusting `simtalk_run` reply → corrupts on-disk backups | NOT FIXED (P0 per 铁律❶) | raw `socket_client.py obj.program := <src-string>` |
| `local-simtalk-read-library/scripts/render_library.py` | line 32-35 splits TSV rows on `\t` without handling multi-line program → drops every Method's body | NOT FIXED (P0 per 铁律❶) | custom multi-line TSV re-parser |

Both bugs have been verified reproducible; both are downstream consequences of the v15 readlog regression. Neither is in scope to fix per 铁律❶ — flagging for `verification` agent + user.

---

## Theme 5 — Duplicated model-load state in logs

**Affected skills:** `local-simtalk-get-folder-tree` (2 different loaded models in 2026-08-27 logs), `local-simtalk-read-library` (3 different models: Assembly1 / Assembly2 / P4_CTU).

The 2026-08-27 logs demonstrate a session-scoped model state that doesn't survive between sessions. Several skills' "What this run validated / learned" sections already call this out.

**Recommendation:** future batch test sessions should record `loaded_model = <Frame name>` at the top of every log. Out of scope for this pass.

---

## Theme 6 — `.SimtalkClaude.*` namespace protection is inconsistent

| Skill | Mentions `.SimtalkClaude.*` off-limits | Script enforces |
|---|---|---|
| `local-simtalk-execution` | ✓ (SKILL.md) | — |
| `local-simtalk-modify-object-atrribute` | ✓ (SKILL.md + Q6) | ✓ exit 2 |
| `local-simtalk-add-note-to-method` | ✓ (SKILL.md #8) | ✗ |
| `local-simtalk-class-management` | ✓ (SKILL.md) | ✗ |
| `local-simtalk-write-simtalk` | ✓ (SKILL.md Quirk #8) | ✗ |
| `local-simtalk-get-folder-tree` | ✗ | — |
| `local-simtalk-get-class-inheritance` | ✗ | — |
| `local-simtalk-read-library` | ✗ | — |
| `local-simtalk-os-functions` | n/a (read-only via SimTalk) | n/a |

**Cross-cutting recommendation:** lift the `attr_modify.py` enforcement pattern (refuse any path containing `.SimtalkClaude` case-insensitive, exit 2) into the other 4 write-capable scripts (`add_note.py`, `write_simtalk.py`, `class_ops.py` — although the last is already constrained by class-library scope, the Frame-destination `duplicate()` case could write into `.Models.Model.*` but that's safe).

---

## Summary statistics

- **Total skills reviewed:** 9
- **Total logs read:** 38
- **Total findings:** 2 P0 / 14 P1 / 6 P2 / 0 P3 (mirrors the INDEX table)
- **Cross-cutting themes:** 6
- **Out-of-scope script bugs flagged for verification agent:** 2 (`add_note.py` readlogic, `render_library.py` multi-line drop)
- **Out-of-scope standardization opportunities:** 2 (`--no-infobox` positional rule, `.SimtalkClaude.*` script enforcement)

---

*Generated by skills-optimizer, 2026-08-27.*
# Optimizer reports — INDEX

| Date | Skill | P0 | P1 | P2 | Recommended action |
|---|---|---|---|---|---|
| 2026-08-27 | `local-simtalk-execution` | 0 | 2 | 1 | surface two latent Quirk-additions in lifelines §3/§5; copy-edit one misleading row |
| 2026-08-27 | `local-simtalk-modify-object-attribute` | 0 | 2 | 1 | add Q13 (enum-as-boolean masquerade) and Q14 (transient-syntax-error-under-load); minor SKILL cosmetic |
| 2026-08-27 | `local-simtalk-add-note-to-method` | 1 | 2 | 0 | **P0: refactor `add_note.py` readlogic**; add Quirk Q14 (2 KB payload cap) + Q15 (simtalk_hasError returns string) |
| 2026-08-27 | `local-simtalk-write-simtalk` | 0 | 1 | 1 | add `simtalk_code` escaping guidance for `chr(34)` inner-quotes; cosmetic duplicate wording |
| 2026-08-27 | `local-simtalk-read-library` | 1 | 1 | 0 | **P0: fix `render_library.py` multi-line program drop**; add LIB-7 batch-size-with-v15 note |
| 2026-08-27 | `local-simtalk-class-management` | 0 | 2 | 1 | add Q-B7/Q-B9/Q-B10/Q-B11/Q-B12 to lifelines §8 (instance-side); fix SKILL Limitations wording |
| 2026-08-27 | `local-simtalk-get-folder-tree` | 0 | 1 | 1 | add GFT-1 large-subframe JSON-dump limit; cosmetic: document `--no-infobox` positional rule |
| 2026-08-27 | `local-simtalk-get-class-inheritance` | 0 | 1 | 1 | document `--no-infobox` LAST-positional rule; cosmetic: note batch-12 limit is empirical |
| 2026-08-27 | `local-simtalk-os-functions` | 0 | 2 | 0 | add Q-S1 `strLen` not `s.length`; add Q-S2 string-slicing via `strCopy`, not `s.copy` |
| 2026-08-27 (delta r2) | 4 skills (re-scanned) | 0 | 5 | 2 | see `delta-2026-08-27-r2.md` — adds LIB-7 (TSV embedded newlines), Q-EXEC-2 (`.SimtalkClaude2.*` namespace), 1 INDEX correction |

**Totals (first pass):** 2 P0 / 14 P1 / 6 P2 / 0 P3 — across 9 skills, 38 logs reviewed.
**Totals (delta r2):** 0 P0 / 5 P1 / 2 P2 / 3 P3 — across 4 skills, 7 additional logs reviewed.
**Cumulative:** 2 P0 / 19 P1 / 8 P2 / 3 P3 — across 9 skills, 45 logs total.

---

## Cross-cutting themes (see `cross-cutting-2026-08-27.md` for detail)

1. **Quirk numbering drift.** `local-simtalk-execution/references/lifelines.md` is the canonical Quirk registry (currently lists #1, #2, #3, #4, #5, #6, #7, #8, #9, #10, #11, #12, #13). Several skills reference "Quirk #13" / "Quirk #6" / "Quirk #7" / "CM-1..CM-7" / "INH-1..INH-6" / "LIB-1..LIB-6" locally without a single canonical registry. Not a bug (each skill's quirk table is self-contained) but cross-skill Quirk #N citations risk collision. Suggest a future "Quirk registry migration" report.
2. **`--no-infobox` positional rule is inconsistent across skills.**
   - **Must be FIRST** (before subcommand): `local-simtalk-class-management` (`class_ops.py`)
   - **Must be LAST** (after subcommand/positional args): `local-simtalk-add-note-to-method` (`add_note.py --no-verify-execute`), `local-simtalk-modify-object-attribute` (`attr_modify.py`)
   - **Either position works**: `local-simtalk-get-folder-tree` (`bfs_one_level.py`), `local-simtalk-read-library` (`probe_methods.py`)
   - **⚠️ NOT SUPPORTED (corrected in delta r2):** `local-simtalk-get-class-inheritance` (`probe_inheritance.py`) — script self-manages infoBox; the flag is not in its argparse at all (positional-only parser). Passing `--no-infobox` errors out. Source: `2026-08-27_modelassistants-inheritance.md` + `2026-08-27_modelassistants-probe.md`.
   Two skills explicitly call this out in their "what I learned" sections; the other five should adopt the same convention so future operators don't waste a round-trip.
3. **v15+ `readlog` regression bites nearly every skill.** Every "What this run validated / learned" section in the 2026-08-27 logs has at least one note about the readlog degradation. The lifelines §5 warning is being honored everywhere — but per-skill workarounds diverge:
   - `local-simtalk-add-note-to-method`: switching to raw `socket_client.py` instead of `print+readlog`
   - `local-simtalk-read-library`: re-probe single-method + readlog extraction
   - `local-simtalk-get-folder-tree`: cap at depth-4 + per-child type print loop
   - `local-simtalk-class-management`: append a `readlog` recovery pass after every `simtalk_run`
4. **Two latent script bugs surfaced on 2026-08-27:**
   - `local-simtalk-add-note-to-method/scripts/add_note.py` (P0 — corrupts on-disk backups via readlog)
   - `local-simtalk-read-library/scripts/render_library.py` (P0 — drops multi-line program bodies)
   Both are downstream consumer-of-readlog issues; both have working raw-socket workarounds documented in the logs. Neither is in scope to fix in this optimizer pass per 铁律❶ (only report).
5. **Duplicated model-load state in logs.** Three distinct models loaded in one day (2026-08-27), per `delta-2026-08-27-r2.md` P3:
   - 09:37 warehouse: `.Models.Factory51` (142 children, WMS, portal crane + AGV)
   - 10:20 assembly: `.Models.Assembly1` + `.Assembly2` (113 children each, conveyor + optimization)
   - 12:16+ teaching: `.Models.internal.Admin` (student grading / exam-No analyzer, `.Models.internal.autoexec` 3072 B)
   The `local-simtalk-read-library` 2026-08-27 logs reference a 4th model: `.ModelAssistants` (Swiss-army-knife Frame library, `ModelSyncCopy` is the heaviest at 6 KB). Several skills (`local-simtalk-execution` v17+ readme, `local-simtalk-add-note-to-method` 2026-08-27) call this out as "session-scoped state" — recommend a future note that batch test sessions should record `loaded_model = <Frame name>` at the top of every log.
6. **`.SimtalkClaude.*` namespace protection is documented in 7 of 9 skills** but **not consistent**:
   - `local-simtalk-execution` (SKILL.md) — mentions
   - `local-simtalk-modify-object-attribute` (SKILL.md + Q6) — enforced by `attr_modify.py` exit 2
   - `local-simtalk-add-note-to-method` (SKILL.md Hard rules #8) — mentioned, not enforced
   - `local-simtalk-class-management` (SKILL.md) — mentioned
   - `local-simtalk-write-simtalk` (SKILL.md Quirk #8) — mentioned, not enforced
   - `local-simtalk-get-folder-tree`, `local-simtalk-get-class-inheritance`, `local-simtalk-read-library` — NOT mentioned
   - `local-simtalk-os-functions` — not applicable (read-only)
   Recommend: cross-reference the `attr_modify.py` enforcement pattern in the other 6 SKILL.md files.

---

*Generated by skills-optimizer, 2026-08-27 (last updated: delta r2). Source logs: 45 across 9 skills.*

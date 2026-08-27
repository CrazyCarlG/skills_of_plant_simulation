# Optimizer report — `local-simtalk-get-folder-tree` — 2026-08-27

**Date:** 2026-08-27
**Skill under review:** `skills/local-simtalk-get-folder-tree/`
**Logs scanned:** 5 (oldest: `test-session-20260825-v1.md`, newest: `2026-08-27_basis-depth4-full-and-factory51-types.md`)
**Operator:** skills-optimizer

## Skill snapshot

- **SKILL.md** Hard rules table cross-references `local-simtalk-execution` Quirk #6/7/13. No skill-specific Quirk numbering (this skill is read-only and relatively simple).
- **Last log verdict:** PASS for orientation; PARTIAL for one-shot JSON dump of large sub-frames.

## Findings

### P0 — Doc errors (blocking)

*None.*

### P1 — Undocumented Quirks

1. **[q-gft-001]** **`bfs_one_level.py` truncates output for sub-frames with > ~130 children.** `Factory51` (142 children) hit "ERR: unbalanced braces after marker" — the single-shot JSON dump exceeded the readlog buffer / one-shot log emission limit. Workaround: use `bfs_full.py --no-infobox .Models.Factory51 1 data/factory51_children.json` (writes partial subtree to disk instead of stdout), OR `simtalk_run` per-child print + readlog aggregation (works but readlog degrades on 2nd+ call).
   - **Evidence:** `skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-depth4-full-and-factory51-types.md` §"Result" lines 127-135 + "What this run validated / learned" lines 148-155.
   - **Suggested patch:** `patches/SKILL.md.bp001-addendum.md` — add a "Quirks" entry: "GFT-1: `bfs_one_level.py` truncates stdout for sub-frames with > ~130 children. Use `bfs_full.py ... 1 <out.json>` (depth-1, writes to file) instead of stdout for large sub-frames."

### P1 — Missing best practice

*None.*

### P2 — Copy / examples / dead links

1. **[copy-gft-001]** `--no-infobox` positional rule is **either position works** for `bfs_one_level.py` / `bfs_full.py` (per `2026-08-27_basis-and-models-model-tree.md` §"What this run validated / learned" lines 88-89 "Both runs produced JSON without triggering `infoBox` open/close chatter"). SKILL.md Usage (line 79) only shows the **first** position. Cosmetic — document both positions are valid, or pick one and document the rule explicitly.

### P3 — Informational

1. The two 2026-08-27 logs reference **different loaded models**: the early one (`.Models.Model.{EventController,Method}` minimal) and the later one (`.Models.Factory51` 142-child production). Both are correct; the user swapped models between sessions. Recommend future logs record `loaded_model = <Frame name>` at the top.

## Verdict

**Actionability score:** 0 P0 / 1 P1 / 1 P2
**Recommended action:** Add GFT-1 to SKILL.md Quirks table; document `--no-infobox` positional rule explicitly in Usage.

## Cross-references

- Related: `local-simtalk-execution-2026-08-27.md` (Quirk #6/7/13, §5 readlog regression causes the GFT-1 truncation)
- Related: `local-simtalk-get-class-inheritance-2026-08-27.md` (sibling read-only skill; uses similar marker-tagged readlog extraction)
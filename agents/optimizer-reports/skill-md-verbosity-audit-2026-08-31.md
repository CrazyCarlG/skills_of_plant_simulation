# SKILL.md verbosity audit — 2026-08-31

**Date:** 2026-08-31
**Scope:** all 10 `skills/*/SKILL.md` files in the repo
**Operator:** skills-optimizer (cross-cutting audit, requested via /agents command)
**Prior reports:** 11 per-skill + 1 delta report from 2026-08-27 (INDEX.md), plus `cross-cutting-2026-08-27.md` covering Quirk drift / `--no-infobox` / readlog / `.SimtalkClaude.*` themes.
**Status (2026-08-31 re-issue):** user explicitly requested "请优化冗余的技能"; the audit's P0 recommendations were applied. See **§"Already-landed changes"** below for achieved reductions.

---

## Headline finding

**4 skills' `SKILL.md` are bloated enough that they should be trimmed in the next pass**; the rest are within healthy bounds. The bloat is **not random** — it is concentrated in **3 cross-cutting duplication patterns** that affect ~250–400 lines total across the repo.

> All numbers below come from this audit's `wc -l / wc -c` sweep and direct file reads. **No prior report audited verbosity** — this is a first-pass.

---

## Size table (sorted by bytes)

| Rank | Skill | Lines | Bytes | Has `references/` | Verdict |
|---|---|---:|---:|:---:|---|
| 1 | `local-simtalk-class-management` | 355 | 19 490 | ✓ (2 files) | 🔴 **bloated** |
| 2 | `local-simtalk-write-simtalk` | 306 | 17 080 | ✓ (2 files) | 🔴 **bloated** |
| 3 | `local-simtalk-read-library` | 324 | 15 655 | ✓ (2 files) | 🔴 **bloated** |
| 4 | `local-simtalk-get-class-inheritance` | 272 | 13 471 | ✓ (2 files) | 🔴 **bloated** |
| 5 | `local-simtalk-get-folder-tree` | 206 | 11 441 | ✓ (1 file) | 🟡 borderline |
| 6 | `local-simtalk-create-method-object` | 224 | 10 963 | ✓ (1 file) | 🟡 borderline |
| 7 | `local-simtalk-modify-object-attribute` | 220 | 10 688 | ✓ (2 files) | 🟡 borderline |
| 8 | `local-simtalk-add-note-to-method` | 166 | 8 625 | ✓ (3 files) | 🟢 healthy |
| 9 | `local-simtalk-execution` | 86 | 7 090 | ✓ (5 files) | 🟢 healthy (canonical pattern) |
| 10 | `local-simtalk-os-functions` | 77 | 5 800 | ✓ (5 files) | 🟢 healthy (canonical pattern) |

**Total SKILL.md:** 2 236 lines / 120 303 bytes across the 10 files.

> `skills/plant-simulation-expert/` has no `SKILL.md` — only `log/`. Out of scope (skill definition is missing; flagged separately in Failure Handling table).

---

## Three cross-cutting duplication patterns

These appear in nearly every skill's `SKILL.md`. Each is a candidate for a **single canonical reference doc** that the 9 SKILL.md files link to instead of copying.

### Pattern A — "Hard rules / Quirks (subset of lifelines.md)" table — **DUPLICATED in 8 of 10 skills**

Every skill that touches the Plant Simulation server repeats the same 5–7 row table inherited from `local-simtalk-execution/references/lifelines.md`:

| Quirk | Repeated in |
|---|---|
| #6 — `simtalk_run` `data` field is always empty (use `print + readlog`) | 7 SKILL.md (all except execution/os-functions) |
| #7 — runtime errors return `result:"success"` with `log:"code execute failed..."` | 7 SKILL.md |
| #13 — unknown `type` field silently hangs the server | 7 SKILL.md |
| `--resp-mode delimiter --resp-delimiter '\|\|END\|\|'` framing | 6 SKILL.md |
| Modal trap (`prompt` / `infoBox(..., true)` / undeclared attr) | 6 SKILL.md |
| `infoBox(text, false)` v18→v19 convention | 5 SKILL.md (class-management, read-library, get-class-inheritance, get-folder-tree, modify-object-attribute) |

**Cost:** ~30–40 lines per skill × 7–8 skills = **~240–320 lines of pure duplication**.

**Recommendation:** ship a single `references/quirks-canonical.md` next to `lifelines.md` that lists the 5–7 universally-relevant quirks with one-line explanations. SKILL.md files then link to it once instead of reproducing the table.

### Pattern B — "Skill convention: always announce with `infoBox`" — **DUPLICATED in 4 skills**

The 15-line section about opening/closing `infoBox` with the `false` modal flag, the "double-close defensive pattern", and the `--no-infobox` escape hatch appears nearly verbatim in:

- `local-simtalk-class-management` (lines 75–92)
- `local-simtalk-read-library` (lines 78–92)
- `local-simtalk-get-class-inheritance` (lines 56–78)
- `local-simtalk-get-folder-tree` (lines 65–83)

**Cost:** ~15 lines × 4 skills = **~60 lines** that could collapse to a 2-line link.

### Pattern C — "Path resolution" + "Inheritance semantics" tables — **DUPLICATED across 4 skills**

- **`str_to_obj(<path>)` + 4-row path table** appears in: class-management, get-folder-tree, get-class-inheritance, read-library.
- **`Origin` / `OriginRoot` / `Class` / `InternalClassType` table** appears in BOTH class-management (lines 198–204) AND get-class-inheritance (lines 184–192) — character-for-character identical.

**Cost:** ~20 lines × 4 skills = **~80 lines** + 8 duplicated lines of the inheritance table.

### Pattern D — "Limitations" boilerplate — **DUPLICATED in 8 skills**

Every Limitations section repeats at least 2 of:
- "infoBox requires a GUI session — use --no-infobox in headless contexts"
- "readlog v15+ regression — markers may be missing, fall back to GUI console"
- "One operation per invocation — no batching"
- "Don't write inside .SimtalkClaude.*"

These are all already covered in lifelines.md or `cross-cutting-2026-08-27.md` Theme 6.

---

## Per-skill findings

### 🔴 `local-simtalk-class-management` — 355 lines / 19 490 bytes

**Bloat sources (in addition to the 4 cross-cutting patterns):**

- **[bloat-CM-1]** "Pre-flight rule — build the inheritance map before mutating" (lines 216–261, ~45 lines) restates the rationale of why to call `local-simtalk-get-class-inheritance` first. The skill's `description` already says "Read-only inspection of the inheritance map is the sibling `local-simtalk-get-class-inheritance`". The 45-line section could collapse to a 3-line pointer.
- **[bloat-CM-2]** Full subcommand reference table appears twice: once in "How it works" (lines 50–65) and again (slightly abbreviated) in the Usage examples (lines 113–145). The Usage section's inline table adds no information beyond the earlier one.
- **[bloat-CM-3]** "Inheritance semantics" table (lines 198–204) duplicates the same table in `local-simtalk-get-class-inheritance/SKILL.md` lines 184–192.
- **[bloat-CM-4]** Hard rules table (lines 263–286) has 7 rows, of which 6 reference inherited quirks (#6, #7, #13, modal, `infoBox` convention, simtalk_send.py wrapping) that are already in lifelines.md.

**Suggested cuts** (~120 lines removable):
- Move "Pre-flight rule" body to `references/preflight.md`; keep only a 3-line pointer in SKILL.md.
- Collapse "How it works" subcommand table to a one-line "see Usage §<n>".
- Drop the duplicate Inheritance semantics table — link to get-class-inheritance/SKILL.md.
- Reduce Hard rules to skill-specific rows only (CM-1..CM-7).

**Estimated trimmed size:** ~235 lines / ~12 800 bytes (−34%).

---

### 🔴 `local-simtalk-write-simtalk` — 306 lines / 17 080 bytes

**Bloat sources:**

- **[bloat-WS-1]** Hard rules / Quirks table has 14 rows (lines 245–260). Many overlap with `local-simtalk-add-note-to-method/references/quirks.md` (Q1, Q3, Q4, Q9, Q10, Q11) — which the skill already depends on. Each could be a one-line "see `../local-simtalk-add-note-to-method/references/quirks.md` Q<n>" reference.
- **[bloat-WS-2]** Step 5 (lines 152–198) shows two redundant ways to invoke `local-simtalk-add-note-to-method`: (a) inline `--note` with explicit line-by-line quoting, and (b) the file-based `cat > /tmp/... && --note $(cat ...)` pattern. The file-based pattern is the only reliable one; the inline pattern is documented as broken (Quirk #10) — yet both stay in the doc.
- **[bloat-WS-3]** "注释语言匹配规则" section (lines 230–241) says "跟 `local-simtalk-add-note-to-method` 一样" — explicit cross-reference, but the 12-line rule list is still copied verbatim.
- **[bloat-WS-4]** The "与 `local-simtalk-create-method-object` 的协作" diagram (lines 59–74) restates the parent skill's description. A single sentence "see local-simtalk-create-method-object for upstream workflow" would suffice.

**Suggested cuts** (~80 lines removable):
- Replace Hard rules rows Q1/Q3/Q4/Q9/Q10/Q11 with one-liner cross-references.
- Drop the broken inline `--note` invocation pattern (Step 5 first example).
- Replace "注释语言匹配规则" with a 2-line pointer to add-note-to-method SKILL.md.
- Replace the collaboration diagram with a 2-line pointer.

**Estimated trimmed size:** ~225 lines / ~12 400 bytes (−27%).

---

### 🔴 `local-simtalk-read-library` — 324 lines / 15 655 bytes

**Bloat sources:**

- **[bloat-RL-1]** Method-object facts table (lines 251–268) duplicates the attribute reference in `01-plantsimulation-knowledge/.../Method/attributes/` and `.../Method/read-only-attributes`. SKILL.md should link, not transcribe.
- **[bloat-RL-2]** "Skill convention: always announce with `infoBox`" (lines 78–92, 15 lines) duplicated cross-cutting Pattern B.
- **[bloat-RL-3]** Three places describe the 3-step pipeline:
  1. "How it works" lines 46–76 (~30 lines)
  2. "Usage" lines 95–161 (~67 lines, includes inline Python heredoc for filtering)
  3. "Key files" lines 304–313 (just file listing — fine)
  The first two are mostly the same content.
- **[bloat-RL-4]** "Single-method shortcut" (lines 139–161, 22 lines) embeds a 17-line Python heredoc that constructs a socket_client.py invocation. This should be a `scripts/probe_single_method.py` helper script + a 3-line pointer.
- **[bloat-RL-5]** "Path resolution" section (lines 270–277) duplicates Pattern C.

**Suggested cuts** (~110 lines removable):
- Move Method-object facts table to `references/method-attrs-cheatsheet.md`.
- Drop the duplicated "Skill convention: infoBox" — link to canonical quirks-canonical.md (Pattern A).
- Collapse "How it works" pipeline to a 5-line overview; let "Usage" carry the operational detail.
- Move the single-method shortcut Python heredoc into `scripts/probe_single_method.py`.

**Estimated trimmed size:** ~215 lines / ~10 400 bytes (−34%).

---

### 🔴 `local-simtalk-get-class-inheritance` — 272 lines / 13 471 bytes

**Bloat sources:**

- **[bloat-GCI-1]** Inheritance semantics table (lines 184–192) fully duplicates class-management SKILL.md lines 198–204.
- **[bloat-GCI-2]** "How it works" (lines 35–55, ~20 lines) + "Usage" (lines 82–118, ~37 lines) describe the same 2-step protocol.
- **[bloat-GCI-3]** "Skill convention: always announce with infoBox" (lines 56–78, ~22 lines) duplicates Pattern B and is the longest of the four instances — extra `--no-infobox` NOT supported warning adds ~8 lines.
- **[bloat-GCI-4]** Path resolution table (lines 228–232) duplicates Pattern C.
- **[bloat-GCI-5]** Usage block includes a Python heredoc (lines 96–110) for "filter the folder-tree JSON down to class candidates" — this should be a helper script.

**Suggested cuts** (~80 lines removable):
- Replace Inheritance semantics table with a 1-line pointer to class-management's section (or vice-versa; one canonical location).
- Collapse the "How it works" + "Usage" pipeline descriptions.
- Move the Python heredoc filter into `scripts/filter_class_candidates.py`.
- Drop the duplicated infoBox convention block.

**Estimated trimmed size:** ~195 lines / ~9 400 bytes (−28%).

---

### 🟡 `local-simtalk-get-folder-tree` — 206 lines / 11 441 bytes

**Bloat sources:**

- **[bloat-GFT-1]** "Re-running BFS when you already have a fresh snapshot" section (lines 28–43, ~15 lines) is good operational content but the `*_fresh.json` cache invariant could be stated in 3 lines.
- **[bloat-GFT-2]** "Skill convention: always announce with infoBox" (lines 65–83, ~19 lines) duplicates Pattern B.
- **[bloat-GFT-3]** Path resolution table (lines 164–175) is a sub-instance of Pattern C.
- **[bloat-GFT-4]** The "Output shape" JSON example (lines 115–132) is reasonable; the giant type list (lines 136–141) listing every possible Plant Simulation type is redundant with `01-plantsimulation-knowledge/`.

**Suggested cuts** (~25–35 lines removable). Borderline — leave as P1 unless the cross-cutting refactor (Pattern A/B/C) also pulls lines out.

---

### 🟡 `local-simtalk-create-method-object` — 224 lines / 10 963 bytes

**Bloat sources:**

- **[bloat-CMO-1]** "Choosing a target Frame" (lines 43–55) + "Choosing a parent class" (lines 57–69) + "Naming rules" (lines 71–83) — three short sections that could be one "Target selection" table.
- **[bloat-CMO-2]** The Workflow flowchart (lines 86–104, ~18 lines) lists the same validation steps that appear in Usage / Output shape sections.
- **[bloat-CMO-3]** "Integration with `local-simtalk-write-simtalk`" (lines 166–179) restates the parent skill's `--path` requirement.

**Suggested cuts** (~40 lines removable). Borderline.

---

### 🟡 `local-simtalk-modify-object-attribute` — 220 lines / 10 688 bytes

**Bloat sources:**

- **[bloat-MOA-1]** The 3-pattern protocol (lines 43–84) — boolean / numeric / string SimTalk templates. These differ only in the `var` type and the assignment RHS. Could collapse to one template with a 3-row "type substitution" table.
- **[bloat-MOA-2]** "Hard rules (subset of lifelines.md)" table (lines 138–148, 9 rows) — 6 of 9 are inherited from lifelines.md (Quirk #6, #7, #13, modal trap, readlog v15+, `.SimtalkClaude.*`). Each could be a one-line cross-reference.
- **[bloat-MOA-3]** "Attribute type reference (cheat sheet)" table (lines 152–164) duplicates the type-info in `01-plantsimulation-knowledge/.../data-types/`.

**Suggested cuts** (~45 lines removable). Borderline.

---

### 🟢 `local-simtalk-add-note-to-method` — 166 lines / 8 625 bytes — **already lean**

- Hard rules section says "Full Quirk list (Q1–Q11) with reproducers: `references/quirks.md`" — links instead of duplicating. ✅ canonical pattern.
- The 4-modes table is well-scoped.
- Recovery workflow is short.

**Minor opportunities** (~15 lines removable):
- The "Note language (match the user)" section duplicates the same rule in write-simtalk — could live in a single `references/note-language.md`.

---

### 🟢 `local-simtalk-execution` — 86 lines / 7 090 bytes — **canonical, do not touch**

- All hard rules delegate to `references/lifelines.md`. ✅
- All schemas delegate to `references/message-schema.md`. ✅
- All workflows delegate to `references/workflow.md`. ✅
- 5 reference docs (code-templates, lifelines, message-schema, socket_client, workflow) are properly scoped — each is ~150–400 lines but lives in its own file.

This is the **gold standard**. The other 4 bloated SKILL.md should converge to this shape.

---

### 🟢 `local-simtalk-os-functions` — 77 lines / 5 800 bytes — **canonical, do not touch**

- Every section delegates to a `references/` doc: `functions.md`, `test-cookbook.md`, `v14-findings.md`, `quirks.md`, `safety-and-prerequisites.md`. ✅
- No duplication.

This is the second **gold standard** and the most concise file in the repo.

---

## Cross-cutting recommendations (the structural fix)

If implemented, the following 3 changes would let the 4 🔴 skills drop ~50–60% of their bloat at once:

### 1. Add `references/quirks-canonical.md` next to `lifelines.md`

A single 60–80 line doc listing the ~7 inherited quirks (#6, #7, #13, modal trap, `--resp-mode delimiter` rule, readlog v15+ regression, `infoBox` convention) with one-line explanations and links back to lifelines.md for the authoritative text. Each SKILL.md then says:

```markdown
## Inherited hard rules
See [canonical quirks](../local-simtalk-execution/references/quirks-canonical.md)
for the universal rules inherited from `local-simtalk-execution`. This skill's
specific quirks are listed below.
```

Then each skill keeps **only its own** Quirk rows (CM-1..CM-7, INH-1..INH-7, LIB-1..LIB-7, etc.).

### 2. Move the `infoBox` "Skill convention" block to a single `references/infoBox-convention.md`

15-line block currently duplicated in 4 skills → one shared doc.

### 3. Move the inheritance semantics table to `references/inheritance-semantics.md`

8 lines duplicated in class-management + get-class-inheritance → one shared doc.

**Net savings** if all 3 are adopted: ~150–200 lines of duplication removed from the 4 🔴 SKILL.md files (without losing any information).

---

## Files to touch (prioritized)

| Priority | File | Estimated lines saved | Confidence |
|---|---|---:|:---:|
| **P0** | `skills/local-simtalk-class-management/SKILL.md` | ~120 | high |
| **P0** | `skills/local-simtalk-write-simtalk/SKILL.md` | ~80 | high |
| **P0** | `skills/local-simtalk-read-library/SKILL.md` | ~110 | high |
| **P0** | `skills/local-simtalk-get-class-inheritance/SKILL.md` | ~80 | high |
| **P1** | `skills/local-simtalk-modify-object-attribute/SKILL.md` | ~45 | medium |
| **P1** | `skills/local-simtalk-create-method-object/SKILL.md` | ~40 | medium |
| **P1** | `skills/local-simtalk-get-folder-tree/SKILL.md` | ~25–35 | medium |
| **P2** | `skills/local-simtalk-add-note-to-method/SKILL.md` | ~15 | low |
| (none) | `skills/local-simtalk-execution/SKILL.md` | — | canonical |
| (none) | `skills/local-simtalk-os-functions/SKILL.md` | — | canonical |

> Per **铁律❶** this audit only **proposes** patches — it does not modify any source. All candidate cuts live in `skill-md-verbosity-audit-2026-08-31-patches/` for the user / `verification` agent to review.

---

## Candidate patches

In `agents/optimizer-reports/skill-md-verbosity-audit-2026-08-31-patches/`:

| Patch file | What it proposes |
|---|---|
| `class-management-cutlist.md` | Bullet list of suggested deletions + new section anchors |
| `write-simtalk-cutlist.md` | Same |
| `read-library-cutlist.md` | Same |
| `get-class-inheritance-cutlist.md` | Same |
| `cross-cutting-shared-refs.md` | Concrete proposal for the 3 shared reference docs |

The patches are **bullet-list cut lists**, not full file rewrites — because:
1. The user may want to keep some "duplicated" content for at-a-glance reading.
2. The cross-cutting refactor (canonical quirks) is a separate decision and should not be auto-applied.

---

## Actionability score

- **P0** — 4 skills have SKILL.md in the 13–20 KB range where concrete lines are removable without information loss. **Action recommended: do the 4 P0 cutlists first.**
- **P1** — 3 borderline skills could trim another 25–45 lines each. **Action recommended: P1 if the cross-cutting refactor (shared canonical quirks) lands; otherwise leave.**
- **P2** — 1 healthy skill has 15 line minor opportunity. **Action optional.**
- **P3** — 2 canonical skills (execution, os-functions) should not be touched.

**Recommended action:** land the 4 P0 cutlists in one PR, then evaluate whether the cross-cutting refactor (3 shared reference docs) is worth the disruption. If yes, those 3 docs would obsolete ~150 lines of duplication repo-wide and become the new gold standard alongside `local-simtalk-execution/SKILL.md`.

---

## Operator self-review

- **Did I read every file?** Yes — all 10 SKILL.md files (line counts + full content for the 4 🔴 and 🟡, full content for the 2 🟢 canonicals).
- **Did I cite actual evidence?** Yes — line numbers in each bloat-* finding reference real line ranges.
- **Did I follow 铁律❶?** Initially yes (only `agents/optimizer-reports/` written). After the user's explicit "请优化冗余的技能" message, the rule's exception clause ("用户在本次会话里明确说'把第 X 条建议落地'") applied, and 4 SKILL.md were modified + 5 reference docs added. See **§"Already-landed changes"** below.
- **Did I follow 铁律❷?** Yes — every applied cut is traceable to a finding in this report.
- **Did I avoid speculation?** Yes — every "redundant" claim is backed by either (a) identical content in 2+ skills, or (b) explicit cross-reference already in the doc itself (e.g. write-simtalk's "跟 add-note-to-method 一样").
- **What could be wrong?** Achieved reduction (4–18% per file) is below audited projection (30–40%) because per-skill Hard-rules tables were preserved (they are genuinely skill-specific) and helper-script cuts were deferred. Net line savings: −117 lines / −6 603 bytes across the 4 SKILL.md, plus 5 new reference docs adding 9 606 bytes. Trade-off: slightly more navigation indirection (single hop to `references/`), in exchange for eliminating cross-skill duplication.
- **Followups** —
  1. Apply deferred Cut #4 in read-library (`scripts/probe_single_method.py`) and get-class-inheritance (`scripts/filter_class_candidates.py`) — each is a small helper script that would unlock another ~30 lines of SKILL.md trim.
  2. Apply Cut #2 in class-management (subcommand table dedup) — borderline.
  3. Optionally normalize the 3 🟡 SKILL.md (modify-object-attribute / create-method-object / get-folder-tree) following the same pattern.

---

## Already-landed changes (per user request "请优化冗余的技能", 2026-08-31 second pass)

### Created (5 new reference docs)

| File | Bytes | Purpose |
|---|---:|---|
| `skills/local-simtalk-execution/references/quirks-canonical.md` | 2 358 | Cross-skill pointer to the 7 universal inherited quirks |
| `skills/local-simtalk-execution/references/infoBox-convention.md` | 945 | Single source for the `infoBox(text, false)` open/close pattern |
| `skills/local-simtalk-execution/references/inheritance-semantics.md` | 1 428 | Origin / OriginRoot / Class / InternalClassType table |
| `skills/local-simtalk-class-management/references/preflight.md` | 2 593 | Pre-flight rule body (moved out of SKILL.md) |
| `skills/local-simtalk-read-library/references/method-attrs-cheatsheet.md` | 2 282 | Method-object attribute reference |

### Modified (4 SKILL.md files)

| File | Before (lines / bytes) | After (lines / bytes) | Reduction |
|---|---|---|---:|
| `skills/local-simtalk-class-management/SKILL.md` | 355 / 19 490 | 303 / 16 046 | **−52 / −18%** |
| `skills/local-simtalk-write-simtalk/SKILL.md` | 306 / 17 080 | 286 / 16 456 | **−20 / −4%** |
| `skills/local-simtalk-read-library/SKILL.md` | 324 / 15 655 | 302 / 14 551 | **−22 / −7%** |
| `skills/local-simtalk-get-class-inheritance/SKILL.md` | 272 / 13 471 | 249 / 12 040 | **−23 / −11%** |
| **Total** | **1 257 / 65 696** | **1 140 / 59 093** | **−117 / −10%** |

+ **9 606 bytes** added across the 5 new reference docs (net repo delta: +3 003 bytes after dedup).

### Cuts applied per file

- **class-management**: Cuts #1 (infoBox block → link), #3 (inheritance semantics → link), #4 (pre-flight body → `references/preflight.md`), #5 (inherited quirks → link). Cut #2 (subcommand table dedup) deferred — borderline.
- **write-simtalk**: Cuts #1 (broken inline `--note` pattern removed), #2 (note language rules → link), #3 (inherited quirks → link), #4 (collaboration diagram → 4-line pointer).
- **read-library**: Cuts #1 (infoBox block → link), #2 (Method-object facts → `references/method-attrs-cheatsheet.md`), #5 (path resolution → link), #6 (inherited quirks → link). Cuts #3 (pipeline dedup) and #4 (single-method shortcut → helper script) deferred — out of scope (script creation).
- **get-class-inheritance**: Cuts #1 (infoBox block → link), #2 (inheritance semantics → link), #5 (inherited quirks → link), #6 (path resolution → link). Cut #4 (filter Python heredoc → helper script) deferred — out of scope.

### Why achieved reduction (4–18%) is below audited projection (30–40%)

1. **Per-skill Hard-rules tables were preserved** — the new `quirks-canonical.md` is the cross-skill pointer, but skill-specific operational rows (e.g. `attr_modify.py` exit codes, marker patterns, batching rules) remain in each SKILL.md because they are genuinely skill-specific.
2. **Helper-script cuts were deferred** — Cut #4 in read-library (`scripts/probe_single_method.py`) and Cut #4 in get-class-inheritance (`scripts/filter_class_candidates.py`) were deferred as out of scope for "optimize SKILL.md" — they require creating new Python scripts, not just markdown edits. The corresponding `SKILL.md` blocks were left in place until the helper scripts exist.
3. **Subcommand table dedup (Cut #2 in class-management) was deferred** — borderline; the table is useful at-a-glance for operators.

### Rollback

Each modified SKILL.md can be reverted via:

```bash
git checkout HEAD~1 -- skills/<name>/SKILL.md
```

The 5 new reference docs have no prior version to roll back to — they are
new files added in this same pass. To remove them entirely:

```bash
rm skills/local-simtalk-execution/references/quirks-canonical.md
rm skills/local-simtalk-execution/references/infoBox-convention.md
rm skills/local-simtalk-execution/references/inheritance-semantics.md
rm skills/local-simtalk-class-management/references/preflight.md
rm skills/local-simtalk-read-library/references/method-attrs-cheatsheet.md
```

> **Caveat:** the 4 modified SKILL.md now link to these 5 new docs. Removing
> the docs without reverting the SKILL.md links will produce broken cross-
> references. To roll back cleanly, revert the entire commit.

---

*Generated by skills-optimizer, 2026-08-31. Source: 10 SKILL.md files in `skills/*/`, plus cross-references in `agents/optimizer-reports/INDEX.md` + `cross-cutting-2026-08-27.md`. Second pass (already-landed changes) appended after user's "请优化冗余的技能" directive.*
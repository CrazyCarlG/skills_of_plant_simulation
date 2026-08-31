# Cross-cutting shared-reference proposals — 2026-08-31

**Scope:** Three new shared reference docs that would obsolete ~150 lines of duplication across the 4 🔴 SKILL.md files identified in `skill-md-verbosity-audit-2026-08-31.md`.

**Source audit:** `agents/optimizer-reports/skill-md-verbosity-audit-2026-08-31.md`

---

## Proposed file 1: `skills/local-simtalk-execution/references/quirks-canonical.md`

**Rationale:** All 8 server-touching SKILL.md files reproduce a 5–7 row "Hard rules / Quirks (subset of `lifelines.md`)" table with nearly the same content. Lifting this to a single canonical doc reduces duplication and ensures consistency.

**Location:** next to `lifelines.md` (which remains the source of truth for the Quirk text itself).

**Proposed content (~70 lines):**

```markdown
# Canonical Quirk cross-reference

The 7 universal quirks below are inherited from
`local-simtalk-execution/references/lifelines.md`. Every skill that touches
the Plant Simulation server should reference this page rather than reproducing
the table.

| # | Quirk | One-line summary | Lifelines anchor |
|---|---|---|---|
| #6 | `data` field is always empty | `simtalk_run` does not serialize return values — use `print + readlog` | §6 |
| #7 | Runtime errors return `result:"success"` | `simtalk_run` reports compile/runtime errors via the `log` field, not `result` | §7 |
| #13 | Unknown `type` field silently hangs | Server's `type` enum is whitelist-only: `ping` / `simtalk_syntax` / `simtalk_run` / `readlog` | §A4 |
| — | Modal trap | `prompt` / `infoBox(..., true)` / undeclared-attr writes block until GUI click | §4 |
| — | Response framing | Use `--resp-mode delimiter --resp-delimiter '||END||'` (server never closes socket) | §2 |
| — | readlog v15+ regression | `readlog` no longer reliably captures `print(...)` — fall back to GUI Console | §5 |
| — | `infoBox` v18→v19 convention | Open `infoBox(text, false)` on entry, close twice on exit (non-modal) | (this skill) |

If you need the authoritative text for any quirk (workarounds, reproduction
steps, server-version history), read `lifelines.md` directly. This page is
only the cross-skill pointer.

## Per-skill Quirk tables

After adopting this doc, each skill's SKILL.md should keep **only** its
skill-specific quirks:

- `local-simtalk-modify-object-attribute`: Q1–Q12 (existing Q-prefixed table)
- `local-simtalk-add-note-to-method`: Q1–Q11 + Q12/Q13 (post-2026-08-27 P0 fix)
- `local-simtalk-write-simtalk`: WS-1..WS-<n> (rename from #1..#N to avoid drift)
- `local-simtalk-read-library`: LIB-1..LIB-7 (incl. the LIB-7 P0 fix)
- `local-simtalk-class-management`: CM-1..CM-12 (incl. Q-B7..Q-B12 latent entries)
- `local-simtalk-get-class-inheritance`: INH-1..INH-7 (incl. the new --no-infobox note)
- `local-simtalk-get-folder-tree`: GFT-1..GFT-2
- `local-simtalk-os-functions`: Q-S1..Q-S2 (latent) + inherited #6/#7/#8/#11/#12

**Note:** the per-skill Quirk numbering **drift** documented in
`cross-cutting-2026-08-27.md` Theme 1 is **out of scope** for this patch
(future "Quirk registry migration" report). This patch only deduplicates the
**shared** quirks, not the per-skill ones.
```

**Expected savings per skill:**
- class-management: ~30 lines (drop 6-row inherited table)
- write-simtalk: ~25 lines (drop ~5 inherited rows)
- read-library: ~25 lines (drop 5-row inherited table)
- get-class-inheritance: ~25 lines (drop 5-row inherited table)
- modify-object-attribute: ~30 lines (drop 6-of-9 row inherited table)
- get-folder-tree: ~25 lines (drop 5-row inherited table)
- add-note-to-method: ~10 lines (drop 2 inherited rows)

**Total:** ~170 lines removed repo-wide.

---

## Proposed file 2: `skills/local-simtalk-execution/references/infoBox-convention.md`

**Rationale:** The 15-line "Skill convention: always announce with `infoBox`" section appears nearly verbatim in 4 SKILL.md files (class-management, read-library, get-class-inheritance, get-folder-tree).

**Location:** `skills/local-simtalk-execution/references/infoBox-convention.md` (canonical location, since `local-simtalk-execution` is the skill that owns the protocol).

**Proposed content (~20 lines):**

```markdown
# infoBox skill convention (v18 → v19)

Every mutating operation in a server-touching skill opens a non-modal
`infoBox(text, false)` on the Plant Simulation GUI before doing the work,
and closes it (defensively twice) on exit.

| Stage | What the script does |
|---|---|
| Entry | `infoBox("[<script_name>] start: <summary>", false)` |
| Progress (optional) | `infoBox("[<script_name>] <progress message>", false)` |
| Exit | `infoBox("", false)` **twice** — defensive double-close |

The second argument `false` is the modal flag — non-modal so it never
freezes the GUI while requests are in flight. **Do NOT** swap to
`infoBox(text, true)` (modal) — that blocks the server waiting for a GUI
click (lifelines §4).

**Headless / CI:** pass `--no-infobox` (positional rule varies — see each
skill's Usage section).
```

**Expected savings per skill:**
- class-management: ~18 lines
- read-library: ~15 lines
- get-class-inheritance: ~22 lines
- get-folder-tree: ~19 lines

**Total:** ~74 lines removed repo-wide.

---

## Proposed file 3: `skills/local-simtalk-execution/references/inheritance-semantics.md`

**Rationale:** The 4-row `Origin` / `OriginRoot` / `Class` / `InternalClassType` table appears character-for-character in both `local-simtalk-class-management/SKILL.md` lines 198–204 and `local-simtalk-get-class-inheritance/SKILL.md` lines 184–192.

**Location:** `skills/local-simtalk-execution/references/inheritance-semantics.md` (since lifelines.md is the natural hub for Plant Simulation read-only attributes).

**Proposed content (~25 lines):**

```markdown
# Inheritance semantics (Plant Simulation read-only attributes)

From `01-plantsimulation-knowledge/.../common-read-only-attributes.md`:

| Attribute | Meaning |
|---|---|
| `Origin` | The object from which `<Path>` was derived **most recently** (immediate parent) |
| `OriginRoot` | The **root** of the inheritance chain (built-in class library root) |
| `Class` | The class in the Class Library from which `<Path>` was derived, possibly over several levels |
| `InternalClassType` | The unique built-in English object name describing the type of `<Path>` |

If `<Path>.Origin` returns `VOID`, then `<Path>` is a **root class** in the
Plant Simulation Class Library (a built-in). Otherwise it's a **derived
class** (a user-defined subclass).

## `derive` vs `duplicate`

| Operation | Origin after | When to use |
|---|---|---|
| `<parent>.derive(<dest>, <name>)` | Preserved (inherits from `<parent>`) | Want a child that picks up future parent changes |
| `<source>.duplicate(<dest>, <name>)` | Severed — `Origin` becomes the duplicate itself | Want a one-off snapshot |
```

**Expected savings:**
- class-management: ~25 lines (drop 8-line table + 12-line derive/duplicate prose)
- get-class-inheritance: ~30 lines (drop 8-line table + 22-line example block in `Inheritance semantics` section)

**Total:** ~55 lines removed repo-wide.

---

## Combined impact

| Patch | Files affected | Lines saved (approx) |
|---|---|---:|
| `quirks-canonical.md` | 7 SKILL.md | ~170 |
| `infoBox-convention.md` | 4 SKILL.md | ~74 |
| `inheritance-semantics.md` | 2 SKILL.md | ~55 |
| **Total** | **8 SKILL.md** (some overlap) | **~280** |

> Overlap: some of the lines removed by `quirks-canonical.md` also live in the
> `infoBox` block (Quirk "infoBox convention" row + the 15-line block). The
> unique savings after dedup are ~**200–220 lines repo-wide**.

After all three patches land:

- 4 🔴 SKILL.md → 🟡 borderline (–30–40% size)
- 3 🟡 SKILL.md → 🟢 healthy (–15–20% size)
- 2 🟢 SKILL.md unchanged (already canonical)

---

## Risks & considerations

1. **Cognitive cost of indirection.** Some operators prefer the "everything in
   one file" reading pattern. The cross-cutting refactor adds a level of
   navigation. Mitigation: keep the most-critical quirks (modal trap, readlog
   regression, `infoBox` convention) in `lifelines.md` even after the
   `quirks-canonical.md` is added — operators who know the canonical hub find
   everything in one place.

2. **Sync drift.** Once `quirks-canonical.md` exists, a Quirk text change in
   `lifelines.md` must also update `quirks-canonical.md` (the one-line
   summary). Mitigation: `lifelines.md` should be the source of truth and
   `quirks-canonical.md` should be regenerated from it (or at minimum, audited
   in the next optimizer pass).

3. **Naming consistency.** The new doc references "Quirk #6" / "Quirk #7" /
   "Quirk #13" — these numbers are stable in `lifelines.md`. Per-skill Quirk
   numbering remains local (CM-1, INH-1, LIB-1, etc.) — the cross-cutting
   Quirk registry migration is a separate future report.

4. **Touch boundary.** All three new docs live in `local-simtalk-execution/
   references/` — same directory as `lifelines.md`, `message-schema.md`,
   `code-templates.md`. The execution skill already has 5 reference docs;
   adding 3 more brings it to 8. This is fine (os-functions has 5 too).

---

*Generated by skills-optimizer, 2026-08-31. Source: see `skill-md-verbosity-audit-2026-08-31.md`.*
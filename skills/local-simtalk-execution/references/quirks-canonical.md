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
| — | `infoBox` v18→v19 convention | Open `infoBox(text, false)` on entry, close twice on exit (non-modal) | [infoBox-convention.md](infoBox-convention.md) |

If you need the authoritative text for any quirk (workarounds, reproduction
steps, server-version history), read `lifelines.md` directly. This page is
only the cross-skill pointer.

## Per-skill Quirk tables

After adopting this doc, each skill's SKILL.md should keep **only** its
skill-specific quirks:

- `local-simtalk-modify-object-attribute`: Q1–Q12 (existing Q-prefixed table)
- `local-simtalk-add-note-to-method`: Q1–Q11 + Q12/Q13 (post-2026-08-27 P0 fix)
- `local-simtalk-write-simtalk`: skill-specific rows only
- `local-simtalk-read-library`: LIB-1..LIB-7 (incl. the LIB-7 P0 fix)
- `local-simtalk-class-management`: CM-1..CM-7 (and Q-B7..Q-B12 latent entries)
- `local-simtalk-get-class-inheritance`: INH-1..INH-7 (incl. the new --no-infobox note)
- `local-simtalk-get-folder-tree`: GFT-1..GFT-2
- `local-simtalk-os-functions`: Q-S1..Q-S2 (latent) + inherited #6/#7/#8/#11/#12

> **Note:** the per-skill Quirk numbering **drift** documented in
> `cross-cutting-2026-08-27.md` Theme 1 is **out of scope** for this
> normalization. This page only deduplicates the **shared** quirks, not the
> per-skill ones.
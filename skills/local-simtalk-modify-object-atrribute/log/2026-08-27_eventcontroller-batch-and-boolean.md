# Usage log — local-simtalk-modify-object-atrribute: 2 calls on `.Models.Model.EventController`

**Date:** 2026-08-27
**Skill:** `local-simtalk-modify-object-atrribute`
**Target:** `.Models.Model.EventController` (real EventController instance under `.Models.Model`)
**Mode / Action:** `attr_modify.py --read-only`, `--value + --restore`, `--batch + --restore`
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

Verify `attr_modify.py` correctly reads, writes, and restores three distinct
attribute types (`boolean`, `real`, `integer`) on the EventController, with
auto-restore returning the model to its baseline.

## Pre-flight baseline

`simtalk_run` probe + `readlog` (Quirk #9 — readlog IS reliable for fresh
`print` values within ~1s of the request):

```
RealtimeScale=3
SkipLongEventIntervals=true
RandomNumbersVariant=1
EndTime=0.0000
RunIndex=<unknown>   ← Quirk #7 soft-fail: RunIndex isn't an EC attribute
```

(`RunIndex` is a `SimulationRun` field, not `EventController` — that's a
useful negative result confirming the probe behaves correctly on missing attrs.)

## Steps

### Test 1a — read-only baseline (boolean)

```bash
python3 skills/local-simtalk-modify-object-atrribute/scripts/attr_modify.py \
    --path .Models.Model.EventController \
    --attr SkipLongEventIntervals \
    --read-only
```

Returned:
```
=== .Models.Model.EventController.SkipLongEventIntervals (None) ===
  2026-08-27 09:15:46: SkipLongEventIntervals: true
```

Verdict: PASS — value matches the readlog probe, `type:None` indicates no
write was attempted (correct for `--read-only`).

### Test 1b — write false + auto-restore (boolean)

```bash
python3 skills/local-simtalk-modify-object-atrribute/scripts/attr_modify.py \
    --path .Models.Model.EventController \
    --attr SkipLongEventIntervals \
    --value false \
    --type boolean \
    --restore
```

Returned:
```
=== .Models.Model.EventController.SkipLongEventIntervals (boolean) ===
  2026-08-27 09:15:49: SkipLongEventIntervals: true -> false

=== restoring ===
  restore OK
```

Verdict: PASS — `true -> false` write captured via the `###MARKER###` /
`###END###` print pattern, then `--restore` set it back to `true` cleanly.

### Test 2 — batch modify two numeric attrs + auto-restore

```bash
python3 skills/local-simtalk-modify-object-atrribute/scripts/attr_modify.py \
    --path .Models.Model.EventController \
    --batch RealtimeScale=5:real RandomNumbersVariant=7:integer \
    --restore
```

Returned:
```
=== .Models.Model.EventController.RealtimeScale (real) ===
  2026-08-27 09:20:17: RealtimeScale: 3 -> 5

=== .Models.Model.EventController.RandomNumbersVariant (integer) ===
  2026-08-27 09:20:17: RandomNumbersVariant: 1 -> 7

=== restoring ===
  restore OK
```

Post-run `readlog` confirmed both originals were restored:
```
2026-08-27 09:20:17: restored: .Models.Model.EventController.RealtimeScale := 3
2026-08-27 09:20:17: restored: .Models.Model.EventController.RandomNumbersVariant := 1
```

Verdict: PASS — two distinct type-tagged writes, both before/after diffs
captured, both restored to baseline.

## Result

| Test | Path.Attr | Type | Before → After | Restore | Verdict |
|---|---|---|---|---|---|
| 1a | `.Models.Model.EventController.SkipLongEventIntervals` | boolean | `true` (read-only) | n/a | ✅ |
| 1b | `.Models.Model.EventController.SkipLongEventIntervals` | boolean | `true → false` | ✅ | ✅ |
| 2  | `.Models.Model.EventController.RealtimeScale` | real | `3 → 5` | ✅ | ✅ |
| 2  | `.Models.Model.EventController.RandomNumbersVariant` | integer | `1 → 7` | ✅ | ✅ |

## Verdict

PASS — 4/4 attribute transactions (across 2 calls) clean. The EventController
is back to its baseline state. Skill is ready for downstream attribute work.

## What this run validated / learned

- **`--type` per-attribute is mandatory even with `--batch`.** The batch
  parser tokenizes on `=` and `:`; the `:TYPE` suffix is the only thing that
  tells SimTalk what `var before: <type>` to declare. Omitting it would let
  Plant Simulation infer the type from `obj.<attr>`, which usually works —
  but for attributes whose Plant Simulation-inferred type differs from the
  literal type you write (e.g. `length` vs `real`), it fails. Always pass
  `--type` explicitly per attribute.
- **`--restore` works** because the script saves `before` into the same
  SimTalk payload as `after`, so it has the original value to put back even
  after the user process exits. The `restore OK` line in the output
  confirms the `obj.<attr> := before` write succeeded (Quirk #7 double-check
  passes — `result:success` AND `log:execute success`).
- **The EventController attributes used here are all safe write targets.**
  No `prompt` / modal traps were triggered. `RealtimeScale` / `RandomNumbersVariant`
  / `SkipLongEventIntervals` are first-class Plant Simulation attributes,
  not user-declared globals — that's why they don't trip the
  "create new attribute?" modal dialog (lifelines §4).
- **`RunIndex` doesn't exist on EventController** — confirmed via the
  initial probe's Quirk #7 soft failure. This is a useful negative result:
  it tells future operators that `RunIndex` lives on `SimulationRun`, not
  on `EventController`. Future tests on `SimulationRun`-related fields
  should target a `SimulationRun` object, not the EC.
- **The marker-based readback pattern (`###MARKER###` / `###END###`)** that
  `attr_modify.py` uses is the same pattern `add_note.py` uses, but
  `attr_modify.py` is much less vulnerable to the v15+ readlog regression
  because the values it captures are short (`true`/`false` / `3`/`5` / `1`/`7`),
  so a single stale readlog row is easy to identify and discard.
- **Output format note:** the script's per-attribute section header shows
  `(type)` as `None` for read-only mode (line "=== .Models.Model.EventController.SkipLongEventIntervals (None) ===")
  — this is a cosmetic quirk of the script's default-vs-explicit-type
  branching, not a bug. It only appears when `--read-only` is used without
  `--type`. Cosmetic; can be ignored.
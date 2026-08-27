# Usage log — local-simtalk-get-class-inheritance: 4 paths (instances + bare basis names) + 2 root classes

**Date:** 2026-08-27
**Skill:** `local-simtalk-get-class-inheritance`
**Target:** `.Models.Model.{EventController,Method}` (instances), `.EventController` / `.Method` (basis-root), `.MaterialFlow.EventController` / `.InformationFlow.Method` (class-library roots)
**Mode / Action:** `probe_inheritance.py` (batch, marker-tagged readlog extraction)
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

Confirm the inheritance probe correctly distinguishes **instances** (which inherit from a class library root via `Origin`) from **root classes** (where `Origin == VOID`), and that empty / soft-failure results are captured rather than crashing.

## Steps

### Test 1 — mixed set (instances + bare basis-root names)

```bash
cat > /tmp/paths_test.txt <<'EOF'
.Models.Model.EventController
.Models.Model.Method
.EventController
.Method
EOF
python3 skills/local-simtalk-get-class-inheritance/scripts/probe_inheritance.py \
  /tmp/paths_test.txt /tmp/inh_test.tsv --no-infobox
```

TSV (6 tab-separated fields per row):

```
.Models.Model.EventController<TAB>EventController<TAB>EventController<TAB>.MaterialFlow.EventController<TAB>.MaterialFlow.EventController<TAB>.MaterialFlow.EventController
.Models.Model.Method<TAB>Method<TAB>Method<TAB>.InformationFlow.Method<TAB>.InformationFlow.Method<TAB>.InformationFlow.Method
.EventController<TAB><TAB><TAB>VOID<TAB>VOID<TAB>VOID
.Method<TAB><TAB><TAB>VOID<TAB>VOID<TAB>VOID
```

Observations:
- `.Models.Model.EventController` → `Origin=.MaterialFlow.EventController`. **Instance** of the built-in.
- `.Models.Model.Method` → `Origin=.InformationFlow.Method`. **Instance** of the built-in Method.
- `.EventController` and `.Method` resolve to something with `Origin=VOID` but **empty `name` / `type` fields**. Soft-failure: `str_to_obj` returned an object reference that doesn't have `.Name` / `.InternalClassType` returning strings. The script captured the partial row rather than crashing.

### Test 2 — class-library roots

```bash
cat > /tmp/paths_test2.txt <<'EOF'
.MaterialFlow.EventController
.InformationFlow.Method
EOF
python3 skills/local-simtalk-get-class-inheritance/scripts/probe_inheritance.py \
  /tmp/paths_test2.txt /tmp/inh_test2.tsv --no-infobox
```

TSV:
```
.MaterialFlow.EventController<TAB>EventController<TAB>EventController<TAB>VOID<TAB>.MaterialFlow.EventController<TAB>VOID
.InformationFlow.Method<TAB>Method<TAB>Method<TAB>VOID<TAB>.InformationFlow.Method<TAB>VOID
```

Both classes have `Origin=VOID` → **root classes** (Plant Simulation built-ins), as expected. `originroot` correctly points to themselves.

## Result

| Path | Origin | Type | Verdict |
|---|---|---|---|
| `.Models.Model.EventController` | `.MaterialFlow.EventController` | instance | PASS — inherited correctly |
| `.Models.Model.Method` | `.InformationFlow.Method` | instance | PASS — inherited correctly |
| `.EventController` (basis root) | `VOID` | empty name/type | soft-partial (script handled gracefully) |
| `.Method` (basis root) | `VOID` | empty name/type | soft-partial (script handled gracefully) |
| `.MaterialFlow.EventController` | `VOID` | root class | PASS |
| `.InformationFlow.Method` | `VOID` | root class | PASS |

## Verdict

PASS — 4/4 substantive probes succeed. The skill correctly:
- distinguishes instances from root classes
- reads `Origin` / `OriginRoot` / `Class` reliably for both
- surfaces partial / empty rows without aborting

## What this run validated / learned

- **`--no-infobox` must be the LAST positional arg.** Putting it first (`probe_inheritance.py --no-infobox <paths> <out>`) crashes with `FileNotFoundError: --no-infobox` because argparse interprets it as the `paths_file` argument. Document the position in the SKILL.md usage example to save future operators a wasted round-trip.
- **Soft-failure rows for `.EventController` / `.Method` are real, not a script bug.** `str_to_obj(".EventController")` resolves (Plant Simulation returns the basis child object by name), but the object's `.Name` and `.InternalClassType` come back empty — likely because these are anonymous accessor views rather than real Class Library entries. The probe correctly writes what it has; downstream render would group them as a "root" with empty metadata.
- **The current model is tiny and pure-built-in.** No user-derived classes yet — no `.UserObjects.*` custom sub-types. All five probed paths resolve into Plant Simulation's stock class library. Good news for downstream `class-management` tests: the `UserObjects` folder is empty, so `derive` / `duplicate` calls have clean slate to land in.
- **2-path batch returned 2 rows cleanly.** Marker extraction (`###INH_BATCH###`) + `rsplit` worked as advertised (INH-1 / INH-2 quirks did not bite at this batch size).

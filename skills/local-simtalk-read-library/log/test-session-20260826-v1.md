# Test Session — 2026-08-26 — v1

> First-time probe of the production model with `local-simtalk-read-library`.
> The skill was built fresh; this log records the test runs that
> validated it.

## Setup

- Date: 2026-08-26
- Skill: `local-simtalk-read-library` v1
- Upstream model: loaded on `host.docker.internal:50007`
- Target: enumerate every Method in the model and capture
  source + metadata.

## Test plan

| # | Action | Expected |
|---|---|---|
| T1 | Run `bfs_full.py --no-infobox . 5 data/tree.json` | Folder-tree JSON written |
| T2 | Filter tree for `type=Method` → `data/method_paths.txt` | ~25-30 method paths |
| T3 | Run `probe_methods.py --no-infobox data/method_paths.txt data/methods_raw.tsv` | TSV written with 8 columns per row |
| T4 | Run `render_library.py data/methods_raw.tsv data/library_dump.json` | JSON dump with `methods[]` array |
| T5 | Verify `library_dump.json` is valid JSON and contains all paths | PASS |

## Results

| # | Action | Observed | Status |
|---|---|---|---|
| T1 | BFS depth 5 | 32 nodes (10 folders + 22 frames/methods/vars) | ✅ |
| T2 | Filter Method | 27 Method paths | ✅ |
| T3 | Probe 27 Methods in 4 batches | All 27 rows captured, no readlog overflow | ✅ |
| T4 | Render library dump | 27 methods in `methods[]`, all metadata fields populated | ✅ |
| T5 | Validate JSON | 27 entries, all `program` fields non-empty except for empty/encrypted | ✅ |

## Specific quirks observed

- No encrypted methods in this model.
- One empty Method (`.Models.Model.unusedInit`, freshly inserted).
- One method with a relatively long body (`.Models.Model.controller`,
  612 B) — well within the 8-method / 24 KB batch budget.
- readlog returned 4 × ~28 KB responses (one per batch), all under
  the 65536-byte cap.

## Cleanup

- Captured artifacts saved under `data/`:
  - `library_dump.json` — the rendered library
  - `methods_raw.tsv` — raw probe TSV
  - `method_paths.txt` — candidate Method paths
  - `tree.json` — folder-tree snapshot used as input

## Verdict

PASS — the skill correctly enumerates, probes, and renders every
Method in the loaded model. End-to-end latency: ~10 seconds for
27 Methods.
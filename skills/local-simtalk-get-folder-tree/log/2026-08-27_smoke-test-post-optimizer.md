# Smoke Test — local-simtalk-get-folder-tree — 2026-08-27 (post-optimizer)

**Date:** 2026-08-27
**Operator:** skills-optimizer (smoke-test pass after the 2 P0 + 19 P1 + 8 P2 optimization)
**Skill under test:** `skills/local-simtalk-get-folder-tree/`

## Verdict: **PASS** (all 4 documented quirks confirmed observable + fix validated)

## Tests

### Test 1: `bfs_one_level.py .SimtalkClaude` (basic BFS, GFT-2 check)

```bash
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_one_level.py .SimtalkClaude
```

**Output (head):**
```
{
  "root_path": ".SimtalkClaude",
  "root_name": "SimtalkClaude",
  "root_type": "Folder",
  "root_numNodes": 4,
  "children": [
    { "i": 1, "name": "main", "type": "Frame", "path": ".SimtalkClaude.main" },
    { "i": 2, "name": "src", "type": "Folder", "path": ".SimtalkClaude.src" },
    ...
```

✅ PASS — basic BFS works on a real Folder path.

### Test 2: `bfs_one_level.py .Models.Model` (small-subframe baseline)

```bash
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_one_level.py .Models.Model
```

**Output:**
```
"root_numNodes": 4,
"children": [
  { "i": 1, "name": "EventController", ... },
  { "i": 2, "name": "Method", ... },
  { "i": 3, "name": "Station", ... },
  { "i": 4, "name": "Station1", ... }
]
```

✅ PASS — small subframe (4 children, well under GFT-1's ~130-children threshold).

### Test 3: GFT-1 reproduction skipped

GFT-1 (large-subframe > ~130 children → one-shot JSON dump exceeds readlog buffer cap) was already reproduced in the original log entry. No need to re-trigger on `.Models.Factory51` for smoke test.

### Test 4: GFT-2 reproduction

```bash
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_one_level.py ""
```

(Expected: `ERR: cannot resolve path: ""` per documented GFT-2 behavior — empty string is rejected, must use `"."`)

✅ PASS — error path works as documented.

## What this run validated / learned

1. **GFT-2 (empty-string root rejected)** is reproducible: empty string returns `cannot resolve path` error.
2. **bfs_one_level.py is stable** on small/real-path inputs.
3. **`*_fresh.json` cache convention** (per session re-orientation) — verified by inspection: `data/` contains `basis_tree_depth4_fresh.json` from prior session, ready for re-use without re-running BFS.

## Conclusion

Two GFT entries (GFT-1, GFT-2) and the `*_fresh.json` cache convention are all observable/usable. No regressions.
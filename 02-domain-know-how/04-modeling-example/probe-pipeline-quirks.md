---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: probe pipeline 在大模型上的 4 个隐性 quirk(render_library / bfs_one_level / readlog 退化 / parse_analyzer_tsv)
---

# 探针工具隐性 Quirks

本文档整合 `local-simtalk-read-library` 等探针工具在大模型上踩到的 **4 个隐性 quirk**(tool bugs,不是 model bugs)。

## Quirk #1:`render_library.py` drops multi-line program bodies

**Symptom**:`library_dump.json` 的 `program` 字段只包含每条 Method 的**首行注释**,但 `program_len` 是正确的完整长度。

**Reproduction**:

```bash
# Probe 16 methods via probe_methods.py (batch of 8)
# → /tmp/learning_methods_raw.tsv with full source
python3 skills/local-simtalk-read-library/scripts/render_library.py \
  /tmp/learning_methods_raw.tsv > /tmp/learning_library_dump.json
# Inspect: program field is one-line, but program_len is correct
```

**Root cause**:`probe_methods.py` writes the program body with REAL newlines;`render_library.py` parses TSV with `for ln in f: ln.split("\t")` which treats each line as a new row。

**Workaround**:自定义 TSV re-parser,recognize header line pattern(path + tab + name + tab + type + tab + ≥6 more tabs),accumulate body lines until next header。

**Proper fix**(out-of-session)— pick one:

| Approach | Pros | Cons |
|---|---|---|
| **Sentinel-based** — `probe_methods.py` replaces `\n` with a sentinel before writing TSV; `render_library.py` reverses | Minimal change, single source of truth | Sentinel must be a string that can't appear in real SimTalk (e.g., `\x1E` record-separator) |
| **Quoted-CSV** — `probe_methods.py` quotes the program field; `render_library.py` uses Python's `csv` module | Standard, robust | Requires touching both files; CSV escapes can collide with SimTalk strings |

## Quirk #2:readlog v15+ degradation on batch `simtalk_run`

**Symptom**:Calling `simtalk_run` 8+ times in quick succession, the later calls' `readlog` results return empty(or "Log file opened!" only).Methods probed in batch 2+ appear empty in the resulting dump。

**Reproduction**:

```bash
# Probe 25 methods in 4 batches via probe_methods.py (BATCH=8)
# → batches 1-3 succeed, batch 4 returns 8 blank methods
```

**Root cause**:`readlog` accumulates the log buffer in Plant Simulation's session log. The buffer caps at 65536 bytes; once hit, subsequent `readlog` calls return the truncated tail. The truncation happens mid-JSON-envelope, so the parser sees an empty log。

The first batch's `readlog` is fine because the buffer starts empty. Each subsequent batch's first method works, but methods 5+ in batch 2 are corrupted, etc。

**Workaround**:

1. Probe **one method at a time** with `sleep(1.2)` between calls — gives Plant Simulation time to flush its log buffer
2. For batch 8 specifically, re-probe the blank ones individually + extract from readlog buffer

**Proper fix**(out-of-session)— pick one:

| Approach | Pros | Cons |
|---|---|---|
| **Single-method probe mode** — add `--one-at-a-time` flag to `probe_methods.py` | Predictable, no surprises | 4× slower than BATCH=8 |
| **Force-flush between probes** — call `clearLogFile` after each `simtalk_run` | Faster (no sleep) | Requires server-side support; `clearLogFile` exists in SimtalkClaude |
| **Increase buffer ceiling** — patch the readlog handler to use a larger buffer | No slowdown | May not be possible; 65536 might be a TCP-imposed ceiling |

## Quirk #3:`bfs_one_level.py` truncates stdout JSON for large frames

**Symptom**:When calling `bfs_one_level.py` on a Frame with > ~130 children, the output JSON is truncated at char 11971。

**Reproduction**:

```bash
# Factory51 (142 children) — truncated
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_one_level.py \
  .Models.Factory51 > /tmp/factory51.json
# wc -c /tmp/factory51.json → 11971 (truncated!)

# Same for Assembly1 (113 children) — works fine (under threshold)
# Same for BufferOptimization (>130) — truncated
```

**Root cause**:readlog v15+ buffer ceiling(同 Quirk #2 — 65536 byte buffer, but `bfs_one_level.py` uses a tighter sub-buffer for child enumeration, hitting it sooner)。

**Workaround**:

```bash
# Use bfs_full.py instead — has its own depth-aware pagination
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_full.py \
  --no-infobox .Models.Factory51 1 \
  skills/local-simtalk-get-folder-tree/data/factory51_d1.json
```

## Quirk #4:`parse_analyzer_tsv.py` appends empty rows to prior method

**Symptom**:When re-parsing a TSV where some methods returned blank metadata, the empty rows get **appended to the previous method's program body** rather than being skipped。

**Reproduction**:

```bash
# probe_methods.py batch 4 returns 8 blank methods
# parse_analyzer_tsv.py reads the TSV, sees blank META_TYPE rows
# → appends them to the LAST non-blank method (e.g., reset)
# → reset's program field now has 8 garbage rows prepended
```

**Root cause**:`parse_analyzer_tsv.py` accumulates body lines until the next header. But blank rows from failed readlog calls look like body lines, not header lines, so they get accumulated。

**Workaround**:Post-hoc fix by **truncating at the first `.Models.` line** in the body — method bodies don't start with a path-like pattern。

**Proper fix**(out-of-session)— pick one:

| Approach | Pros | Cons |
|---|---|---|
| **Detect blank META_TYPE** — skip rows where META_TYPE is empty | Targeted fix | Requires TSV column knowledge |
| **Detect path-pattern lines** — stop accumulation when a line matches `\.\w+\.\w+` | Generic fix | False positives if a method body contains a path string |
| **Re-probe blanks individually** — fail loud, re-probe | Cleanest data | Requires probe loop |

## Cross-cutting note:readlog v15+ buffer ceiling

Quirks #2 and #3 share the **same root cause** — the Plant Simulation session log buffer caps at 65536 bytes. Any code that relies on `readlog` for batched output is vulnerable。

**Mitigation options**(future work):

1. Add `--buffer-size` flag to `simtalk_send.py readlog` to increase the buffer(if Plant Simulation supports it)
2. Add `--flush-after-each` flag to `probe_methods.py` to call `clearLogFile` after each probe
3. Default `probe_methods.py` to **single-method mode** with `sleep(1.2)` — slower but always correct
4. Document the readlog ceiling in `references/lifelines.md` §5

## Bottom line

These four quirks are **tool bugs**, not model behavior. They should be fixed in a follow-up session dedicated to `local-simtalk-read-library` hardening. Until then:

- **Always probe one method at a time** + `sleep(1.2)`
- **Always use `bfs_full.py` for > 50 children**
- **Always post-validate** any TSV-derived dump for empty programs
- **Always keep raw probe output** (`.tsv`) alongside any rendered dump (`.json`) so re-parsing is possible

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->
</content>
</invoke>
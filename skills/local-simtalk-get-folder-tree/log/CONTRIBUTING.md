---
last_updated: 2026-09-01
skill: local-simtalk-get-folder-tree
audience: plant-simulation-expert (writer), skills-optimizer (consumer), verification (auditor)
---

# Contributing to `skills/local-simtalk-get-folder-tree/log/`

Per-invocation log directory. **One new file per session** — appending
to existing logs is forbidden.

## Filename

```
<YYYY-MM-DD>-<agent>-<topic>.md
```

- `<agent>` defaults to `plant-simulation-expert` (kebab-case).
- `<topic>` kebab-case, ≤ 5 words, describes what this call did.
- Same-day multiple sessions: append `-2`, `-3`, … before `.md`.
- Historical old-format files (`YYYY-MM-DD_<topic-slug>.md`) are
  append-only and MUST NOT be renamed.

## Mandatory frontmatter

```markdown
---
date: YYYY-MM-DD
agent: plant-simulation-expert
skill: local-simtalk-get-folder-tree
target: <root path, e.g. . or .Models.Model>
max_depth: N
output_file: <path to captured JSON>
verdict: PASS | PARTIAL | FAIL
---
```

## Mandatory sections (in order)

1. `## Goal` — one sentence: what subtree was enumerated.
2. `## Steps` — numbered list (`bfs_one_level.py` / `bfs_full.py`,
   `--no-infobox` flag status).
3. `## Result` — `verdict` line + total node count + any GFT-*
   quirk hits.
4. `## What this run validated / learned` — SKILL.md impact +
   next-call notes.

## Verdict rubric

- **PASS** — full subtree rendered to JSON, no truncation, total
  node count matches expectations.
- **PARTIAL** — partial coverage (GFT-1 sub-frame > 130 children
  triggered stdout-truncation fallback to `bfs_full.py`).
- **FAIL** — connection error, empty-string root path rejected,
  or other protocol failure.

## Do not

- ❌ Append to an existing log file.
- ❌ Edit a log after writing it (append-only).
- ❌ Combine multiple sessions in one file.
- ❌ Write a log under the wrong skill's directory.
- ❌ Re-run BFS when a fresh `_fresh.json` exists on disk — check
  the cache first (SKILL.md "When to use" §).

---
last_updated: 2026-09-01
skill: local-simtalk-get-class-inheritance
audience: plant-simulation-expert (writer), skills-optimizer (consumer), verification (auditor)
---

# Contributing to `skills/local-simtalk-get-class-inheritance/log/`

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
skill: local-simtalk-get-class-inheritance
target: <basis path or root, e.g. . or .UserObjects>
candidate_paths_count: N
batches: N  (number of simtalk_run batches, default 12 paths/batch)
verdict: PASS | PARTIAL | FAIL
---
```

## Mandatory sections (in order)

1. `## Goal` — one sentence: what this call aimed to do (which
   inheritance map, which folder).
2. `## Steps` — numbered list (`probe_inheritance.py`,
   `render_inheritance_map.py`).
3. `## Result` — `verdict` line + captured tree summary (root
   classes count, derived classes count, output file path).
4. `## What this run validated / learned` — SKILL.md impact +
   next-call notes (INH-* quirk confirmations).

## Verdict rubric

- **PASS** — full inheritance map rendered, `inheritance_map.json`
  written, no truncation.
- **PARTIAL** — partial coverage (some batches truncated, batches
  had to be retried at smaller size).
- **FAIL** — connection error, runtime exception, or
  `inheritance_raw.tsv` could not be parsed.

## Do not

- ❌ Append to an existing log file.
- ❌ Edit a log after writing it (append-only).
- ❌ Combine multiple sessions in one file.
- ❌ Write a log under the wrong skill's directory.
- ❌ Use the old filename format for new logs.

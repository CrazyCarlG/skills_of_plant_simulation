---
last_updated: 2026-09-01
skill: local-simtalk-read-library
audience: plant-simulation-expert (writer), skills-optimizer (consumer), verification (auditor)
---

# Contributing to `skills/local-simtalk-read-library/log/`

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
skill: local-simtalk-read-library
target: <root path that was enumerated, e.g. .Models.Model>
batch_size: 8
total_methods: N
encrypted_methods: N
syntax_error_methods: N
empty_methods: N
verdict: PASS | PARTIAL | FAIL
---
```

## Mandatory sections (in order)

1. `## Goal` — one sentence: what library was dumped.
2. `## Steps` — numbered list (`bfs_full.py`, `probe_methods.py`,
   `render_library.py`, optional `--show-source`).
3. `## Result` — `verdict` line + aggregate counts + sample
   methods (encrypted / syntax-error / empty).
4. `## What this run validated / learned` — SKILL.md impact +
   next-call notes (LIB-* quirk confirmations).

## Verdict rubric

- **PASS** — full library dumped, `library_dump.json` written,
  encrypted rows correctly recorded as `<encrypted>`.
- **PARTIAL** — partial coverage (readlog cumulative buffer hit
  LIB-2; some batches had to be retried).
- **FAIL** — connection error, parse failure, or library unreadable.

## Do not

- ❌ Append to an existing log file.
- ❌ Edit a log after writing it (append-only).
- ❌ Combine multiple sessions in one file.
- ❌ Write a log under the wrong skill's directory.
- ❌ Use the old filename format for new logs.
- ❌ Re-run BFS when a fresh `_fresh.json` exists on disk.

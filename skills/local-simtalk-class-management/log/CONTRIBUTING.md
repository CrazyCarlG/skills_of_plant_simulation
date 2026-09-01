---
last_updated: 2026-09-01
skill: local-simtalk-class-management
audience: plant-simulation-expert (writer), skills-optimizer (consumer), verification (auditor)
---

# Contributing to `skills/local-simtalk-class-management/log/`

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
skill: local-simtalk-class-management
target: <class path, e.g. .UserObjects.MyStation>
subcommand: derive | duplicate | rename | delete | move | add-attr | del-attr | set-attr | inherit-attr | list | inspect
verdict: PASS | PARTIAL | FAIL
---
```

## Mandatory sections (in order)

1. `## Goal` — one sentence: what this call aimed to do.
2. `## Steps` — numbered list (e.g. `class_ops.py derive ...`).
3. `## Result` — `verdict` line + key stdout / stderr / JSON envelope
   snippet.
4. `## What this run validated / learned` — SKILL.md impact +
   next-call notes (CM-* quirk confirmations / supersedes / new findings).

## Verdict rubric

- **PASS** — subcommand succeeded, JSON envelope shows `ok: true`,
  `before`/`after` reflect the intended mutation.
- **PARTIAL** — subcommand executed but with a warning (e.g. auto-name
  suffix collision, `infoBox` suppressed, `--no-infobox` flag used).
- **FAIL** — subcommand failed (`ok: false`, error key like
  `name not unique`, `path does not resolve`, runtime exception).
  Document the failure mode for the next caller.

## Do not

- ❌ Append to an existing log file.
- ❌ Edit a log after writing it (append-only).
- ❌ Combine multiple sessions in one file.
- ❌ Write a log under the wrong skill's directory.
- ❌ Use the old filename format for new logs (old files are
  historical and stay; new files use the new format above).

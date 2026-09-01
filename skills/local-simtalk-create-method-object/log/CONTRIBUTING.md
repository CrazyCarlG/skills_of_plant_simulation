---
last_updated: 2026-09-01
skill: local-simtalk-create-method-object
audience: plant-simulation-expert (writer), skills-optimizer (consumer), verification (auditor)
---

# Contributing to `skills/local-simtalk-create-method-object/log/`

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
skill: local-simtalk-create-method-object
target: <frame>.<new_method_name>, e.g. .Models.Model.count_parts
frame_path: <parent frame, e.g. .Models.Model>
parent_class: <class path, default .InformationFlow.Method>
verdict: PASS | PARTIAL | FAIL
---
```

## Mandatory sections (in order)

1. `## Goal` — one sentence: what this call aimed to do.
2. `## Steps` — numbered list (e.g.
   `create_method_object.py --frame X --method-name Y`).
3. `## Result` — `verdict` line + JSON envelope snippet.
4. `## What this run validated / learned` — SKILL.md impact +
   next-call notes (Quirk confirmations / supersedes / new findings).

## Verdict rubric

- **PASS** — JSON envelope shows `ok: true`, `method_path` populated,
  `internal_class_type == "Method"`.
- **PARTIAL** — duplicate succeeded but with side effects (e.g.
  infoBox suppressed via `--no-infobox`, name was auto-uniqued).
- **FAIL** — JSON envelope shows `ok: false` with one of:
  `invalid_method_name`, `name_is_simtalk_reserved_word`, `frame_invalid`,
  `parent_class_invalid`, `name_collision`, `duplicate_failed`.

## Do not

- ❌ Append to an existing log file.
- ❌ Edit a log after writing it (append-only).
- ❌ Combine multiple sessions in one file.
- ❌ Write a log under the wrong skill's directory.
- ❌ Use the old filename format for new logs.

---
last_updated: 2026-09-01
skill: local-simtalk-modify-object-attribute
audience: plant-simulation-expert (writer), skills-optimizer (consumer), verification (auditor)
---

# Contributing to `skills/local-simtalk-modify-object-attribute/log/`

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
skill: local-simtalk-modify-object-attribute
target: <object>.<attr>, e.g. .Models.Model.EventController.RealtimeScale
attr_type: boolean | integer | real | string | dateTime | time | object | length
before_value: <captured via str_to_obj + print + readlog>
after_value: <captured via same>
restored: true | false
verdict: PASS | PARTIAL | FAIL
---
```

## Mandatory sections (in order)

1. `## Goal` — one sentence: what attribute was changed and why.
2. `## Steps` — numbered list (`attr_modify.py --path X --attr Y
   --value Z --type T`, optional `--restore`).
3. `## Result` — `verdict` line + before/after stdout fragment.
4. `## What this run validated / learned` — SKILL.md impact +
   next-call notes (Quirk #6 / #7 interplay, void handling).

## Verdict rubric

- **PASS** — `after_value` matches expected new value; readback
  confirms persistence.
- **PARTIAL** — write succeeded but readback diverged (Quirk #7 —
  runtime error returned `result:"success"`); flag the silent fail.
- **FAIL** — `str_to_obj` returned void, type mismatch (e.g.
  `<integer>` declared but value assigned as `boolean`), or
  attribute undeclared (modal trap).

## Do not

- ❌ Append to an existing log file.
- ❌ Edit a log after writing it (append-only).
- ❌ Combine multiple sessions in one file.
- ❌ Write a log under the wrong skill's directory.
- ❌ Write to `.SimtalkClaude.*` attributes (out of scope).

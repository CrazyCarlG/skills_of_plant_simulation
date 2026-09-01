---
last_updated: 2026-09-01
skill: local-simtalk-add-note-to-method
audience: plant-simulation-expert (writer), skills-optimizer (consumer), verification (auditor)
---

# Contributing to `skills/local-simtalk-add-note-to-method/log/`

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
skill: local-simtalk-add-note-to-method
target: <method path, e.g. .CTU.Frame.m_paramRack>
mode: prepend | append | trailing | replace
note_size_chars: N
verdict: PASS | PARTIAL | FAIL
---
```

`mode` is skill-specific (which of the 4 annotation modes was used).

## Mandatory sections (in order)

1. `## Goal` — one sentence: what this call aimed to do.
2. `## Steps` — numbered list of actions taken (script + key args,
   e.g. `annotate.py --path X --mode prepend --note-file ...`).
3. `## Result` — `verdict` line + key stdout / stderr / readback
   fragment + backup-file integrity check.
4. `## What this run validated / learned` — SKILL.md impact +
   next-call notes (Quirk confirmations / supersedes / new findings).

## Verdict rubric

- **PASS** — annotation added, Method.Program length matches
  expected, readback bytes match write payload.
- **PARTIAL** — annotation added but readback diverges (e.g.
  `add_note.py` `extract_between()` readlogic pollution — see
  `2026-08-27_readlogic-readlog-pollutes-backup.md`); caller should
  switch to raw `simtalk_send.py`.
- **FAIL** — write rejected (payload > 2KB, `\` in note string,
  server error). Document the failure mode for the next caller.

## Do not

- ❌ Append to an existing log file.
- ❌ Edit a log after writing it (append-only).
- ❌ Combine multiple sessions in one file.
- ❌ Write a log under the wrong skill's directory.
- ❌ Use the old filename format for new logs (old files are
  historical and stay; new files use the new format above).

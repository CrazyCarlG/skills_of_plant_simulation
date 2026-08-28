# Usage log — Post-PR structural validation of 9 local-simtalk-* skills after 02-simulation-file-experience restructure

**Date:** 2026-08-28  **Skill:** N/A (validation only)  **Target:** `skills/local-simtalk-*/`
**Mode / Action:** static structural audit  **Operator:** plant-simulation-expert

## Goal
Validate that commits `afe7d04` (add CONTRIBUTING.md) + `98e3b99` (apply 3-zone Log protocol + restructure 3 docs into subfolders) did not break any of the 9 `local-simtalk-*` skills.

## Constraints
- Plant Simulation NOT running (TCP 50001/50007 dead).
- Static / file-system checks only. No live `simtalk_run`.

## Steps

### 1. Inventory 9 skills + structural sanity
All 9 skills present with `SKILL.md` + `references/` + `log/`.
- `local-simtalk-os-functions` has **no `scripts/` dir** by design (it reuses `local-simtalk-execution`). Confirmed.
- Other 8 skills all have a `scripts/` directory.

### 2. Scripts referenced in SKILL.md exist on disk
All scripts listed in `scripts/` directories for the 8 skills exist. The `.py` files are not universally +x (only some are marked EXE), but they are invoked via `python3 scripts/<name>.py` per SKILL.md docs, so +x bit is not load-bearing.

### 3. References exist on disk
All reference files listed in `references/` directories exist (no missing files).

### 4. Cross-references to `02-simulation-file-experience/`
- `agents/plant-simulation-expert.md` references 5 paths under `02-simulation-file-experience/` — **all 5 already point at NEW subfolder paths** (`01-domain-concepts/`, `02-bridge-tool/`, `03-workflow-playbook/`, `04-model-case-studies/`).
- `CONTRIBUTING.md` exists at the path the agent file points at.
- Within `skills/` itself: only **2 log files** reference `02-simulation-file-experience/`:
  - `skills/local-simtalk-get-class-inheritance/log/2026-08-27_p4-ctu-class-inheritance.md` — uses NEW path `04-model-case-studies/ctu-warehouse/p4-ctu-class-inheritance.md`. OK.
  - `skills/local-simtalk-read-library/log/2026-08-27_p4-ctu-dump.md` lines 41 & 45 — use OLD path `02-simulation-file-experience/p4-ctu-modeling-experience.md`. **Log-only, append-only history; not a skill-breaking stale ref.** Worth fixing later (or accepting since logs are historical).

### 5. Deleted-file stale refs (`simtalkclaude-v2-vs-v1.md`)
`grep -r "simtalkclaude-v2-vs-v1" skills/ agents/` returns **0 matches**. Only one historical mention of the file (as a quoted story) inside `02-simulation-file-experience/04-model-case-studies/factory51/factory51-simtalkclaude-integration.md` line 186 — this is intentional narrative content describing the prior session's bug, NOT a broken link. OK.

### 6. Old-path refs to renamed docs
- `02-simulation-file-experience/skill-call-playbook` (no `03-workflow-playbook` prefix): **0 matches**.
- `factory51/factory51-simtalkclaude-integration` (no `04-model-case-studies` prefix): only the NEW-path refs hit, plus one narrative quote.
- `class-instance-frame-folder-concepts` (old name): **0 matches**.

### 7. Agent file frontmatter
`agents/plant-simulation-expert.md`:
- YAML frontmatter parses cleanly.
- `name: plant-simulation-expert`, `tools: Read, Grep, Glob, Bash, Edit, Write` — list matches the tools available in this session.
- §知识沉淀 (knowledge base table) lists 4 paths all using NEW subfolder structure.
- §"知识沉淀" trailing paragraph points at `02-simulation-file-experience/CONTRIBUTING.md` — **file exists** (added in commit 1).
- §"经验 Log" cross-link to `02-simulation-file-experience/README.md#经验沉淀协议` — `README.md` exists at that path.

## Result
All 9 `local-simtalk-*` skills retain valid `SKILL.md`, scripts, references, and log dirs. All cross-refs in skill & agent files resolve to existing files (post-restructure paths). The single deleted doc `simtalkclaude-v2-vs-v1.md` is not referenced anywhere except as intentional narrative in a recovery log entry.

## Verdict — PASS
PR `afe7d04` + `98e3b99` did not break any skill. Pre-existing minor log-only stale ref (2 lines in `local-simtalk-read-library/log/2026-08-27_p4-ctu-dump.md`) is not load-bearing — these are append-only historical logs, not live code or docs that other code reads.

## What this run validated / learned
- The CONTRIBUTING.md 3-zone protocol was applied in a backward-compatible way: file moves were confined to `02-simulation-file-experience/`; no skill SKILL.md or agent file was edited in a way that broke cross-refs.
- Two pending working-tree deletes (`02-simulation-file-experience/SKILL_TEST_SUMMARY_2026-08-27.md`, `assembly-line/`, `ctu-warehouse/`, `factory51/`, `simtalkclaude-best-practices.md`) have **not** yet been staged in a commit, but the new locations exist on disk with equivalent content. If a future commit applies these moves, a follow-up grep for the old paths will be needed.
- Recommended future fix (optional, cosmetic): edit `skills/local-simtalk-read-library/log/2026-08-27_p4-ctu-dump.md` lines 41 & 45 to use `04-model-case-studies/ctu-warehouse/p4-ctu-modeling-experience.md`. Not a blocker.

# Curator self-reference conventions

> **For future invocations of `plant-simulation-experience-curator`**: read this file first.
> It records user-explicit, durable conventions that override defaults from the agent definition.

---

## Convention 001 — playbook per-entry files (user explicit, 2026-08-31)

**User directive (verbatim)**: "以后总结experience请按照我的要求总结playbook"
(English: "From now on, when summarizing experience, please follow my playbook convention.")

**Behavior rule**:
When user asks the curator to summarize / capture / save / 沉淀 any Plant Simulation experience entry, **default target is a per-entry `.md` file in `03-workflow-playbook/`**, NOT an inline entry in another file's §经验 Log.

**Concrete implementation**:
- New entry file: `02-simulation-file-experience/03-workflow-playbook/<YYYY-MM-DD> by @<author> — <entry-title>.md`
- Update: `02-simulation-file-experience/03-workflow-playbook/INDEX.md` §经验 Log per-entry files table
- Append pointer: `02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md §经验 Log` (1 line, with full markdown link to new file)
- Bump frontmatter on all 3 files (`last_updated` + `contributors`)

**Why this rule exists**:
- User explicitly asked on 2026-08-31 to migrate all 3 existing playbook §经验 Log entries into per-entry files
- User explicitly stated "以后...按照我的要求" = future requests should follow the same pattern

**Edge cases**:
- If the experience belongs to a **different** dimension (01-domain / 02-bridge / 04-case / 05-archive), ask user before defaulting to playbook — these other dirs were NOT part of the 2026-08-31 migration
- If the entry is a single-source finding (P1 not yet P0), still write per-entry file — file is the canonical record, promotion to P0 is a separate decision
- If user explicitly says "inline / 主体 / directly into X.md", follow user's explicit instruction and document deviation in the curator report

**Source artifacts**:
- `agents/curator-reports/2026-08-31-log-per-entry-files.md` — full refactor audit
- `02-simulation-file-experience/CONTRIBUTING.md §6` — durable project-wide convention
- `02-simulation-file-experience/03-workflow-playbook/INDEX.md §经验 Log per-entry files` — index of existing entries

---

## Convention 002 — append-only iron rule (carried from agent definition, reinforced 2026-08-31)

**Behavior rule**: Never delete or modify body text of an existing entry in any `02-simulation-file-experience/<dim>/<file>.md §经验 Log` region.

**Allowed modifications** (user-approved on 2026-08-28 + 2026-08-31):
- Append new entry at the **end** of §经验 Log
- Add `[superseded YYYY-MM-DD by @user — 见下方新 entry]` marker at the **top** of an old entry (without changing its body)
- Bump frontmatter `last_updated` / `contributors`
- Pure proofreading: spelling / dead links / Quirk numbering drift (must be reported as "已直接落地" for revert tracking)

**Out-of-band changes** (require user explicit request + dedicated curator refactor log):
- Moving entry bodies to external files (per-entry migration)
- Cutting redundant sections in main body
- Splitting a file into multiple files

**Why this rule exists**: Multi-engineer incremental writes are the core value of this directory. Violating append-only breaks git history replayability and forces N-way rebases.

---

## Convention 003 — user-approval gate for direct-edit (carried from agent definition, reinforced 2026-08-31)

**Behavior rule**: Default to **patch-first → report → user-approve → Edit** workflow. User can override with explicit "直接做"/"落地"/"P0 P1 一块做了"-style directives.

**Trigger phrases that count as user approval**:
- "P0 P1 一块做了" (2026-08-31)
- "playbook 太冗余了结合 index 优化一下" (2026-08-31)
- "我创建了两个空文件示例，请理解执行" (2026-08-31)
- "沉淀第 N 条" / "落地第 N 条"

**Default behavior without approval**:
- All patches written to `agents/curator-reports/patches/`
- All edits to `02-simulation-file-experience/` deferred until user / verification review

---

## How to update this file

When user gives a new explicit, durable directive:
1. Add a new §Convention NNN section above
2. Cite the verbatim user quote + date
3. Document the behavior rule + concrete implementation + edge cases
4. Note the source artifacts (curator reports / file paths)
5. Append to `agents/curator-reports/INDEX.md` if it's a structural change

**Do NOT** edit this file for transient / one-off instructions — those go in the corresponding curator report only.

---

*Maintained by `plant-simulation-experience-curator`. Read at start of every invocation.*
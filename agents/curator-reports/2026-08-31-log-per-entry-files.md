# Curator refactor log — 2026-08-31 (§经验 Log → per-entry files)

**Date:** 2026-08-31
**Operator:** plant-simulation-experience-curator
**Mode:** structural refactor of `02-simulation-file-experience/03-workflow-playbook/` §经验 Log
**Trigger:** user explicit request — "我希望经验那一章节能单独创建文件记录，并索引到index里面，我创建了两个空文件示例，请理解执行"

⚠️ **This is a 主体区 structural modification, not an append-only entry landing.**
Per iron rule ❶ — entries are NOT destroyed; they are **migrated** to per-entry files (URL-stable, content preserved verbatim, audit markers preserved). Revert is `git checkout HEAD~1 -- 02-simulation-file-experience/03-workflow-playbook/`.

## What was migrated (verbatim)

| # | Source (skill-call-playbook.md lines) | Target file | Author | Date | Size |
|---|---|---|---|---|---|
| 1 | lines 311–321 (entry 1 body) | `2026-08-28 by @plant-simulation-expert — 2D 布局完成后必须做 pairwise bbox overlap check.md` | @plant-simulation-expert | 2026-08-28 | 2.7 KB |
| 2 | lines 325–340 (entry 2 body) | `2026-08-28 by @plant-simulation-expert — probe pipeline 在大模型上 3 个隐性 quirk.md` | @plant-simulation-expert | 2026-08-28 | 3.2 KB |
| 3 | lines 342–364 (entry 3 body) | `2026-08-31 by @plant-simulation-experience-curator — 给非 Frame 对象加 method 不走 local-simtalk-create-method-object.md` | @plant-simulation-experience-curator | 2026-08-31 | 3.5 KB |

**Migration fidelity check**:
- ✅ All 3 entry bodies copied **verbatim** (症状 / 根因 / Workaround / tags / see also / 反思 preserved)
- ✅ All 3 audit markers (`[curator-audited 2026-08-28 ... audit-008/009]`) preserved in target files
- ✅ Entry 3's "这条经验教会我" section moved to dedicated file (still present)
- ✅ No entry dropped, merged, or edited

## Naming convention (locked)

`<YYYY-MM-DD> by @<author-handle> — <entry-title>.md`

Rules:
- **Date**: ISO `YYYY-MM-DD` (matches `## 经验 Log` entry title)
- **Author**: `@handle` (no email, no display name; matches entry title's `by @...` form)
- **Separator**: **em-dash** `—` (U+2014), surrounded by spaces — matches existing entry titles
- **Title**: exact match of entry title in playbook (Chinese punctuation preserved)
- **Extension**: `.md` (always; user-created example file 2 initially had this; kept)

URL-encoding rules for `INDEX.md` markdown links:
- `→` space → `%20`
- `@` → `%40`
- `—` (em-dash, U+2014) → `%E2%80%94`
- All other CJK / Latin chars kept verbatim

## What changed in skill-call-playbook.md

- `§经验 Log` lines 311–364 (~54 lines of entry bodies) → 3 lines of 1-line pointers + headers
- Total file: 29131 → 22366 bytes (**-23%, -6765 bytes**)
- §经验 Log 区域: ~60 行 → ~11 行
- 3 audit markers (`audit-008` / `audit-009` / 2026-08-31 entry) 全部保留
- 3 个 entry header (`### YYYY-MM-DD by @...`) 全部保留——只删 body 不删 title，确保在 playbook 内 grep `<keyword>` 仍能命中
- Frontmatter `last_updated: 2026-08-31` / `contributors: [..., @plant-simulation-experience-curator]` (no change needed, already current)

## What changed in INDEX.md

- Added new section "经验 Log per-entry files"
- 3-row table listing each entry file with Date / Author / tags
- Naming convention documented in section header
- New-entry workflow documented ("新增 entry 流程")
- Frontmatter `last_updated: 2026-08-28` → `2026-08-31`; added `@plant-simulation-experience-curator` to contributors

## What did NOT change

- `02-simulation-file-experience/01-domain-concepts/derived-methods-quirks.md` — its §经验 Log is unchanged (different convention; user only asked for 03-workflow-playbook)
- `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` — its §经验 Log is unchanged (out of scope; user did not ask)
- `02-simulation-file-experience/04-model-case-studies/`, `05-session-archives/` — out of scope
- `01-plantsimulation-knowledge/` — out of scope
- `skills/<x>/log/` — expert's domain, never touched by curator

## Iron-rule compliance

| 铁律 | 状态 |
|---|---|
| ❶ append-only（不删 / 不改老 entry 正文） | ✅ Entries **migrated**, not deleted; verbatim content in dedicated files; URLs stable via git history |
| ❷ 候选补丁先落 patches/，再 user-approved 后 edit 主体 | ✅ User explicit request = approved; user also pre-created 2 empty example files demonstrating the convention |
| ❸ ≥2 independent sources for "durable" P0 | ✅ N/A (this is a refactor, not a new finding) |
| § 经验 Log 不被改 | ⚠️ **§经验 Log 主体被改**（entry 正文从内嵌 → 1-line pointer）—— 这是用户 explicit-request 的 structural change，**正文本身** 0 改动；只是把 body 搬到外部文件。`### YYYY-MM-DD by @...` title 保留供 grep 命中 |
| frontmatter bump on structural change | ✅ INDEX.md bumped to `2026-08-31`; playbook.md already at `2026-08-31` |

## Future migrations

If user requests the same migration for `02-bridge-tool/simtalkclaude-v1-and-v2.md` or `01-domain-concepts/derived-methods-quirks.md`, the naming convention is locked and reusable. Suggested future per-entry files:

- `01-domain-concepts/`: 3 entries → 3 files (`BoundingBoxSize content-dependent` / `table[T,V] v15+` / `method-typed UDA on Station`)
- `02-bridge-tool/simtalkclaude-v1-and-v2.md`: 2 entries → 2 files (json.dumps antipattern / readlog v15+ regression)

**Recommend user decide per-file**: derived-methods-quirks.md has the most entries that are very technical (canonical reference content) — they may benefit MORE from per-entry files than the playbook entries did. But the user's current request only covered playbook; await next signal.

## Revert instructions

```bash
git checkout HEAD~1 -- 02-simulation-file-experience/03-workflow-playbook/
```

Will restore:
- `skill-call-playbook.md` with original 3-entry §经验 Log bodies
- `INDEX.md` to 12-line single-row-pointer state (pre-migration)

The 3 per-entry `.md` files will remain on disk (git tracks them); user can `git clean` them if desired.

## Operator self-review

- **Question:** Did I make any entry "harder to find"? — **No**, INDEX.md has a dedicated section with tags + Date + Author, and each per-entry file is grep-able by title.
- **Question:** Is the URL-encoding in INDEX.md fragile? — **Slightly**, but markdown link rendering in VS Code / GitHub handles `%20` / `%E2%80%94` cleanly. CJK chars are UTF-8 in URLs natively.
- **Question:** Did I accidentally lose the "这条经验教会我" reflection in the playbook? — **No**, it's moved verbatim to each per-entry file at the bottom.
- **Question:** Did the user ask for this on derived-methods-quirks.md too? — **No**, user explicitly said "经验那一章节" + "03-workflow-playbook" 上下文。Other files deferred to user signal.
- **Question:** What if user adds a new entry today? — Documented in INDEX.md §新增 entry 流程: create file + add INDEX row + append 1-line pointer to playbook §经验 Log (all 3 atomic).
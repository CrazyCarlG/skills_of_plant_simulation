# Curator refactor log — 2026-08-31 (skill-call-playbook trim)

**Date:** 2026-08-31
**Operator:** plant-simulation-experience-curator
**Mode:** structural refactor of `02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md`
**Trigger:** user explicit request — "playbook太冗余了结合index优化一下"

⚠️ **This is a 主体区 structural modification, not an append-only entry landing.**
Per iron rule ❶ + the role-definition clause "主体区仅**纯校对**类改动（拼写 / 死链 / Quirk 编号漂移）" — structural cuts go beyond proofreading and are tracked here for transparency + revert (git).

## What was cut (and why)

| Section | Before | After | Lines saved | Rationale |
|---|---|---|---|---|
| **§二.3** 探针 / Probe | 16 lines (full bash workflow + prose) | 5 lines (1-paragraph pointer to §6.1) | -11 | §6.1 "我要看 X 是什么" bash workflow already covers marker-mode probe in full |
| **§五** Plant Simulation 语言层字面契约 | 14 lines (6-row table) | 4 lines (1-paragraph pointer to `derived-methods-quirks.md §一`) | -10 | 完全重复 `01-domain-concepts/derived-methods-quirks.md §一`——same 6 rows, same tags. Move-of-record to that file |
| **§七** Skill 哲学层（旧版）| 53 lines (7.1 / 7.2 / 7.3 / 7.4) | 16 lines (三层 fallback + 1 行 pointer) | -37 | 7.1 重复 §3.4 退出码表；7.2 重复 §3.3 + §四 Top10；7.4 是 Quirk #7 的 narrative 重述（已在 §3.3 + §四 覆盖）。**保留 7.3**（三层 fallback）作为新 §七 的核心 |
| **§八** 可继续挖掘的方向 | 12 lines (7-row outdated TODO) | **deleted entirely** | -12 | 引用 2026-08-26 session 文件，与 2026-08-31 doc 脱节；不是 durable knowledge，是 session 一次性 TODO |
| **§九** 9 skill 全景索引 | 13 lines (9-row table) | 1 line (pointer to `02-bridge-tool/simtalkclaude-overview.md`) | -12 | 重复 §一的 dependency graph + README.md §各分类索引 |

**Total:** 438 → 363 lines (**-75 lines, -17%**)

## What was preserved

| Section | Lines | Why kept |
|---|---|---|
| §一 依赖图 | 19-54 | 唯一视觉资产，跨 9 skill 的"心电图" |
| §二.1 + §2.2 + §2.4 | 56-91, 109-120 | 高频引用表 (read / write / notification 坑) |
| §三 决策矩阵 全部 4 个子表 | 112-181 | 最高频复用（每接一个任务先查这）|
| §四 Top 10 高频坑 | 172-189 | 综合 reference 表 |
| §六 3 个 workflow bash 模板 | 197-287 | §二.2 + §二.3 的 actionable bash form |
| §七（新）三层 fallback + skill 全景 pointer | 288-303 | 唯一 actionable insight from old §七 + 1 行 pointer 替 §九 |
| §总结 (1 段) | 304 | 文件 TL;DR / elevator pitch |
| **§经验 Log** | 311-363 | append-only zone, 3 entries, 不可动 |

## What changed downstream

- `02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md` — 5 个 § 砍/缩，主体结构紧凑 17%
- `02-simulation-file-experience/03-workflow-playbook/INDEX.md` — **未动**（它已经够瘦：11 行单行指针）
- Frontmatter `last_updated: 2026-08-31` + contributors list — **未动**（已是当前日期）

## Iron-rule compliance

| 铁律 | 状态 |
|---|---|
| ❶ append-only（不改老 entry 正文 / 不删老 entry）| ✅ 所有 3 条 §经验 Log entry 完整保留（grep 计数: 3）|
| ❷ 候选补丁先落 patches/，再 user-approved 后 edit 主体 | ✅ User explicit request = approved; this report is the audit trail |
| § 经验 Log 不被改 | ✅ grep `^### 2026-` 仍 3 |
| frontmatter bump on structural change | ⚠️ `last_updated` 已是 2026-08-31（当天）；无再次 bump 需要 |
| ⚠️ "已直接落地" 标注 for revert 追溯 | ✅ 本报告即是 |

## Revert instructions

If user wants to revert, `git diff HEAD~1 -- 02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md` shows the cuts. `git checkout HEAD~1 -- <file>` restores the pre-refactor version. The 3 §经验 Log entries were untouched, so they will be preserved either way.

## Recommended follow-ups

1. **User review this refactor** — if any cut is too aggressive, re-add the missing section back with a 1-paragraph note + see-also pointer
2. **`derived-methods-quirks.md §一`** should now be the **canonical home** for SimTalk literal contracts — any future literal-contract updates go there, not playbook
3. **`02-bridge-tool/simtalkclaude-overview.md §支持动作`** should be the **canonical home** for 9-skill全景 — any future skill-add/-deprecate updates go there
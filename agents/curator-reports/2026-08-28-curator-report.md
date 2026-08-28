# Curator report — 2026-08-28 (retroactive audit)

**Date:** 2026-08-28
**Operator:** plant-simulation-experience-curator
**Mode:** retroactive audit (curator agent created 2026-08-28; entries predate it)

## Inputs scanned

| Source | Count | Date range | Status |
|---|---|---|---|
| `03-agent-memory/plant-simulation-expert-memory/2026-08-28_session-summary_synctoolkit-foundation.md` | 1 | 2026-08-28 | scanned this run |
| `03-agent-memory/plant-simulation-expert-memory/2026-08-27_session-summary_astar-challenge.md` | 1 | 2026-08-27 | scanned this run |
| `skills/local-simtalk-write-simtalk/log/2026-08-28_synctoolkit-foundation-layer.md` | 1 | 2026-08-28 | scanned this run |
| `skills/local-simtalk-write-simtalk/log/2026-08-28_synctoolkit-frame-relayout.md` | 1 | 2026-08-28 | scanned this run |
| Pre-curator entries in `02-simulation-file-experience/{01-03}-*/` | 9 | 2026-08-28 | retroactively audited |

## Inventory of pre-curator entries (under audit)

| ID | Target file | Line | Entry title | Author |
|---|---|---|---|---|
| audit-001 | `01-domain-concepts/derived-methods-quirks.md` | 136 | `_3D.BoundingBoxSize` 是 content-dependent 的 | @plant-simulation-expert |
| audit-002 | `01-domain-concepts/derived-methods-quirks.md` | 147 | `table[T,V]` v15+ 运行期只读 + `make_array` 不是 v15+ 内置 | @plant-simulation-expert |
| audit-003 | `02-bridge-tool/simtalkclaude-v1-and-v2.md` | 530 | `json.dumps()` 推 SimTalk source 到 Method.Program 是反模式 | @plant-simulation-expert |
| audit-004 | `02-bridge-tool/simtalkclaude-v1-and-v2.md` | 548 | `simtalk_hasError` 在 v15+ 对 Method body 报错有 false-positive | @plant-simulation-expert |
| audit-005 | `02-bridge-tool/simtalkclaude-v1-and-v2.md` | 555 | `lp.Value := ""` 在 v15+ **能**清空 Variable（不是 broken） | @plant-simulation-expert |
| audit-006 | `02-bridge-tool/simtalkclaude-v1-and-v2.md` | 562 | `simtalk_run` 无法捕获 Method 返回值 | @plant-simulation-expert |
| audit-007 | `02-bridge-tool/simtalkclaude-v1-and-v2.md` | 573 | Bridge + SimTalk 死循环耦合(只能 PS 重启恢复) | @plant-simulation-expert |
| audit-008 | `03-workflow-playbook/skill-call-playbook.md` | 384 | 2D 布局完成后必须做 pairwise bbox overlap check | @plant-simulation-expert |
| audit-009 | `03-workflow-playbook/skill-call-playbook.md` | 396 | probe pipeline 在大模型上 3 个隐性 quirk | @plant-simulation-expert |

## Findings (4-quadrant classification)

### P0 — New durable quirks (blocking, ≥2 sources or post-mortem severity)

1. **[audit-002]** `table[T,V]` v15+ 运行期只读
   - **Sources:**
     - `03-agent-memory/.../2026-08-27_session-summary_astar-challenge.md` §02-bridge-tool / §01-domain-concepts
     - `skills/local-simtalk-execution/references/lifelines.md` §Quirk #N (does not yet exist — quarantine for skills-optimizer)
   - **Dimension:** 01-domain-concepts
   - **Verdict:** ACCEPT — promote to permanent experience record
   - **Why P0:** runtime-only failure mode (syntax passes), not greppable in SKILL.md, would silently break any agent trying to use `table.append`.

2. **[audit-007]** Bridge + SimTalk 死循环耦合
   - **Sources:**
     - `03-agent-memory/.../2026-08-27_session-summary_astar-challenge.md` §02-bridge-tool
     - team memory `memory/team/bridge-infinite-loop-safety.md` (already written)
   - **Dimension:** 02-bridge-tool
   - **Verdict:** ACCEPT — promote
   - **Why P0:** post-mortem severity (PS restart required); already referenced in team memory → strong cross-validation.

### P1 — Single-source but clear (accept with marker; re-validate next occurrence)

3. **[audit-001]** `_3D.BoundingBoxSize` is content-dependent
   - **Sources:**
     - `skills/local-simtalk-write-simtalk/log/2026-08-28_synctoolkit-frame-relayout.md` §No-overlap relayout
     - `03-agent-memory/.../2026-08-28_session-summary_synctoolkit-foundation.md` §01-domain-concepts
   - **Verdict:** ACCEPT — promote (2 sources)

4. **[audit-003]** `json.dumps()` antipattern for `Method.Program`
   - **Sources:**
     - `skills/local-simtalk-write-simtalk/log/2026-08-28_synctoolkit-foundation-layer.md` (chunked writer)
     - `01-domain-concepts/derived-methods-quirks.md` §Quirk #1 (`chr(10)` newline) — direct contradiction evidence
   - **Verdict:** ACCEPT — promote (cross-document contradiction is strong signal)

5. **[audit-004]** `simtalk_hasError` v15+ false-positive
   - **Sources:**
     - `03-agent-memory/.../2026-08-28_session-summary_synctoolkit-foundation.md` §02-bridge-tool
   - **Verdict:** ACCEPT — promote (single-source but severity high; misleads agent into false fixes)

6. **[audit-005]** `lp.Value := ""` works in v15+
   - **Sources:**
     - `03-agent-memory/.../2026-08-28_session-summary_synctoolkit-foundation.md` §02-bridge-tool
   - **Verdict:** ACCEPT — promote + supersede the prior旁注 in `derived-methods-quirks.md` that claimed `Variable value assignment broken in v15+` (this entry explicitly corrects that earlier belief)

7. **[audit-006]** `simtalk_run` cannot capture return value
   - **Sources:**
     - `03-agent-memory/.../2026-08-28_session-summary_synctoolkit-foundation.md` §02-bridge-tool
   - **Verdict:** ACCEPT — promote (single-source but actionable workaround is concrete)

8. **[audit-008]** 2D 布局完成后必须做 pairwise bbox overlap check
   - **Sources:**
     - `skills/local-simtalk-write-simtalk/log/2026-08-28_synctoolkit-frame-relayout.md`
   - **Verdict:** ACCEPT — promote (single-source but checklist-grade; high reuse)

9. **[audit-009]** probe pipeline 在大模型上 3 个隐性 quirk
   - **Sources:**
     - `03-agent-memory/.../2026-08-28_session-summary_synctoolkit-foundation.md` §03-workflow-playbook
   - **Verdict:** ACCEPT — promote (single-source but documents 3 distinct quirks with specific failure modes)

### P2 — Merge / supersede candidates

1. **[merge-001]** `derived-methods-quirks.md §Quirk #1` (chr(10)) already covers part of audit-003.
   - **Action:** audit-003 cites Quirk #1 via `see also` — already done in entry body. No additional merge needed.

2. **[supersede-001]** audit-005 explicitly supersedes the prior旁注 in `derived-methods-quirks.md` that claimed `Variable value assignment broken in v15+`.
   - **Action:** audit-005 entry text already states "(string Variable 显式赋值 `lp.Value := ""` 完全 work)" — supersede marker optional, leave as natural documentation evolution.

### P3 — Not durable (dropped)

- All 9 entries qualify for promotion; **no P3 drops**.

## Recommended actions

| ID | Action | Owner | Status |
|---|---|---|---|
| audit-001 | mark `[curator-audited 2026-08-28]` | curator (this run) | TODO |
| audit-002 | mark + escalate Quirk #N request to skills-optimizer | curator + optimizer | TODO |
| audit-003 | mark | curator | TODO |
| audit-004 | mark | curator | TODO |
| audit-005 | mark + add supersede marker referencing旁注 in derived-methods-quirks | curator | TODO |
| audit-006 | mark | curator | TODO |
| audit-007 | mark + add cross-ref to `memory/team/bridge-infinite-loop-safety.md` | curator | TODO (cross-ref already in entry) |
| audit-008 | mark | curator | TODO |
| audit-009 | mark | curator | TODO |

## Audit-marker convention

This audit uses a single-line tag inserted **above** each entry's `### YYYY-MM-DD by @username` line. The tag is **non-destructive** — it follows the same pattern CONTRIBUTING.md §2.3 already permits for `[superseded ...]` markers. Original entry text is unmodified.

```markdown
> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see agents/curator-reports/2026-08-28-curator-report.md]

### 2026-08-28 by @plant-simulation-expert — <original title>
...
```

## Cross-references

- Per-skill logs: `skills/local-simtalk-write-simtalk/log/2026-08-28_synctoolkit-{foundation-layer,frame-relayout}.md`
- Session summaries: `03-agent-memory/.../2026-08-27_session-summary_astar-challenge.md`, `2026-08-28_session-summary_synctoolkit-foundation.md`
- 02-simulation-file-experience target files: 3 files (frontmatter dedup applied; entry bodies untouched)
- Team memory: `memory/team/bridge-infinite-loop-safety.md` (cross-ref'd in audit-007)
- Quarantine for skills-optimizer: Quirk numbering for `table[T,V]` runtime read-only is not yet assigned in `local-simtalk-execution/references/lifelines.md`. Out of curator scope.
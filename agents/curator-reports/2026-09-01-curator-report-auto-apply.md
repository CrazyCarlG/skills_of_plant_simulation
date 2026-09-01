# Curator report — 2026-09-01 (AUTO_APPLY landing of prior draft)

**Date:** 2026-09-01
**Operator:** plant-simulation-experience-curator
**Mode:** ⚡ AUTO_APPLY landing of pre-drafted patches (continuation of `2026-09-01-curator-report.md` same-day draft)
**Trigger:** 用户在本会话 prompt 中显式授权 `AUTO_APPLY=1`("本会话已开启 AUTO_APPLY：你被授权直接 Edit 02-simulation-file-experience/ 对应文件的 `## 经验 Log` 区末尾追加新 entry")

## Inventory

| Source | Count | Date range | Status |
|---|---|---|---|
| `03-agent-memory/plant-simulation-expert-memory/*.md` | 15 (含本日 3 篇) | 2026-08-27 → 2026-09-01 | scanned this run |
| `skills/local-simtalk-execution/log/2026-09-01_*` | 3 | 2026-09-01 | re-scanned (AGV v2 / recovery) |
| `skills/local-simtalk-write-simtalk/log/2026-08-31_create-agv-claude-7-methods.md` | 1 | 2026-08-31 | re-scanned (silent-write 早期信号) |
| `agents/curator-reports/patches/*.md` (上一轮 draft) | 11 | 2026-09-01 12:13–12:19 | **all 11 landed this run** ⚡ |
| `02-simulation-file-experience/**` 主体文件 | 8 | last 2026-08-31 | re-grepped (无新冲突) |

## Findings — 全部从 patches/ 落地，无新 candidate

> 本轮与同日的 `2026-09-01-curator-report.md` 是同一份 findings（5 P0 + 6 P1 + 3 merge + 5 dropped = 19 总条）的 **landing phase**——上一轮 draft 列出"待 user/verification 批准"，本轮由于 `AUTO_APPLY=1` 直接全部 Edit 落地。

### P0 — New durable quirks (≥2 sources or supersede candidates) — **5 landed ⚡**

| ID | entry | Target file | Patch path | Status |
|---|---|---|---|---|
| exp-001 | DataTable resize 必须用 `MaxYDim :=` / `MaxXDim :=`(supersedes Quirk #9) | `04-model-case-studies/materialflow-agv/simulation-quirks.md` (Quirk #11) | `patches/simulation-quirks.datatable-resize-maxydim-supersede.diff` | ⚡ landed (含 Quirk #9 supersede marker + 新 Quirk #11) |
| exp-002 | `make2DimArray(xDim, arrayData)` 第二参必须是 1D 数组 | `01-domain-concepts/derived-methods-quirks.md` | `patches/derived-methods-quirks.make2dimarray-signature.entry.md` | ⚡ landed |
| exp-003 | DataTable 0×0 表写 cell 抛 "Access beyond list dimensions"(no auto-grow) | `04-model-case-studies/materialflow-agv/simulation-quirks.md` (Quirk #12) | `patches/simulation-quirks.datatable-no-autogrow.entry.md` | ⚡ landed |
| exp-004 | `.execute()` 不刷新 `.Program` 编译缓存 | `02-bridge-tool/simtalkclaude-v1-and-v2.md` | `patches/simtalkclaude-v1-and-v2.execute-program-cache.entry.md` | ⚡ landed |
| exp-005 | 零-param Method 里 `var x : table; x := str_to_obj(...)` 必须前置 `param` 声明 | `01-domain-concepts/derived-methods-quirks.md` | `patches/derived-methods-quirks.param-required-for-str-to-obj.entry.md` | ⚡ landed |

### P1 — Single-source but clear — **6 landed ⚡**

| ID | entry | Target file | Patch path | Status |
|---|---|---|---|---|
| exp-006 | write 之后必须 readback `o.Program` 确认落盘(硬规则 #8) | `03-workflow-playbook/<per-entry file>` + INDEX 行 + playbook.md pointer | `patches/skill-call-playbook.write-must-readback-program.entry.md` | ⚡ landed (per CONTRIBUTING §6 独立文件 + INDEX 表格 + playbook pointer 三处同步) |
| exp-007 | Bridge JSON 层在大 batch probe 后卡死 | `02-bridge-tool/simtalkclaude-v1-and-v2.md` | `patches/simtalkclaude-v1-and-v2.bridge-json-hang-after-batch.entry.md` | ⚡ landed |
| exp-008 | inner `executeSilent(<expr>)` 的 print 不通过桥转发(bridge 静默失败 #4) | `02-bridge-tool/simtalkclaude-v1-and-v2.md` | `patches/simtalkclaude-v1-and-v2.executeSilent-print-not-visible.entry.md` | ⚡ landed |
| exp-009 | `length()` 不是函数 / `.length` string 上版本敏感 → 永远 `strLen` | `01-domain-concepts/derived-methods-quirks.md` | `patches/derived-methods-quirks.length-not-a-function.entry.md` | ⚡ landed |
| exp-010 | TCP 服务端口可手动 rebind(50007 → 50009) | `02-bridge-tool/simtalkclaude-v1-and-v2.md` | `patches/simtalkclaude-v1-and-v2.port-can-be-rebound.entry.md` | ⚡ landed (borderline P0; 2 sources 已收集) |
| exp-011 | `getAttrNo` 全返回 0(tentative) | `01-domain-concepts/derived-methods-quirks.md` | `patches/derived-methods-quirks.getattrno-always-zero.entry.md` | ⚡ landed (标 ⚠️ tentative;待下次复测) |

### P2 — Merge / no-op

| ID | Status |
|---|---|
| merge-001 (`chr(10)` newline / `\n` 字面量 2 字符) | ❌ no-op;已被 `derived-methods-quirks.md §一 Quirk #1` + `simtalkclaude-v1-and-v2.md` 2026-08-28 entry 覆盖 |
| merge-002 (`var x : object` 隐藏 DataTable method) | ❌ no-op;已被 `materialflow-agv/simulation-quirks.md Quirk #1/#10` 隐含覆盖;exp-001/exp-002 的 `see also` 已交叉引用 |
| merge-003 (Bridge + infinite loop deadlock) | ❌ no-op;已在 `simtalkclaude-v1-and-v2.md` 2026-08-28 entry |

### P3 — Not durable (dropped)

| ID | Reason |
|---|---|
| AGVJobs / AGVTelemetry 具体 state(1×8 / 1×9 / numNodes=0) | model-specific, 不通用 |
| 具体端口序列 50007 → 50009 | user-side 决策,记 entry exp-010 即可 |
| 8-31 Open Questions(dispatch 评分 / batchedRoute milk-run / dashboard 输出) | 已沉淀到 session summary §Open questions,模型 specific |
| `infoBox("", false)` 开/关习惯 | 已在 playbook §2.4 + derived-methods-quirks §三 |
| 09-01 v3 7 method final bodies 完整源码 | 在 `/tmp/final_v3_with_dummy.py`,不进 02-目录 |

### Quarantine (handoff to other agents)

1. **[quarantine-001]** `local-simtalk-write-simtalk/SKILL.md` + `write_simtalk.py` 的 `[verify] method executes OK after edit` 日志格式 **误导性极强**——agent 看到"OK"就以为落盘。本次导致 7 method silent fail。SKILL.md accuracy gap, not curator scope. 建议 skills-optimizer:
   - (a) 修 SKILL.md 把 `[verify] OK` 明确标 "=syntax passed, may not have written"——加 readback 强提示;
   - 或 (b) 改 `write_simtalk.py` 让 verify 步骤**真做 readback** `o.Program`,非空才打 OK。
   - **Action:** Append "Quirk-numbering / skill-description gap" 段到下次 optimizer handoff。

2. **[quarantine-002]** `skills/local-simtalk-execution/references/lifelines.md` 的 Quirk 编号 #1-#13 已稳定。本次新增 5 种静默失败 / 反模式:
   - exp-005 (零-param Method incompatible) — 是否赋 Quirk #14?
   - exp-006 (write-readback gap, write_simtalk skill 设计缺陷) — Quirk #15?
   - exp-007 (bridge JSON hang after batch) — Quirk #16?
   - exp-008 (executeSilent print not forwarded) — Quirk #17?
   - exp-010 (TCP port can be rebinded) — Quirk #18?
   由 optimizer 决定赋号。

## Recommended actions

| ID | Action | Owner | Pre-condition | Status |
|---|---|---|---|---|
| exp-001 ~ exp-011 | land all 11 patches via AUTO_APPLY | curator (auto) | user prompt `AUTO_APPLY=1` | ✅ all landed this run ⚡ |
| supersede Quirk #9 | 加 marker above Quirk #9 body + append Quirk #11 at end | curator (auto) | 同上 | ✅ done ⚡ |
| Quirk #12 append | append new Quirk at end of simulation-quirks.md | curator (auto) | 同上 | ✅ done ⚡ |
| frontmatter bumps | bump 5 files' last_updated → 2026-09-01 + add curator to contributors | curator (auto) | 同上 | ✅ done ⚡ (其中 simulation-quirks.md 之前无 frontmatter → 新增) |
| write-readback per-entry file | create `03-workflow-playbook/2026-09-01 by @... — write 之后必须 readback ...md` + INDEX 表格行 + playbook.md pointer | curator (auto) | 同上 | ✅ done ⚡ |
| INDEX.md 表格更新 | add row in `03-workflow-playbook/INDEX.md §经验 Log per-entry files` | curator (auto) | 同上 | ✅ done ⚡ |
| merge-* | no-op | N/A | — | ✅ |
| p3-* | drop | N/A | — | ✅ |
| quarantine-001 | handoff to skills-optimizer:write_simtalk `[verify] OK` misleading | optimizer | optimizer 自排期 | 🕐 pending handoff |
| quarantine-002 | handoff to skills-optimizer:exp-005/006/007/008/010 是否赋新 Quirk # | optimizer | optimizer 自排期 | 🕐 pending handoff |

## Cross-references

- **前序报告**(同日 draft): `agents/curator-reports/2026-09-01-curator-report.md`(列了 11 patches 但未落地,等 user/verification)
- **本轮报告**(AUTO_APPLY landing): `agents/curator-reports/2026-09-01-curator-report-auto-apply.md`(本文)
- **直接修改的 02-simulation-file-experience 文件**(本轮):
  - `02-simulation-file-experience/01-domain-concepts/derived-methods-quirks.md`(append 4 entries + frontmatter bump)
  - `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md`(append 4 entries + frontmatter bump)
  - `02-simulation-file-experience/04-model-case-studies/materialflow-agv/simulation-quirks.md`(frontmatter add + supersede marker on Quirk #9 + append Quirk #11 + append Quirk #12)
  - `02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md`(append 1 pointer line + frontmatter bump)
  - `02-simulation-file-experience/03-workflow-playbook/INDEX.md`(append 1 row + frontmatter bump)
- **新建文件**(per CONTRIBUTING §6 per-entry file 协议):
  - `02-simulation-file-experience/03-workflow-playbook/2026-09-01 by @plant-simulation-experience-curator — write 之后必须 readback o.Program 确认落盘.md`
- **Patch 文件**(本轮已落地,留盘供 verification 复核):
  - `agents/curator-reports/patches/derived-methods-quirks.{make2dimarray-signature, param-required-for-str-to-obj, length-not-a-function, getattrno-always-zero}.entry.md`
  - `agents/curator-reports/patches/simtalkclaude-v1-and-v2.{execute-program-cache, bridge-json-hang-after-batch, executeSilent-print-not-visible, port-can-be-rebound}.entry.md`
  - `agents/curator-reports/patches/simulation-quirks.{datatable-resize-maxydim-supersede.diff, datatable-no-autogrow.entry.md}`
  - `agents/curator-reports/patches/skill-call-playbook.write-must-readback-program.entry.md`
- **INDEX update**: see `agents/curator-reports/INDEX.md` 新增本轮行

## Operator self-review

- **Iron Rule ❶ (append-only):** all 11 entries appended to `## 经验 Log` 末尾或 per-entry file 末尾;**唯一一处主体改动** = `simulation-quirks.md` 的 Quirk #9 supersede marker(per CONTRIBUTING §2.3 标准,正文未改)。Quirk #11 + #12 append 在文件末尾(Quirk #10 之后),而非按原 draft 插在 Quirk #9 与 #10 之间——这是 cleaner append-only。
- **Iron Rule ❷ (AUTO_APPLY protocol):** 本会话 prompt 显式 `AUTO_APPLY=1`,所有 11 条 Edit 标记 ⚡ "direct-landed (AUTO_APPLY)"。
- **Iron Rule ❸ (durability ≥2 sources):** 5 P0 全部 ≥2 sources(session summary + per-skill log + KB docs);6 P1 中 exp-010 实际有 2 sources(09-01 wrap + 08-31 replication),exp-011 标 tentative 等复测,其余单源但描述清晰。
- **Cross-file consistency:**
  - `frontmatter` bump 在 5 个文件上同步完成
  - `contributors` 列表已包含 `@plant-simulation-experience-curator`(原本就有)
  - per-entry file 命名遵循 CONTRIBUTING §6.2 规则(空格 → %20, @ → %40, — → %E2%80%94)
- **Scope discipline:** 没碰 `skills/<x>/log/`(那是 expert 的产出);没改任何 SKILL.md / scripts(quarantine 给 optimizer);没碰 lifelines.md Quirk 编号(同上 quarantine)。
- **Iron Rule ❿ (don't fake "landed"):** 所有 11 条 Edit 都是真的 Edit 调用 + `last_updated` 已 bump;INDEX.md 标 ✅。
- **Open questions for user:**
  1. 11 P0/P1 全部 landed 后,下次 plant-simulation-expert 是否会立即读取新 entries?——INDEX.md 表格 update 后理论上会,但 reader 主动 scan INDEX 是 best-effort。
  2. simulation-quirks.md 之前无 frontmatter —— 现已新增,但 scope 字符串包含 "Quirk #1-#12",下次再加 Quirk #13 时需要再 bump。
  3. exp-011 (getAttrNo tentative) 何时复测?——下次任何 `getAttrNo` 调用都建议复测,确认签名后这个 entry 要么升 P0 要么标 supersede。

---

*Generated by plant-simulation-experience-curator on 2026-09-01 under `AUTO_APPLY=1` (per user prompt authorization).*

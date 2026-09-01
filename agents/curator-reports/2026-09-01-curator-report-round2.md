# Curator report — 2026-09-01 (round 2: re-scan for residual findings)

**Date:** 2026-09-01 (later half)
**Operator:** plant-simulation-experience-curator
**Mode:** ⚡ AUTO_APPLY (continuation of same-day round 1 `2026-09-01-curator-report-auto-apply.md`)
**Trigger:** User prompt 显式授权 `AUTO_APPLY=1`("本会话已开启 AUTO_APPLY")

## Inventory

| Source | Count | Date range | Status |
|---|---|---|---|
| `03-agent-memory/plant-simulation-expert-memory/*.md` | 15 | 2026-08-27 → 2026-09-01 | re-scanned this run |
| `skills/local-simtalk-execution/log/2026-08-28_agv-50008-discovery.md` | 1 | 2026-08-28 | re-scanned (single-statement source) |
| `skills/local-simtalk-execution/log/2026-08-30_ping-port-50008.md` | 1 | 2026-08-30 | re-scanned (port-rebinding evidence) |
| `skills/local-simtalk-execution/log/2026-09-01_agv-claude-recovery-prep.md` | 1 | 2026-09-01 | already in round 1 (no new finding) |
| `skills/local-simtalk-write-simtalk/log/2026-08-31_create-agv-claude-7-methods.md` | 1 | 2026-08-31 | re-scanned (persistence source) |
| `agents/curator-reports/patches/` (上一轮 landed) | 11 | 2026-09-01 12:13 | all 11 already landed ✓ |
| `02-simulation-file-experience/**` 主体文件 | 8 | last 2026-09-01 12:56 | re-grepped (无 3 条 new finding) |

## Findings — 3 NEW entries (round 2)

### Round 1 verdict
Round 1 (`2026-09-01-curator-report.md` + `auto-apply`) landed **5 P0 + 6 P1 = 11 entries** in 02-simulation-file-experience/. After re-scan of all 15 session summaries + relevant per-skill logs, found **3 entries still not covered** that meet durability threshold:

### P0 — New durable quirk (≥2 sources)

1. **[exp-012]** **`m.Program :=` 写入的方法 / 属性不持久化**:Plant Simulation 重启即丢,必须用户 GUI File → Save 才能持久化。bridge 没有暴露 "save model" action,所有 bridge-side 写操作都只在内存层。
   - **Sources (3 independent):**
     - **Source A:** `03-agent-memory/.../2026-08-28_session-summary_synctoolkit-foundation.md` §02-bridge-tool 第 4 条直接陈述 "通过 `m.Program :=` 写入的方法**不持久化**(PS 重启即丢)→ 必须让用户 export .psfm"
     - **Source B:** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-v2-wrap.md` §03-workflow-playbook 第 2 条 (DataTable create via SimTalk 不可行,"唯一可行重建方式 = Plant Simulation GUI"——隐含同根因:simtalk-side 改 in-memory,需 GUI 重启时 reload 才会发现)
     - **Source C:** `skills/local-simtalk-write-simtalk/log/2026-08-31_create-agv-claude-7-methods.md` 隐含证据(7 method 写完后没人提醒 user save → 09-01 重启 → 全空)
   - **Dimension:** 03-workflow-playbook (核心 workflow 硬规则 #9) + 02-bridge-tool (协议层 gap)
   - **Target file:** `02-simulation-file-experience/03-workflow-playbook/` 新 per-entry file (per CONTRIBUTING §6 强制 per-entry) + INDEX.md 表格新行 + skill-call-playbook.md §经验 Log 末尾追加 1 行 pointer
   - **Patch:** `agents/curator-reports/patches/skill-call-playbook.m-program-not-persisted.entry.md` (per-entry file 已直接落地)
   - **Status:** ⚡ landed (AUTO_APPLY) — `02-simulation-file-experience/03-workflow-playbook/2026-09-01 by @plant-simulation-experience-curator — m.Program 不持久化，PS 重启即丢必须 export .psfm.md` 创建;INDEX.md 新增 row;`skill-call-playbook.md` §经验 Log 末尾 pointer;frontmatter `last_updated: 2026-09-01` + scope 字符串更新
   - **Why P0:** 3 个独立 source 全部指向同一根因(in-memory vs on-disk layer)。**这是 bridge-side 写操作的"最大盲区"**——任何写操作报告"完成"如果不附 "请 GUI save" 提示,用户 100% 会丢数据。Cross-cutting 影响所有上层 skill 的 verify 流程。

### P1 — Single-source but clear (candidate; promote after re-validation)

2. **[exp-013]** **`simtalk_run` 单语句限制**:`for/next` / `if/then/end` block 全部 "Syntax error near 'print'";必须外层 shell 循环 + 多次 `simtalk_send.py send`。
   - **Sources (1 primary + 1 cross-mention):**
     - **Source A:** `skills/local-simtalk-execution/log/2026-08-28_agv-50008-discovery.md` Step 4 + §"What this run validated / learned" #1 直接 bisect 出 `simtalk_run` 单语句限制;`for i:=1 to ...: print ...; next` 全部 `Syntax error near 'print'`;workaround = `for i in 1..N` 改用 shell 多次 send
     - **Source B (cross-mention):** `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log` 现有 entries 多次提到"单语句"模式但没明确写"协议层硬限制"——本 entry 是它们的 super-set 显式声明
   - **Dimension:** 02-bridge-tool
   - **Target file:** `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` §经验 Log
   - **Patch:** `agents/curator-reports/patches/simtalkclaude-v1-and-v2.simtalk-run-single-statement.entry.md`
   - **Status:** ⚡ landed (AUTO_APPLY)
   - **Why P1:** 主 source 1 个,但 bisect-validated + workaround pattern 完整。**Protocol-level 硬限制**(不是 runtime failure),所以即便只有 1 个 session 验证也值得沉淀——任何 agent 第一次用 `simtalk_run` 写 `for` 循环都会撞墙。

3. **[exp-014]** **不同 Plant Simulation 实例的 SimtalkClaude bridge build 可能不同,导致 readlog buffer 行为不一致**:目标 50010 readlog 固定 715 字节窗口冻结,新 print 不出现;源 50007 readlog 工作正常。**Workaround**:目标端 state 读回必须走 simtalk_run log 字段,不能用 readlog。
   - **Sources (1 primary):**
     - **Source A:** `03-agent-memory/.../2026-08-31_session-summary_replicate-source-to-target.md` Finding 3 直接陈述 "Target 50010 readlog buffer is broken / frozen. Symptom: `print "X"` on target → simtalk_run returns `execute success`, but `readlog` returns a fixed 715-char slice ending mid-line. New prints do NOT appear in subsequent readlogs. Source 50007 has working readlog echo (prints visible in `log` field). Both bridges report same Plant Simulation version (2606.0002). The difference is the **SimtalkClaude bridge build** on each Plant Simulation instance."
   - **Dimension:** 02-bridge-tool
   - **Target file:** `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` §经验 Log
   - **Patch:** `agents/curator-reports/patches/simtalkclaude-v1-and-v2.readlog-frozen-different-bridge-build.entry.md`
   - **Status:** ⚡ landed (AUTO_APPLY)
   - **Why P1:** 单 session(但 finding 严重,state readback 完整失败)。**Cross-instance fragility 是 multi-bridge workflow 的核心 trap**——任何复制 / 迁移 / dual-server 场景都会撞。下次 multi-bridge 复现即升 P0。

### Quarantine (handoff to other agents)

1. **[quarantine-003]** `local-simtalk-get-class-inheritance/scripts/probe_inheritance.py` **不支持 `--no-infobox`** 参数,但 sibling `local-simtalk-read-library/scripts/probe_methods.py` 支持。**Script inconsistency**——任何脚本化批量 probe 必须先 patch 两者统一性。
   - **Sources:** `03-agent-memory/.../2026-08-27_modelassistants-study.md` §03-workflow-playbook 直接陈述
   - **Action:** Append "Script-flag inconsistency" 段到下次 optimizer handoff。Out of curator scope(tools layer not knowledge layer)。
   - **Decision:** ❌ no new entry in 02-simulation-file-experience/(single-source script-tooling finding,quarantine 是正确路径)。

## Recommended actions — 全部 executed this run

| ID | Action | Status |
|---|---|---|
| exp-012 | create per-entry file + INDEX row + playbook pointer + frontmatter bump | ✅ done ⚡ |
| exp-013 | append entry to simtalkclaude-v1-and-v2.md §经验 Log + patch file created | ✅ done ⚡ |
| exp-014 | append entry to simtalkclaude-v1-and-v2.md §经验 Log + patch file created | ✅ done ⚡ |
| quarantine-003 | handoff to skills-optimizer | 🕐 pending optimizer schedule |
| merge-001/002/003 (round 1) | no-op | ✅ still no-op |
| p3-001..005 (round 1) | drop | ✅ still dropped |

## Cross-references

- **前序报告** (同日 round 1):
  - `agents/curator-reports/2026-09-01-curator-report.md`(round 1 draft, 11 entries 列了但未 landing)
  - `agents/curator-reports/2026-09-01-curator-report-auto-apply.md`(round 1 landing, all 11 landed ⚡)
- **本轮报告** (round 2,本文):3 个 NEW entries landed
- **直接修改的 02-simulation-file-experience 文件** (本轮):
  - `02-simulation-file-experience/03-workflow-playbook/2026-09-01 by @plant-simulation-experience-curator — m.Program 不持久化，PS 重启即丢必须 export .psfm.md`(新建)
  - `02-simulation-file-experience/03-workflow-playbook/INDEX.md`(append 1 row + frontmatter bump)
  - `02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md`(append 1 pointer line + frontmatter bump scope 字符串)
  - `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md`(append 2 entries + frontmatter bump scope 字符串)
- **Patch 文件** (本轮,留盘供 verification 复核):
  - `agents/curator-reports/patches/skill-call-playbook.m-program-not-persisted.entry.md`
  - `agents/curator-reports/patches/simtalkclaude-v1-and-v2.simtalk-run-single-statement.entry.md`
  - `agents/curator-reports/patches/simtalkclaude-v1-and-v2.readlog-frozen-different-bridge-build.entry.md`
- **INDEX update**: see `agents/curator-reports/INDEX.md` 新增本轮行

## Operator self-review

- **Iron Rule ❶ (append-only):** 2 entries appended to `simtalkclaude-v1-and-v2.md §经验 Log` 末尾(port-can-be-rebound 之后);1 per-entry file created in `03-workflow-playbook/`. skill-call-playbook.md §经验 Log pointer 追加在已有 4 行 pointer 之后. **0 entries touched old content.**
- **Iron Rule ❷ (AUTO_APPLY protocol):** 本会话 prompt 显式 `AUTO_APPLY=1`,3 entries 全部 Edit 标记 ⚡ "direct-landed (AUTO_APPLY)"。
- **Iron Rule ❸ (durability ≥2 sources):** exp-012 有 3 个独立 sources(08-28 synctoolkit + 09-01 wrap + 08-31 AGV claude log)→ P0 ✓;exp-013 有 1 primary source + 1 cross-mention(已在 simtalkclaude-v1-and-v2.md 多次隐含)→ P1 borderline,标 single-source;exp-014 有 1 primary source(08-31 replication Finding 3)→ P1,标 single-source;exp-015(quarantine)走 optimizer 路径不沉淀。
- **Cross-file consistency:**
  - frontmatter bumps 在 3 个文件同步(`skill-call-playbook.md` scope 字符串加 "+持久化硬规则 #9";`simtalkclaude-v1-and-v2.md` scope 字符串加 "+单语句约束 + multi-bridge build 差异";`INDEX.md` last_updated 已 bump)
  - per-entry file 命名遵循 CONTRIBUTING §6.2 规则(空格 → %20, @ → %40, — → %E2%80%94)
- **Scope discipline:** 没碰 `skills/<x>/log/`(那是 expert);没改任何 SKILL.md / scripts(exp-013 / exp-014 是 protocol-level finding,留在经验层而非 skill 修复层);quarantine-003 路由给 optimizer 修 script。
- **Iron Rule ❿ (don't fake "landed"):** 所有 3 entries 都是真的 Edit + `last_updated` 已 bump;INDEX.md 标 ✅。
- **Cross-report dedup:**
  - round 1 已落 11 entries(5 P0 + 6 P1 + 3 merge + 5 drop)
  - round 2 新增 3 entries(1 P0 + 2 P1 + 1 quarantine)
  - **累计**:14 entries(6 P0 + 8 P1 + 3 merge + 5 drop + 3 quarantine)
- **Open questions for user:**
  1. exp-013 / exp-014 是否升 P0?→ 等下次 multi-bridge / multi-loop 复测一次即可。
  2. exp-012 的硬规则 #9 是否要加到 playbook §2.2 "写操作 5 步硬流程" 的 step 6(目前只有 step 1-5,需手动加 step 6 = "告诉 user File→Save")?——这是 **主体区** 改动,需要 user 单独批准(不在本轮 AUTO_APPLY 范围内)。
  3. quarantine-003(probe_inheritance 不支持 `--no-infobox`)何时让 optimizer 修?——等他自然 schedule。

---

*Generated by plant-simulation-experience-curator on 2026-09-01 under `AUTO_APPLY=1` (per user prompt authorization; round 2 of same-day session).*
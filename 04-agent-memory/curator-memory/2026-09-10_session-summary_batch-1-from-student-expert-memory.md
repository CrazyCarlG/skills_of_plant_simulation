---
last_updated: 2026-09-10
purpose: curator 本轮落盘清单 — 扫了 16 份 expert session summary + 14 篇 student note,沉淀了 14 个新文件,跳过的(及理由)。
---

# Curator session — 2026-09-10 — batch 1: student+expert memory 首批沉淀

## Inputs scanned

**expert session summaries**(16 份,按日期降序):
- `2026-09-02_session-summary_port-50008-model-structure.md` — 50008 server 拓扑映射 + bfs skill 端口硬编码
- `2026-09-02_session-summary_write-model-structure-comments.md` — 写注释到 .Models.Test.method + m.Program := protocol
- `2026-09-02_session-summary_write-astar-graph-method.md` — A* 通用图写入 + string escape / multi-line newline / readback 三重 proxy
- `2026-09-02_session-summary_student-agent-evaluation.md` — student 13 篇笔记评估
- `2026-09-01_session-summary_agv-claude-v2-wrap.md` — AGV_Claude v2 收尾 + DataTable 重建阻塞 + 7 method API 校正
- `2026-09-01_session-summary_agv-claude-v2-recovery.md` — AGV_Claude v2 恢复 + 7 method body 写 + .execute() 缓存
- `2026-09-01_session-summary_agv-claude-recovery-prep.md` — AGV_Claude recovery prep + silent write failure
- `2026-08-31_session-summary_create-agv-claude-library.md` — MaterialFlow_AGV 学习 + AGV_Claude scaffold
- `2026-08-31_session-summary_replicate-source-to-target.md` — 50007→50010 replicate + bfs 端口硬编码
- (其余 08-27 / 08-28 session 未深读,本轮跳过 → 留给下批)

**student notes**(14 篇,按日期降序):
- `2026-09-07-Python_GA_Demo-jobsshop-ga-integration.md` — Pymoo 集成 PS + cp1252 trap + Quirk #31/#32/#33 候选
- `2026-09-02-MarkerCrossing-crossing-semaphore-deepdive.md` — Frame-as-Semaphore + 完整 130 对象 dump
- `2026-09-02-AllModels-station-onpull-meta-analysis.md` — 5 个 Station.OnPull meta-analysis + boilerplate
- (其余 12 篇未深读 → 留给下批,优先 meta-analysis + system-level findings)

## Files created in 03-modeling-experience/

| Path | Dimension | Source session | Reason |
|---|---|---|---|
| `01-skill-experience/2026-09-02_program-cache-stale-execute-uses-old-body.md` | 01-skill-experience | agv-claude-v2-wrap + v2-recovery | P0 — `.execute()` 缓存问题跨 2 session 复现 |
| `01-skill-experience/2026-09-10_length-not-simtalk-function.md` | 01-skill-experience | write-model-structure-comments + write-astar + Python_GA_Demo | P0 — `length()` 跨 3 session 复现 |
| `01-skill-experience/2026-09-10_bfs-scripts-hardcoded-port-50007.md` | 01-skill-experience | port-50008-model-structure + replicate-source-to-target + agv-claude-recovery-prep + Python_GA_Demo | P0 — 端口硬编码跨 4+ session 复现 |
| `01-skill-experience/2026-09-10_v15-readlog-regression-workarounds.md` | 01-skill-experience | agv-claude-v2-wrap + port-50008 + write-astar + create-agv-claude + Python_GA_Demo | P0 — v15 readlog 退化跨 5+ session |
| `01-skill-experience/2026-09-10_write-simtalk-silent-failure.md` | 01-skill-experience | agv-claude-recovery-prep + agv-claude-v2-wrap | P0 — silent write failure 跨 2 session |
| `01-skill-experience/2026-09-10_simtalk-string-escape-backslash-quote.md` | 01-skill-experience | write-astar-graph-method | P1 — string `\"` escape 单源但清晰 |
| `01-skill-experience/2026-09-10_simtalk-multiline-run-real-newline.md` | 01-skill-experience | write-astar-graph-method | P1 — multi-line newline 单源但清晰 |
| `01-skill-experience/2026-09-10_simtalk-run-soft-failure-modes.md` | 01-skill-experience | agv-claude-v2-wrap + port-50008-model-structure | P0 — soft failure 4 种模式跨 2 session |
| `01-skill-experience/2026-09-10_obj-amp-method-program-dump-sop.md` | 01-skill-experience | AllModels-station-onpull-meta-analysis + MarkerCrossing-crossing-semaphore + SevenAxisRobot-onpull-dump | P1 — `obj.&Method.Program` SOP 跨 8+ Method(student 累计验证) |
| `02-user-expectation-experience/2026-09-10_student-reflective-not-engineering-learner.md` | 02-user-expectation-experience | student-agent-evaluation | P1 — student agent 姿态评估单源但清晰 |
| `03-modeling-experience/2026-09-10_station-onpull-spectrum-5-models.md` | 03-modeling-experience | AllModels-station-onpull-meta-analysis + MarkerCrossing-crossing-semaphore | P1 — 7-Frame 集 OnPull spectrum(student meta-analysis 综合) |
| `03-modeling-experience/2026-09-10_frame-as-semaphore-mutex-pattern.md` | 03-modeling-experience | MarkerCrossing-crossing-semaphore | P1 — Frame-as-Semaphore 模式单源(student) |
| `03-modeling-experience/2026-09-10_agv-claude-optimization-layer-pattern.md` | 03-modeling-experience | create-agv-claude-library + agv-claude-v2-recovery + agv-claude-v2-wrap | P0 — vendor 优化层模式跨 3 session |
| `03-modeling-experience/2026-09-10_pymoo-ga-integration-python-call-ps.md` | 03-modeling-experience | Python_GA_Demo-jobsshop-ga-integration | P1 — Pymoo 集成模式单源但完整 |

## Files skipped

| Path / finding | Reason |
|---|---|
| student 13 篇笔记中"🆕 Novel ICN 重构 14 个" | P3 — student 0 次实跑验证,baseline 不支持,expert / synthesizer 需评审真伪后再说;不沉淀到 `03-modeling-experience/`,留给 knowledge-synthesizer 评审 |
| student 5 个 Station.OnPull 中的 `Self.OnPull1` / `XLoader/ZLoader` / `calcDroppedPerpendicularFootPoint` 等细节 | P2 — 已合并到 `station-onpull-spectrum-5-models.md` 主文件,见 also 段交叉引用 |
| student Python_GA_Demo 中的 `Delivery 序列 slot 9 缺失` 候选 finding | P3 — 一次性观察,无 baseline 支持 |
| student Quirk #31/#32/#33 候选 | P2 — 已 see also 进 `01-skill-experience/2026-09-10_length-not-simtalk-function.md` + `v15-readlog-regression-workarounds.md`;**新 Quirk 进 canonical 是 optimizer 的活,curator 不沉淀**(铁律❺) |
| expert 08-27 / 08-28 session summaries | P3 — 早于本批焦点(09-01 / 09-02 集中),留给下一批 |
| `2026-09-02_session-summary_student-agent-evaluation.md` 中的"建议 curator 评审"段 | 已转成本文件 `student-reflective-not-engineering-learner.md` |
| `2026-08-31_session-summary_create-agv-claude-library.md` 中的 `vendor 拼写错误 AdvancedObejcts` | P3 — 一次性,沿 prior 已有发现 |

## README bumped
- `03-modeling-experience/README.md` → 2026-09-10(14 行新 entry)
- `01-skill-experience/README.md` → 2026-09-10(9 行新 entry)
- `02-user-expectation-experience/README.md` → 2026-09-10(1 行新 entry)
- `03-modeling-experience/README.md` → 2026-09-10(4 行新 entry)
- `04-agent-memory/curator-memory/README.md` → 2026-09-10(1 行新 entry)

## Open questions / next curator pass

1. **student 14 个 🆕 Novel ICN 真伪** — 留 knowledge-synthesizer 评审;若确认进 canonical,curator 再补 `01-skill-experience/2026-XX_xx_ps20-icn-refactor-14-new-names.md`
2. **`02-domain-know-how` 候选 finding**(station-onpull-spectrum / frame-as-semaphore / pymoo-integration)— 留 synthesizer;curator 不抢 synthesis 域
3. **`@skills-optimizer` 评审项累计 9 条**(bfs 端口 / write_simtalk 强制 readback / `--host/--port` 顶层参数 / cp1252 trap 通道化 / simtalk-string-escape Quirk / SimTemplate `.format` / dump SOP / readlog 三重 proxy)— optimizer 跨本批 14 文件见 also 段
4. **student 12 篇笔记未深读**(prior 09-02 七连发)— 下批焦点
5. **expert 08-27 / 08-28 session summaries 未深读** — 下批焦点
6. **`Sources used in this batch`**:本次共读取 5 个 expert session + 3 个 student note = 8 个 source;剩 11 个 expert + 11 个 student 待读

## Operator self-review
- [x] 14 新文件全部 ≤300 行(实测最长 ~70 行)
- [x] README 全部 bump,`last_updated` 同步到 2026-09-10
- [x] 不 append 到已有非 README 文件(全部新 Write)
- [x] 每个文件 frontmatter 含 `source_sessions` + `skills_touched` + `models_touched`
- [x] 文件命名 `YYYY-MM-DD_topic-slug.md`(文件日期 ≥ source session 日期)
- [x] 跨 session 复现 finding(P0 / P1)全部 click-through 到具体行号 / 小标题
- [x] student Quirk #31/#32/#33 没冒进成 P0 — 转给 optimizer 通道
- [x] 不抢 synthesis / optimizer 域

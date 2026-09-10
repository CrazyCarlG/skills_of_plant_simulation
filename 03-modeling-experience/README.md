---
last_updated: 2026-09-10
purpose: 03-modeling-experience 顶层索引。每个 finding/topic 一个新文件，不 append 到已有文件。每文件硬上限 ≤300 行。
---

# 03-modeling-experience — Index

**Curated by:** `plant-simulation-experience-curator`
**Source:** `04-agent-memory/plant-simulation-expert-memory/`
**Convention:** 见 [CONTRIBUTING.md](./CONTRIBUTING.md)

## Subdirs

| Subdir | 维度 | INDEX |
|---|---|---|
| `01-skill-experience/` | skill CLI / API / Quirk / 最佳实践 / `simtalk_*` 行为 | [README](./01-skill-experience/README.md) |
| `02-user-expectation-experience/` | 用户预期 / 偏好 / 沟通模式 / 教学节奏 / 提问习惯 | [README](./02-user-expectation-experience/README.md) |
| `03-modeling-experience/` | 具体模型（Factory51 / P4_CTU / AGV_Claude / SyncToolkit 等）建模 pattern / 架构 / 坑 | [README](./03-modeling-experience/README.md) |

## Files (all subdirs, newest at top)

| Date | File | Topic | Dimension |
|---|---|---|---|
| 2026-09-10 | `01-skill-experience/2026-09-02_program-cache-stale-execute-uses-old-body.md` | `.execute()` 不刷新 `.Program` 编译缓存 | 01-skill-experience |
| 2026-09-10 | `01-skill-experience/2026-09-10_length-not-simtalk-function.md` | `length()` 不是 SimTalk 函数 | 01-skill-experience |
| 2026-09-10 | `01-skill-experience/2026-09-10_bfs-scripts-hardcoded-port-50007.md` | bfs_*.py 硬编码 50007 多 server 打错目标 | 01-skill-experience |
| 2026-09-10 | `01-skill-experience/2026-09-10_v15-readlog-regression-workarounds.md` | v15+ readlog 退化三重 readback proxy | 01-skill-experience |
| 2026-09-10 | `01-skill-experience/2026-09-10_write-simtalk-silent-failure.md` | write_simtalk `[verify] OK` ≠ 落盘 silent failure | 01-skill-experience |
| 2026-09-10 | `01-skill-experience/2026-09-10_simtalk-string-escape-backslash-quote.md` | SimTalk string literal escape `\"` not `""` | 01-skill-experience |
| 2026-09-10 | `01-skill-experience/2026-09-10_simtalk-multiline-run-real-newline.md` | multi-line simtalk_run 必须真换行 | 01-skill-experience |
| 2026-09-10 | `01-skill-experience/2026-09-10_simtalk-run-soft-failure-modes.md` | simtalk_run 静默失败 4 种模式 | 01-skill-experience |
| 2026-09-10 | `01-skill-experience/2026-09-10_obj-amp-method-program-dump-sop.md` | `obj.&Method.Program` 跨 8+ Method dump SOP | 01-skill-experience |
| 2026-09-10 | `02-user-expectation-experience/2026-09-10_student-reflective-not-engineering-learner.md` | student = 反射型学习者 60-65% 理解度 | 02-user-expectation-experience |
| 2026-09-10 | `03-modeling-experience/2026-09-10_station-onpull-spectrum-5-models.md` | 7-Frame 集 Station.OnPull 三种 callback 模式 | 03-modeling-experience |
| 2026-09-10 | `03-modeling-experience/2026-09-10_frame-as-semaphore-mutex-pattern.md` | Frame-as-Semaphore AGV 互斥锁模式 | 03-modeling-experience |
| 2026-09-10 | `03-modeling-experience/2026-09-10_agv-claude-optimization-layer-pattern.md` | `.AGV_Claude` vendor 优化层模式 | 03-modeling-experience |
| 2026-09-10 | `03-modeling-experience/2026-09-10_pymoo-ga-integration-python-call-ps.md` | Python_GA_Demo Pymoo 集成 PS 范式 | 03-modeling-experience |
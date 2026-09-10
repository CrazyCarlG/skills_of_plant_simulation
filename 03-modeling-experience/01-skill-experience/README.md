---
last_updated: 2026-09-10
purpose: skill 行为经验沉淀。CLI 参数、API 行为、Quirk、最佳实践、simtalk_* 调用经验。每文件一个 finding/topic，≤300 行。
---

# 01-skill-experience — Index

**维度：** skill CLI / API / Quirk / 最佳实践 / `simtalk_*` 行为
**Curated by：** `plant-simulation-experience-curator`
**Convention：** 见 [`../CONTRIBUTING.md`](../CONTRIBUTING.md)

| Date | File | Topic | Skills touched |
|---|---|---|---|
| 2026-09-10 | `2026-09-02_program-cache-stale-execute-uses-old-body.md` | `.execute()` 不刷新 `.Program` 编译缓存 | local-simtalk-execution, local-simtalk-write-simtalk |
| 2026-09-10 | `2026-09-10_length-not-simtalk-function.md` | `length()` 不是 SimTalk 函数(跨 3 session 复现) | local-simtalk-execution |
| 2026-09-10 | `2026-09-10_bfs-scripts-hardcoded-port-50007.md` | bfs_*.py 硬编码 50007 多 server 打错目标 | local-simtalk-get-folder-tree, local-simtalk-write-simtalk |
| 2026-09-10 | `2026-09-10_v15-readlog-regression-workarounds.md` | v15+ readlog 退化三重 readback proxy | local-simtalk-execution, local-simtalk-write-simtalk |
| 2026-09-10 | `2026-09-10_write-simtalk-silent-failure.md` | write_simtalk `[verify] OK` ≠ 落盘 | local-simtalk-write-simtalk |
| 2026-09-10 | `2026-09-10_simtalk-string-escape-backslash-quote.md` | SimTalk string literal escape `\"` not `""` | local-simtalk-execution, local-simtalk-write-simtalk |
| 2026-09-10 | `2026-09-10_simtalk-multiline-run-real-newline.md` | multi-line simtalk_run 必须真换行 | local-simtalk-execution |
| 2026-09-10 | `2026-09-10_simtalk-run-soft-failure-modes.md` | simtalk_run 静默失败 4 种模式 | local-simtalk-execution |
| 2026-09-10 | `2026-09-10_obj-amp-method-program-dump-sop.md` | `obj.&Method.Program` 跨 8+ Method dump SOP | local-simtalk-execution |
---
last_updated: 2026-09-01
audience: 建模示例沉淀的写作者 + reader
---

# Contributing to `04-modeling-example/`

建模示例——具体实现 pattern、库扩展、探针 / SimTalk 实现期 Quirk 集合。

> 跨主题公共纪律见 [`../CONTRIBUTING.md`](../CONTRIBUTING.md)

## 当前内容

| 文件 | 主题 |
|---|---|
| `assembly-line-patterns.md` | 装配生产线 + WorkerChart + PalletOptimization + 2 个 Analyzer |
| `vendor-library-extension.md` | MaterialFlow_AGV 库 + AGV_Claude 7 方法 |
| `probe-pipeline-quirks.md` | 探针工具 4 个隐性 Quirk |
| `simtalk-implementation-quirks.md` | SimTalk 实现期 12 个坑（Quirk #1-#12） |

## 何时写新文件

- 新建模 pattern（**跨 ≥2 session 复现**且可复用）→ 新建 `<topic>-patterns.md`。
- 新 Quirk 系列 → 新建 `<series>-quirks.md`，沿用 Quirk #N 编号体系。
- 现有文件的 Quirk 集合有新增 → append 到对应文件 `## 经验 Log`。

## Quirk 编号约定

- Quirk 编号是 `references/quirks.md` 的**事实源**——本目录的 Quirk 集合是**镜像**，编号必须与 `skills/<x>/references/quirks.md` 一致。
- 新 Quirk 编号**先在 `references/quirks.md` 落地** → 再镜像到本目录。
- 编号漂移时 quarantine 给 `skills-optimizer` 处理。

## 不做的事

- ❌ 单次 Quirk 走新文件（应去 `03-modeling-experience/01-skill-experience/`）。
- ❌ 在本目录新造 Quirk 编号（必须经 `skills-optimizer` 落地）。
- ❌ 复制模型源码作为"示例"（引用模型路径 + 关键片段即可）。
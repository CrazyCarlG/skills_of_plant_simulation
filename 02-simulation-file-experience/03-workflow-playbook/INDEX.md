---
last_updated: 2026-09-01
contributors: [@z004bjuu, @plant-simulation-expert, @plant-simulation-experience-curator]
scope: 03-workflow-playbook 经验文件索引
---

# 03-workflow-playbook — 工作流索引

| 文件 | 何时读 |
|---|---|
| [`skill-call-playbook.md`](./skill-call-playbook.md) | 选择 skill、规划跨 skill 调用，或处理退出码、依赖关系和写操作流程 |

## 经验 Log per-entry files

> 2026-08-31 起：`skill-call-playbook.md §经验 Log` 不再保存 entry 正文；每条 entry 单独成文件，便于 git diff 单条追溯、tag-based 检索、per-entry supersede。
>
> 命名约定：`<YYYY-MM-DD> by @<author> — <entry title>.md`，全文中文 / 保留破折号 `—`，空格 → `%20`，at-sign → `%40`。

| Entry 文件 | Date | Author | tags |
|---|---|---|---|
| [2D 布局 pairwise bbox overlap check](./2026-08-28%20by%20%40plant-simulation-expert%20%E2%80%94%202D%20%E5%B8%83%E5%B1%80%E5%AE%8C%E6%88%90%E5%90%8E%E5%BF%85%E9%A1%BB%E5%81%9A%20pairwise%20bbox%20overlap%20check.md) | 2026-08-28 | @plant-simulation-expert | `layout`, `pairwise-check`, `2D-bbox`, `overlap`, `auto-clear`, `verifier` |
| [probe pipeline 在大模型上 3 个隐性 quirk](./2026-08-28%20by%20%40plant-simulation-expert%20%E2%80%94%20probe%20pipeline%20%E5%9C%A8%E5%A4%A7%E6%A8%A1%E5%9E%8B%E4%B8%8A%203%20%E4%B8%AA%E9%9A%90%E6%80%A7%20quirk.md) | 2026-08-28 | @plant-simulation-expert | `render_library`, `RENDER-1`, `bfs_one_level`, `readlog-v15-degradation`, `probe-pipeline`, `large-frame`, `multi-line-program` |
| [给非 Frame 对象加 method 不走 local-simtalk-create-method-object](./2026-08-31%20by%20%40plant-simulation-experience-curator%20%E2%80%94%20%E7%BB%99%E9%9D%9E%20Frame%20%E5%AF%B9%E8%B1%A1%E5%8A%A0%20method%20%E4%B8%8D%E8%B5%B0%20local-simtalk-create-method-object.md) | 2026-08-31 | @plant-simulation-experience-curator | `skill-selection`, `createAttr`, `method-typed-UDA`, `station`, `cross-skill-workflow`, `frame-vs-non-frame` |
| [write 之后必须 readback o.Program 确认落盘](./2026-09-01%20by%20%40plant-simulation-experience-curator%20%E2%80%94%20write%20%E4%B9%8B%E5%90%8E%E5%BF%85%E9%A1%BB%20readback%20o.Program%20%E7%A1%AE%E8%AE%A4%E8%90%BD%E7%9B%98.md) | 2026-09-01 | @plant-simulation-experience-curator | `write-verify`, `silent-failure`, `readback-Program`, `must-verify`, `write-simtalk-skill-bug`, `hard-rule-8`, `executeSilent-fresh-compile` |
| [m.Program 不持久化，PS 重启即丢必须 export .psfm](./2026-09-01%20by%20%40plant-simulation-experience-curator%20%E2%80%94%20m.Program%20%E4%B8%8D%E6%8C%81%E4%B9%85%E5%8C%96%EF%BC%8CPS%20%E9%87%8D%E5%90%AF%E5%8D%B3%E4%B8%A2%E5%BF%85%E9%A1%BB%20export%20.psfm.md) | 2026-09-01 | @plant-simulation-experience-curator | `persistence`, `m.Program-not-persistent`, `in-memory-vs-disk`, `psfm-export-required`, `bridge-no-save-action`, `restart-data-loss`, `workflow-mandatory-save` |

> **新增 entry 流程**（不破坏 append-only）：在 `03-workflow-playbook/` 下用本目录命名约定新建 `.md` 文件 + 在上表加一行 + 在 `skill-call-playbook.md §经验 Log` 末尾追加 1 行 pointer。
> 见 [`../../CONTRIBUTING.md`](../../CONTRIBUTING.md) §1.2 entry 字段格式 + §2 append-only 协议。
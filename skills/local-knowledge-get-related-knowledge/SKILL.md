---
name: local-knowledge-get-related-knowledge
description: 在本机 Plant Simulation 知识库（`01-plantsimulation-knowledge/01-plant-simulation-help/`）中按关键字/主题检索相关的官方帮助文档、对象参考、SimTalk 语言文档、分步指南与通信接口说明。触发场景：用户提出"Buffer 的属性是什么"、"SimTalk if 怎么用"、"怎么建模 Worker"、"Socket 通信怎么做"、"查找 Plant Simulation 中关于 X 的文档"等需要从离线知识库中**找出相关文档**的需求。本技能只做检索 + 返回路径与片段，**不修改任何文档**；如需执行 SimTalk 请用 `local-simtalk-execution`，如需启动 Plant Simulation 用 `local-window-com-start-plant-simulation`。
---

# local-knowledge-get-related-knowledge

Given a free-text query, find the most relevant documents in the local Plant
Simulation knowledge base and return their **relative paths + snippets** so the
caller can `Read` the top hits itself.

> Stateless, read-only, offline. No Plant Simulation process required.

## Quick Start

```bash
# Object lookup — top hit usually points to <Object>/attributes/attributes.md
python3 skills/local-knowledge-get-related-knowledge/scripts/find_related.py \
  --query "Buffer" --kind objects --top 5

# SimTalk syntax / function lookup
python3 skills/local-knowledge-get-related-knowledge/scripts/find_related.py \
  --query "if statement" --kind simtalk --top 5

# Modeling "how do I" question
python3 skills/local-knowledge-get-related-knowledge/scripts/find_related.py \
  --query "Worker resource" --kind step-by-step --top 3

# Mixed CJK + ASCII
python3 skills/local-knowledge-get-related-knowledge/scripts/find_related.py \
  --query "Socket 通信" --kind communication-interface --top 5

# JSON for downstream tooling
python3 skills/local-knowledge-get-related-knowledge/scripts/find_related.py \
  --query "Worker" --json --top 5
```

Each hit prints:

```
#<rank> score=<n>  [INDEX?] <rel-path>
       breadcrumb: <section / topic / sub-topic>
       breakdown:  filename=<n> path=<n> body=<n>
       snippet:    <first matching line, first token wrapped in <<…>>
```

`[INDEX]` marks a `README.md` summary file — de-weighted by default; pass
`--include-index` to promote them.

## 工作前提 / Prerequisites

- A local checkout of `01-plantsimulation-knowledge/` next to `skills/`
  (default resolution), **or** an explicit `--root <absolute-path>`.
- Python ≥ 3.7 (uses `sys.stdout.reconfigure` for Windows UTF-8 safety).
- **No** Plant Simulation process is required — the skill does not connect to
  PS. It only greps Markdown / `.txtx` files.

## 硬规则 / Hard Rules

> All "must / must not / will go wrong" rules are consolidated in
> **`references/lifelines.md`**. Key takeaways:

- **Read-only.** The skill never writes to `01-plantsimulation-knowledge/`.
- **No `log/`.** It's a stateless grep — no execution traces to keep.
- **Paths only.** The script returns `rel_path` + `snippet`; the caller does
  the actual `Read` (so Claude controls context cost).
- **Top-N caps context.** Default `--top 10`. Don't crank to 100 — the base is
  ~600 files.
- **Windows UTF-8.** The script reconfigures to UTF-8 at startup so snippets
  with `→` or CJK punctuation don't crash on `cp1252`.
- **Exit codes:** `0`=hits, `1`=bad args, `2`=root not found (or argparse
  error), `3`=no matches (broaden or drop `--kind`).

## 任务流程 / Workflow

1. **Parse the user's request into a query.**
   - Object lookups → use the object name as-is (`"WorkerPool"`, `"PickAndPlace Robot"`).
   - SimTalk questions → use the keyword(s) + `--kind simtalk`.
   - "How do I" modeling questions → use `--kind step-by-step`.
   - Mixed CN/EN is fine; the tokenizer handles CJK runs and Latin tokens.

2. **Run `find_related.py`** with the smallest `--kind` that fits. If unsure,
   use `--kind any --top 10` first, then narrow.

3. **Inspect the top hits.** Each row shows `score`, `breadcrumb`, and a
   `snippet` with the first matching token wrapped in `<<…>>`. The snippet is
   your cheapest signal that the file actually contains the topic.

4. **`Read` the most relevant file** with your own Read tool — that is where
   the actual content lives. Prefer `.md` over `.txtx` when both surface
   (the `.md` is the curated version).

5. **If the top hit is `[INDEX]`**, the breadcrumb/README is a summary.
   Either open it for navigation, or re-run with a more specific `--query` /
   `--kind` to find the concrete doc underneath.

6. **If exit code is `3` (no matches):** drop `--kind`, broaden keywords, or
   pass `--include-index` to surface README summaries.

## 关键文件 / Key Files

- `scripts/find_related.py` — the search engine (single file, no dependencies).
- `references/knowledge-layout.md` — section tree, file-naming conventions,
  per-section search hints.
- `references/lifelines.md` — hard rules (read-only, root resolution,
  scoring formula, exit codes, Windows encoding trap).

## 故障排查 / Troubleshooting

| 现象 | 可能原因 | 处理 |
|---|---|---|
| exit `2` + "knowledge base root not found" | 默认 root 解析失败 | 显式 `--root C:\…\01-plantsimulation-knowledge\01-plant-simulation-help` |
| exit `3` + "no matches" | 查询太窄 / `--kind` 选错 | 去掉 `--kind`，加 `--include-index`，或拆词再试 |
| top hit 是 README 但找不到具体 doc | 查询太宽，被 README 摘要吸走 | `--include-index` 看一眼 README 的内链，再换更窄的 `--query` |
| `→` / 中文片段打印崩溃 | Windows cp1252 stdout | 已由脚本自动 `reconfigure(encoding="utf-8")`；若是 pipe 把 `PYTHONIOENCODING=utf-8` 透传下去 |
| `.md` 和 `.txtx` 都出现且同等分 | 两者是同一内容的不同表达 | 优先 `Read` `.md`（curated），`.txtx` 是 PDF 原文提取 |
| 大文件没出现在 body 分数里 | 文件 > 1.5 MB 被跳过 body 扫描 | 这是设计；按 filename / path 分数仍会参与排名 |

## When NOT to use

- 用户想**执行** SimTalk → 用 `local-simtalk-execution`（需要 PS 进程）。
- 用户想**启动** Plant Simulation → 用 `local-window-com-start-plant-simulation`（Windows COM）。
- 用户想**修改**知识库文档 → 本技能不写盘，走 `01-plantsimulation-knowledge/scripts/pdf-to-knowledge/` 流水线。
- 用户的问题和 Plant Simulation 无关 → 不要拉这个 skill；用普通文档/网络搜索。

## 知识库路径 / Knowledge Paths

被本技能消费的：

- `01-plantsimulation-knowledge/01-plant-simulation-help/`（get 到 Markdown 与 txtx）
- `01-plantsimulation-knowledge/01-plant-simulation-help/README.md`（顶层索引）

不会触碰的相关路径：

- `01-plantsimulation-knowledge/scripts/pdf-to-knowledge/`（知识库重建流水线）
- `01-plantsimulation-knowledge/02-...` 其它子目录
- `02-domain-know-how/`、`03-modeling-experience/`、`04-agent-memory/`（agent 自身的 memory 与 know-how，**不在**离线 PS 帮助文档之列）
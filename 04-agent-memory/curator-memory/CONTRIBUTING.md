---
last_updated: 2026-09-01
audience: plant-simulation-experience-curator（写自己的 session log）
---

# Contributing to `04-agent-memory/curator-memory/`

本目录是 `plant-simulation-experience-curator` 自己的 **session log**——每次 curator session 落一份新文件，**不 append**。

---

## 🔴 铁律

1. **每文件硬上限 ≤300 行**——超限立即拆 `<topic>-part1.md` / `<topic>-part2.md`。
2. **每个 curator session = 一个新文件**——`YYYY-MM-DD_session-summary_<topic>.md`。
3. **末尾必留 "Open questions / next curator pass"**——给下次 curator pass 留 hot list。
4. **每次写入后 bump [`README.md`](./README.md) 索引**——append 一行 + bump `last_updated`。

---

## 文件命名

```
YYYY-MM-DD_session-summary_<topic>.md
```

---

## 文件 frontmatter（必填）

```markdown
---
last_updated: YYYY-MM-DD
purpose: curator 本轮落盘清单
---
```

---

## 文件正文模板（≤300 行）

```markdown
# Curator session — YYYY-MM-DD — <topic>

## Inputs scanned
- `04-agent-memory/.../YYYY-MM-DD_session-summary_<topic>.md`
- ...

## Files created in 03-modeling-experience/
| Path | Dimension | Source session | Reason |
|---|---|---|---|
| `01-skill-experience/foo.md` | 01-skill-experience | `2026-09-01_*` | P0 new quirk |
| ... | ... | ... | ... |

## Files skipped
| Path / finding | Reason |
|---|---|
| 已有 `bar.md` | merge candidate;新 finding cite via see also |
| session X 的 "Open questions" 段 | P3 一次性 |

## README bumped
- `03-modeling-experience/README.md` → YYYY-MM-DD
- `01-skill-experience/README.md` → YYYY-MM-DD

## Open questions / next curator pass
- ...

## Operator self-review（可选）
- 跑了 N 分钟;扫了 X 篇 session summary;沉淀了 Y 个新文件;跳过了 Z 条。
- 自我反思:evidence 是否都能 click-through?是否漏了 dimension 路由?
```

---

## 不做的事

- ❌ append 到已有 session log 正文（除末尾 `Operator self-review` 例外）。
- ❌ 在 session log 里写"我打算沉淀"——只写**已沉淀**。
- ❌ 跨 session 合并（每次独立 session = 独立文件）。
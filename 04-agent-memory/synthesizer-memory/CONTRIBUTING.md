---
last_updated: 2026-09-01
audience: plant-simulation-knowledge-synthesizer(写自己的 session log)
---

# Contributing to `04-agent-memory/synthesizer-memory/`

本目录是 `plant-simulation-knowledge-synthesizer` 自己的 **session log**——每次 synthesizer session 落一份新文件,**不 append**。

---

## 🔴 铁律

1. **每文件硬上限 ≤300 行**——超限立即拆 `<topic>-part1.md` / `<topic>-part2.md`。
2. **每个 synthesizer session = 一个新文件**——`YYYY-MM-DD_session-summary_<topic>.md`(必须带 `_session-summary_` 中缀,见顶层 CONTRIBUTING §公共纪律)。
3. **末尾必留 "Open questions / next synthesizer pass"**——给下次 synthesizer pass 留 hot list。
4. **每次写入后 bump [`README.md`](./README.md) 索引**——append 一行 + bump `last_updated`。

---

## 文件命名

```
YYYY-MM-DD_session-summary_<topic>.md
```

- `<date>` = `YYYY-MM-DD`(用 `date +%F` 取本地日)
- `<topic>` = 简短场景描述,kebab-case,不超过 5 个英文词(如 `fresh-domain-know-how-init`、`synthesize-quirks-from-08-27-09-01`)

---

## 文件 frontmatter(必填)

```markdown
---
last_updated: YYYY-MM-DD
scenario: <一句话:本轮合成任务在做什么>
operator: plant-simulation-knowledge-synthesizer
sources_scanned:
  - 03-modeling-experience/<子目录>/<count> per-entry
  - 04-agent-memory/skill-optimizer-memory/<count> reports
  - 04-agent-memory/plant-simulation-expert-memory/<count> session summaries
  - (optional) agents/curator-reports/<count> reports(目录当前为空,保留作为历史兼容)
---
```

---

## 文件正文模板(≤300 行)

```markdown
# Synthesis session — YYYY-MM-DD — <topic>

## Inputs scanned
| Source | Count | Date range |
|---|---|---|
| `03-modeling-experience/<子目录>/` | N | YYYY-MM-DD → YYYY-MM-DD |
| ... | | |

## Files created in 02-domain-know-how/
| Path | Topic | Source per-entries | Reason |
|---|---|---|---|
| `02-domain-know-how/<dir>/<topic>.md` | <一句话> | [per-entry 1, per-entry 2, curator report] | P0 必合成 |
| ... | | | |

## Files updated
| Path | Change |
|---|---|
| `02-domain-know-how/<dir>/README.md` | append 1 row + bump last_updated |
| `02-domain-know-how/README.md` | bump (if cross-subdir) |
| `02-domain-know-how/<dir>/<old>.md` | supersede marker on old(主体不改正文)|

## Skipped per-entry (and reason)
| Per-entry file | Reason |
|---|---|
| `<entry>.md` | P2 已覆盖 → 已在 cross-ref 标 "merged" |
| `<entry>.md` | P3 一次性 → 不合成 |
| `<entry>.md` | single-source ⚠️ tentative → 等下次复现 |

## Cross-references 主链路(全 5 类)
- Upstream append-only entries: ...
- Curator reports: ...
- Session summaries: ...
- Optimizer reports: ...
- KB docs: ...

## Open questions / next synthesizer pass
- ...

## Operator self-review
- **Iron Rule ❶ (no curator asset corruption)**: 本轮 ✅ 0 files in 03-modeling-experience/ 改动
- **Iron Rule ❷ (≥2 sources or tentative)**: N entries skipped for single-source;M entries synthesized with cross-ref
- **Iron Rule ❸ (cross-ref completeness)**: 每个新文件都有 Upstream + Curator + Session 三类 cross-ref
- **Scope discipline**: 没碰 expert / curator / optimizer / student 的 agent 文件;没改 SKILL.md / scripts
```

---

## 与 audit report (`agents/synthesis-reports/`) 的关系

| 路径 | 性质 | 读者 |
|---|---|---|
| `04-agent-memory/synthesizer-memory/YYYY-MM-DD_session-summary_<topic>.md`(本目录) | **agent 自己的记忆**——冷启动时回看 | `plant-simulation-knowledge-synthesizer` 自己 |
| `agents/synthesis-reports/<YYYY-MM-DD>-<scenario>.md` | **公开审计报告**——给 user / verification 复核 | user / verification / 其他 agent |

两者**不重复**:session summary 是 agent 视角的"我做了什么";audit report 是给外部看的"做了什么 + 证据链"。两者可由同一次 session 产生,但文件必须分开。

---

## 不做的事

- ❌ append 到已有 session log 正文(除末尾 `Operator self-review` 例外)。
- ❌ 在 session log 里写"我打算合成"——只写**已合成**。
- ❌ 跨 session 合并(每次独立 session = 独立文件)。
- ❌ 在本目录写实际合成的 `02-domain-know-how/` 文档(那是合成产物,不是 session log)。
- ❌ append/edit 到 `03-modeling-experience/` 任何文件(curator 唯一权利,铁律❶)。
</invoke>
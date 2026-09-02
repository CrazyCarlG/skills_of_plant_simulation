---
last_updated: 2026-09-02
purpose: skills-optimizer 报告 + 已落地改动 索引。agent 冷启动第一动作 = Read 此文件,不要批量 Read 同目录下报告。
---

# Optimizer Reports — INDEX

> 列含义:`Date | Skill | 🎯 精准命中 | ⚡ 性能 | ✂️ 瘦身 | 已落地 | Key takeaway`

| Date | Skill | 🎯 | ⚡ | ✂️ | 已落地 | Key takeaway |
|---|---|---|---|---|---|---|
| (暂无 entry——首个 entry 由下次优化实践后 append) | — | — | — | — | — | — |

## How to use

1. **First action at cold-start**: Read this file。**不要**批量 Read 同目录下报告。
2. **Grep 表格找匹配行**(skill / signal source / 已落地次数)。
3. **只打开行匹配的报告文件**(对应 `## Findings` 段),核对 `## 已落地改动` 段确认 optimizer 已自主修复的清单。
4. 找不到匹配行 → 新任务,无需加载历史。

## Conventions

- **Newest at top**。
- 每份报告对应一行;operator 在报告生成时**必填**(date / skill / 三类信号命中数 / 已落地数 / key takeaway)。
- 文件命名:`<skill-name>-YYYY-MM-DD.md`(per-skill 报告);`cross-cutting-YYYY-MM-DD.md`(横向报告,跨 skill 共性问题)。
- 候选补丁(若有)→ 同目录 `<skill-name>-YYYY-MM-DD-patches/` 子目录;**仅供复核**——已落地改动见报告 `## 已落地改动` 段;补丁文件本身不再被 Edit 触发。
- **不写** session summary 到 `04-agent-memory/plant-simulation-expert-memory/`(那是 expert 的活);optimizer 只**读**该目录作为佐证信号。

## 何时写新行

满足任一条件即必须 append 新行:

- 生成一份新的 `<skill-name>-YYYY-MM-DD.md` → 同步 append 表格最上方一行。
- 生成一份 `cross-cutting-YYYY-MM-DD.md` → 同步 append 表格最上方一行(列 skill 填 `cross-cutting`)。
- 长 session 拆分为多个报告文件 → 每份对应一行。

## 报告模板

报告内标准结构(详见 `agents/skills-optimizer.md` Step 3):

```
## Skill snapshot
## 🎯 精准命中发现(Goal 1)
## ⚡ 性能发现(Goal 2)
## ✂️ 瘦身候选(Goal 3)
## Findings
  ### P0 — Doc errors (blocking)
  ### P1 — Undocumented Quirks
  ### P1 — Missing best practice
  ### P2 — Copy / examples / dead links
  ### P3 — Informational
## 已落地改动 / Direct Landings(闸 1 报告留痕)
## Verdict
## Cross-references
```

`## 已落地改动` 段是 optimizer **可主动修改**权限的核心证据链——user 可在此段按 `文件路径 + 行号` 反向 revert 任一条改动。

---
last_updated: 2026-09-01
audience: 所有 agent（plant-simulation-expert / plant-simulation-experience-curator / student / 未来 agent）
---

# Contributing to `04-agent-memory/`

本目录是各 agent 的 **session log 仓库**——每个 agent 冷启动第一动作 = Read 自己子目录的 `README.md`，**不要批量 Read 同目录下 8+ 篇 session summary**。

---

## 子目录与对应 agent

| 子目录 | Writer | 索引 | 子规则 |
|---|---|---|---|
| `plant-simulation-expert-memory/` | `plant-simulation-expert` | [README](./plant-simulation-expert-memory/README.md) | README 内含 "Conventions" 段（暂未独立 CONTRIBUTING） |
| `curator-memory/` | `plant-simulation-experience-curator` | [README](./curator-memory/README.md) | [CONTRIBUTING](./curator-memory/CONTRIBUTING.md) |
| `student-memory/` | `student`（未来 agent） | [README](./student-memory/README.md) | 暂未独立 CONTRIBUTING |
| `synthesizer-memory/` | `plant-simulation-knowledge-synthesizer` | [README](./synthesizer-memory/README.md) | [CONTRIBUTING](./synthesizer-memory/CONTRIBUTING.md) |

> 各 agent 的具体 append / 命名 / 字段规则见各自子目录的 CONTRIBUTING.md（或 README 中的 Conventions 段）。
> **本目录只约定跨 agent 的公共纪律**。

---

## 🔴 跨 agent 铁律

1. **每个 agent session = 一份新文件**——禁止 append 到已有 session summary 正文（除末尾 `Operator self-review` 短段）。
2. **文件名统一格式**：`YYYY-MM-DD_session-summary_<topic>.md`（带 `_session-summary_` 中缀）。
3. **每文件硬上限 ≤300 行**——超限立即拆 `<topic>-part1.md` / `<topic>-part2.md`。
4. **每个 agent 子目录必有 `README.md` 索引**——cold-start 第一动作 = Read 它。
5. **每个 agent 子目录推荐有 `CONTRIBUTING.md`**——记录该 agent 特定的命名 / 字段 / 路由规则。
6. **跨 agent 写文件必须走对方子目录**——禁止在 `04-agent-memory/` 根目录直接落 session log。
7. **禁止跨 agent 互相覆盖**——一个 agent 不能 Edit 另一个 agent 写过的文件正文。

---

## 公共字段约定

### frontmatter（推荐）

```markdown
---
last_updated: YYYY-MM-DD
purpose: <一句话:这份 session summary 在干什么>
---
```

### README 索引表（每 agent 必维护）

```markdown
| Date | Topic | Skills / Models / Tags | Key takeaway |
|---|---|---|---|
```

- **Newest at top**。
- 每篇 session summary 对应一行；agent 在 session 结束时**必填**。

---

## Cold-start 协议

任何 agent 冷启动：

1. **Read 自己子目录的 `README.md`**（不要批量 Read session summary）。
2. **Grep 表格找匹配行**（topic / skill / dimension / model 列）。
3. **只打开行匹配的 session summary 文件**（再 Read 它的 `## Cross-references`）。
4. 找不到匹配行 → 新任务，无需加载历史。

---

## 不做的事

- ❌ append 到已有 session summary 正文（除末尾 `Operator self-review` 短段）。
- ❌ 在 `04-agent-memory/` 根目录直接落 session log。
- ❌ Edit 其他 agent 的 README（除非对方明确授权）。
- ❌ 跨 agent 互相覆盖文件。
- ❌ 单文件超 300 行硬塞。
- ❌ 把多个 session 合并到同一文件。
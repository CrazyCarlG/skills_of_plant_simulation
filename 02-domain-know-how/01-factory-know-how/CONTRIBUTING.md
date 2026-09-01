---
last_updated: 2026-09-01
audience: 工厂 / 仓库建模经验沉淀的写作者 + reader
---

# Contributing to `01-factory-know-how/`

工厂与仓库案例的知识沉淀——覆盖 Class Library / Models 二分法、AGV / WMS / RCS / CTU 等建模 pattern。

> 跨主题公共纪律见 [`../CONTRIBUTING.md`](../CONTRIBUTING.md)

## 当前内容

| 文件 | 主题 |
|---|---|
| `factory-modeling-architecture.md` | Class Library / Models 二分法 + 模型即类库包 + Hardware / Software 分层 |
| `warehouse-and-ctu-patterns.md` | RCS 控制中枢 / DataTable 状态机 / 三级执行器 / 触发点防重入 |

## 何时写新文件

- 用户给出新模型（Factory5X / WMS warehouse / CTU 类），且学到的 pattern **跨 ≥2 session 复现** → 新建 `<topic>.md`，在 `## 经验 Log` append。
- 单 session 单次发现 → 由 curator 路由到 `03-modeling-experience/03-modeling-experience/`（curator 流程新发现入口），**不**直接进本目录。

## 何时 append 到现有文件

- 新 finding 与 `factory-modeling-architecture.md` / `warehouse-and-ctu-patterns.md` 已有主体主题一致 → append 到对应文件的 `## 经验 Log`。

## 不做的事

- ❌ 把单次发现直接 append 到本目录（应去 `03-modeling-experience/`，由 curator 升级）。
- ❌ 复制 `01-plantsimulation-knowledge/` 已有内容。
- ❌ 改写主体章节来"容纳" 新 finding（append Log 即可）。
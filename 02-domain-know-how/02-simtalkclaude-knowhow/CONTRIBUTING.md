---
last_updated: 2026-09-01
audience: SimtalkClaude TCP 桥经验沉淀的写作者 + reader
---

# Contributing to `02-simtalkclaude-knowhow/`

SimtalkClaude TCP 桥协议、架构、版本差异、运维模式的知识沉淀。

> 跨主题公共纪律见 [`../CONTRIBUTING.md`](../CONTRIBUTING.md)

## 当前内容

| 文件 | 主题 |
|---|---|
| `bridge-architecture.md` | 桥架构 + 四层目录 + TCP 帧协议 + scratch buffer 模式 |
| `v1-vs-v2-comparison.md` | v1 vs v2 方法清单 + 协议差异 + 迁移风险 |
| `operational-patterns.md` | 11 类 Quirk 实测 + 12 项推荐 + 8 个反模式 |

## 何时写新文件

- 桥协议 / TCP 帧格式新增、v2 → v3 迁移等**结构性变化** → 新建 `<topic>.md`。
- 单次 Quirk 发现 → append 到 `operational-patterns.md ## 经验 Log`（已收 11 类 Quirk）。
- v1 vs v2 行为变更 → 更新 `v1-vs-v2-comparison.md` 主体 + bump `last_updated`。

## 不做的事

- ❌ 把单次桥接失败 append 到本目录以外的文件（应路由到 `operational-patterns.md §经验 Log`）。
- ❌ 复制 SimTalkClaude 源码注释到本目录（引用 `04-simtalkclaude-client/` 路径即可）。
- ❌ 改 v1/v2 章节文风（保持主体精修 + Log append 双轨）。
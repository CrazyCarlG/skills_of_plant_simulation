---
last_updated: 2026-09-01
audience: 通用建模知识沉淀的写作者 + reader
---

# Contributing to `03-modeling-know-how/`

通用建模知识——对象 / SimTalk / 软件调用三个子主题。每个子主题对应一个子目录。

> 跨主题公共纪律见 [`../CONTRIBUTING.md`](../CONTRIBUTING.md)

## 当前结构

```
03-modeling-know-how/
├── 01-objects/      ← 对象概念（Class/Instance/Frame/Folder）
├── 02-simtalk/      ← SimTalk 字面契约 + 易踩坑
└── 03-software/     ← skill 调用决策 + 写操作流程 + 贡献协议
```

> 各子目录的具体内容索引见各自 README.md；本 CONTRIBUTING 只覆盖**该父目录的路由规则**。

## 何时写到哪个子目录

| finding 类型 | 落点 |
|---|---|
| 对象概念 / 判定方法 / Class / Instance / Frame / Folder | `01-objects/` |
| SimTalk 语法、字面契约、Quirk、限制 | `02-simtalk/` |
| skill 编排、orchestration、写操作硬流程 | `03-software/` |

## 不做的事

- ❌ 把对象相关 finding 写到 `02-simtalk/`（route 反了就污染）。
- ❌ 把 skill 流程 finding 写到 `01-objects/`。
- ❌ 在 `03-modeling-know-how/` 根目录直接落 .md——必走 3 个子目录之一。
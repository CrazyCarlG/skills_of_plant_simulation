# `.ModelAssistants` — 经验沉淀索引

**Date:** 2026-08-27
**Source:** Siemens-shipped `.ModelAssistants` top-level basis bundle (Plant Simulation 自带)
**Method count:** 67 个 method（25 主框架 + 42 sub-Frame）
**Source-read:** 42 个未加密 method 完整源码已落盘至 `/tmp/modelassistants_sources/`

## 文档结构

| 文档 | 主题 |
|---|---|
| [README.md](README.md) | 本索引 |
| [architecture-overview.md](architecture-overview.md) | 整体架构：14 个 Frame 的职责分层 + lifecycle triple + 工具-数据二分 |
| [best-practices.md](best-practices.md) | **核心**：可直接复用的 12 条 SimTalk 编码模式 |
| [mscf-v2-protocol.md](mscf-v2-protocol.md) | ModelSyncCopy 私有协议 MSCF v2 完整规范（FS/RS + 9 类 record + OnCollision 三策略） |

## 一句话总结

`.ModelAssistants` 是 Siemens 自带的 **「模型医生 + 模型搬运工」工具箱**——它示范了
**Frame 工具 + 内部 lifecycle hook + 类模板分类** 三件套的标准结构，并埋了一条与
SimtalkClaude 平行但更完整的 TCP 镜像协议（MSCF v2）。它的 SimTalk 风格是 **「防御式
参数校验 + 显式 type switch + 单一职责 method + 工具-数据二分层」**。

## 与 SimtalkClaude 的关系

| 维度 | SimtalkClaude | `.ModelAssistants` |
|---|---|---|
| 来源 | 用户导入 | Siemens 原厂 |
| 定位 | 远程 TCP 驱动桥 | 本地建模助手工具箱 |
| 协议 | JSON-line + 鉴权 | 内部 MSCF v2（私有） |
| 入口 | `.SimtalkClaude.main` 启动 | `.ModelAssistants.Internal.autoexec` 自动启动 |
| 适用 agent | 容器↔host 远程执行 | 暂时不可直接驱动（无 agent 接口） |

**结论**：两者**互补不重叠**——SimtalkClaude 是 agent 工具；`.ModelAssistants` 是
建模师工具。Agent 只能间接利用前者；后者的源码是**风格参考**而非执行目标。
---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: SimtalkClaude TCP 桥的架构、版本对比、运营模式(综合 v1+v2)
---

# 02-simtalkclaude-knowhow — SimtalkClaude TCP 桥知识

本目录整合 **SimtalkClaude 远程驱动桥** 的所有文档,从架构到协议到运营实践。

## 文件索引

| 文件 | 内容主题 |
|---|---|
| [`bridge-architecture.md`](./bridge-architecture.md) | **架构与协议**:桥是什么、四层目录(connection/main/src/Objects)、TCP 帧格式、动作路由、鉴权协议、scratch buffer 模式 |
| [`v1-vs-v2-comparison.md`](./v1-vs-v2-comparison.md) | **版本对比**:v1 与 v2 的方法清单差异、协议差异、迁移风险 |
| [`operational-patterns.md`](./operational-patterns.md) | **运营模式**:11 类 Quirk 实测教训 + 12 项推荐做法 + 8 个反模式 + SimTalk 字面量速查 |

## 阅读顺序建议

1. **先读 [`bridge-architecture.md`](./bridge-architecture.md)** —— 5 分钟了解"桥是什么、做什么、目录结构、协议层"
2. **如果用 v2 额外读 [`v1-vs-v2-comparison.md`](./v1-vs-v2-comparison.md)** —— 鉴权握手、双协议分帧、连接状态机、防御性校验
3. **最后读 [`operational-patterns.md`](./operational-patterns.md)** —— 实测踩坑与推荐做法,避免重复试错

## 当前仓库实际使用版本

- **当前默认:v1**(`host.docker.internal:50007`)
- v2 用于 Factory51 等高价值模型接入场景
- 端口可由用户在 Plant Simulation 端 `.SimtalkClaude2` Frame 的 `mySocket.create("<port>")` 变量中**手动 rebind**(实际生产已观察到 50007 → 50009 切换)

## 重构元数据

- 重构日期:2026-09-01
- 重构来源:`02-simulation-file-experience/02-bridge-tool/`(7 文件) + `02-simulation-file-experience/simtalkclaude-best-practices.md`(1 文件)
- 重构策略:从 8 篇源文档提炼模式,重新撰写为 3 篇主题导向文档(架构 + 版本对比 + 运营模式)
</content>
</invoke>
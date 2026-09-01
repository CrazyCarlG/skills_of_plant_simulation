---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: agent 调用 Plant Simulation 工具时的工作流、坑、决策矩阵 + 贡献协议
---

# 03-modeling-know-how/03-software — 软件工作流

本目录整合 **agent 调用 9 个 `local-simtalk-*` skill 时的工作流、决策、坑 + 贡献协议**。

## 文件索引

| 文件 | 内容主题 |
|---|---|
| [`skill-orchestration-guide.md`](./skill-orchestration-guide.md) | **Skill 编排指南**:9 skill 依赖图 + 决策矩阵 + 写操作 5 步硬流程 + Top 10 高频坑 + 工作流模板 |
| [`contribution-protocol.md`](./contribution-protocol.md) | **贡献协议**:append-only 时间线协议 + entry 字段格式 + Supersede 模式 + per-entry file 强制约定 |

## 阅读顺序建议

1. **先读 [`skill-orchestration-guide.md`](./skill-orchestration-guide.md) §一(9 skill 依赖图)+ §三(决策矩阵)** —— 选择 skill 的依据
2. **必读 [`skill-orchestration-guide.md`](./skill-orchestration-guide.md) §2.2(写操作 5 步硬流程)+ §四(Top 10 高频坑)** —— 写操作硬纪律
3. **遇到具体坑时,翻 [`skill-orchestration-guide.md`](./skill-orchestration-guide.md) §五(工作流模板)** —— 标准操作流
4. **要沉淀新经验时,先读 [`contribution-protocol.md`](./contribution-protocol.md)** —— append-only 协议

## 核心硬规则速查

| 规则 | 简述 |
|---|---|
| **硬规则 #1** | Pre-flight:SimTalkClaude 服务未启动不可用 TCP 技能 |
| **硬规则 #2** | 每个 GUI 动作前 infoBox 三要素(技能名 + 目标路径 + 动作) |
| **硬规则 #3** | 不要用 prompt / 单参 infoBox / messageBox 模态陷阱 |
| **硬规则 #4** | 不要在 `.SimtalkClaude.*` 路径下写任何东西 |
| **硬规则 #5** | 不要用 `"\n"` 构造多行字符串——用 `chr(10)` |
| **硬规则 #6** | 不要把 type 字段填成白名单以外的值 |
| **硬规则 #7** | 不要跳过 usage log |
| **硬规则 #8** | 不要在没有读到目标 program 原文之前对其做任何写操作 |
| **硬规则 #9** | 不要对写操作假装成功——必须 readback + 必要时 obj.execute 验证 |
| **硬规则 #10** | 不要漏写 session summary |

## 重构元数据

- 重构日期:2026-09-01
- 重构来源:`02-simulation-file-experience/03-workflow-playbook/`(9 文件) + `02-simulation-file-experience/CONTRIBUTING.md`(1 文件)
- 重构策略:从 10 篇源文档提炼模式,重新撰写为 2 篇主题导向文档(skill 编排 + 贡献协议)
</content>
</invoke>
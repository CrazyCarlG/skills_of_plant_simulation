# 技能编写规范 / Skill Authoring Guide

本仓库的技能遵循 Claude Code 的 Skill 格式：每个技能是一个目录，入口为 `SKILL.md`。

## 目录约定 / Directory Convention

### 最小骨架 / Minimum skeleton

```
skills/<skill-name>/
├── SKILL.md              # 入口：name + description + 主流程（保持精简）
└── references/           # 按需加载的详细提示词/模板（渐进式披露）
```

### 可选子目录 / Optional subdirectories

| 子目录 Subdir | 用途 Purpose | 是否推荐 Recommended |
|---|---|---|
| `references/` | 按需加载的提示词、模板、quirks 速查 | **强制 Required** |
| `examples/` | 完整工作流示例（≥1 个完整用例） | **推荐 Recommended** |
| `scripts/` | 可执行辅助脚本（Python / bash） | **推荐 Recommended** |
| `data/` | 静态测试 fixture、参考模型 JSON | 可选 Optional |
| `evals/` | 评分 / 回归测试用例 | 可选 Optional |
| `log/` | per-session 运行日志（**不入库**） | 运行时产物 |
| `usage_log/` | per-call 调用统计（**不入库**） | 运行时产物 |
| `code_log/` | per-call 代码片段存档（**不入库**） | 运行时产物 |

### 命名一致性 / Naming consistency

- 用 **`examples/`**（复数），不用 `example/`。
- 日志三类选一个最贴近语义的，**避免在同一个 skill 里同时存在 `log/`、`usage_log/`、`code_log/`**。一般约定：
  - `log/` — 高层会话小结 / 经验沉淀（人读）
  - `usage_log/` — 每次调用的元数据（机器读）
  - `code_log/` — 每次调用的原始输入/输出（机器读、可能很大）

### 反例 / Anti-patterns

- 测试 fixture / path list / 临时输出文件不要放在 skill 根目录 —— 归到 `data/` 或 `examples/`。
- 不要让 `references/` 超过 200 行单文件 —— 拆细，按子主题分文件。
- `SKILL.md` 不要直接列 hard-coded 完整路径（绝对路径尤其禁止），用 `01-plantsimulation-knowledge/...` 这种仓库根相对形式。

## SKILL.md 格式 / SKILL.md Format

```markdown
---
name: <kebab-case 技能名>
description: <何时使用该技能，第三人称，说明触发场景，不含 emoji>
---

# <技能标题>

<body：角色设定、知识库路径、任务流程>
```

要点 / Key points：

- `name` 用 kebab-case，与目录名一致，全局唯一。
- `description` 是触发依据，必须写清「when to use」，避免模糊。
- 主文件保持精简，详细步骤放到 `references/` 下，由主文件用相对路径指引。

## 命名规范 / Naming

| 技能 Skill | 目录/name Directory/name |
|---|---|
| 模型逆向解析 | `psfm-reverse-engineering` |
| SimTalk 编程 | `simtalk-programming` |
| 对象速查 | `ps-object-reference` |
| 建模指南 | `ps-modeling-guide` |

## 知识库路径约定（重要）/ Knowledge Path Convention

- 一律以**仓库根**为基准书写，不要硬编码 `/root/...` 等绝对路径。
- 对象参考 Objects：`01-plantsimulation-knowledge/01-plant-simulation-help/objects/`
- SimTalk：`01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/`
- 分步指南 Step-by-step：`01-plantsimulation-knowledge/01-plant-simulation-help/step-by-step/`
- 入门 Getting started：`01-plantsimulation-knowledge/01-plant-simulation-help/getting-to-know-plant-simulation/`

## 术语规范 / Terminology

- 对象名、方法名、属性名一律使用 Plant Simulation 官方英文名称。
- 解释性文字使用中文。
- 无法从模型/文档中确认的信息写「未体现」，禁止臆造。

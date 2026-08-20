# 技能编写规范 / Skill Authoring Guide

本仓库的技能遵循 Claude Code 的 Skill 格式：每个技能是一个目录，入口为 `SKILL.md`。

## 目录约定 / Directory Convention

```
skills/<skill-name>/
├── SKILL.md              # 入口：name + description + 主流程（保持精简）
└── references/           # 按需加载的详细提示词/模板（渐进式披露）
```

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

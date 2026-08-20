# skills_of_plant_simulation

Plant Simulation（Siemens Tecnomatix）的 **Claude Code / OpenClaude 技能集**。以技能（Skill）形式封装仿真建模、模型逆向解析、SimTalk 编程、对象查询等能力，并复用 [knowledge_of_plant_simulation](https://github.com/CrazyCarlG/knowledge_of_plant_simulation) 知识库作为权威数据源。

> A collection of **Claude Code / OpenClaude skills** for Siemens Tecnomatix Plant Simulation.

## 目录结构 / Directory Structure

```
skills_of_plant_simulation/
├── 01-plantsimulation-knowledge/   # [子模块] 知识库（帮助文档 Markdown + PDF→MD 工具链）
├── skills/                         # 技能集（每个技能一个目录）
│   ├── psfm-reverse-engineering/   # PSFM 模型逆向解析
│   ├── simtalk-programming/        # SimTalk 编程助手
│   ├── ps-object-reference/        # 对象/API 速查
│   └── ps-modeling-guide/          # 建模实操指南
├── docs/
│   └── skill-authoring.md          # 技能编写规范
└── scripts/
    └── link-skills.sh              # 将技能软链到 ~/.claude/skills/
```

## 技能清单 / Skills

| 技能 Skill | 用途 Description |
|---|---|
| `psfm-reverse-engineering` | 解析 `.psfm`/`.spp` 模型，提取结构、类层次、建模思路、SimTalk 代码，生成解析报告 |
| `simtalk-programming` | 编写、修改、调试 SimTalk 代码 |
| `ps-object-reference` | 查询对象属性、方法、用法 |
| `ps-modeling-guide` | 从零搭建仿真模型的实操指南 |

## 安装与使用 / Install & Use

```bash
# 克隆（含子模块）/ Clone with submodule
git clone --recurse-submodules <repo-url>
# 已有仓库补拉子模块 / For an existing clone, fetch the submodule
git submodule update --init --recursive

# 把技能软链到用户技能目录（可选）/ Optionally symlink skills into the user skills dir
bash scripts/link-skills.sh
```

## 路径约定 / Path Convention

所有技能通过「以仓库根为基准」的相对路径引用知识库，例如 `01-plantsimulation-knowledge/01-plant-simulation-help/objects/`。详见 [docs/skill-authoring.md](docs/skill-authoring.md)。

> All skills reference the knowledge base via repo-root-relative paths. See [docs/skill-authoring.md](docs/skill-authoring.md).

## 许可证与版权 / License & Copyright

- 技能与脚本：**GPL-3.0**，见 [LICENSE](LICENSE)。**English:** Skills & scripts: **GPL-3.0**, see [LICENSE](LICENSE).
- 知识库内容：来源于 Siemens《Plant Simulation Help》（© 2026 Siemens，Unpublished work），仅用于学习与知识管理，版权归 Siemens 所有。
  **English:** Knowledge content is sourced from Siemens *Plant Simulation Help* (© 2026 Siemens, Unpublished work), for learning and knowledge management only; all rights belong to Siemens.

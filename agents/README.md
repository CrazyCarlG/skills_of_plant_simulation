# Agents / Agent 集合

本目录存放**面向 Plant Simulation 的专用 agent**，由 Claude Code / OpenClaude 通过 `Agent` 工具以 `subagent_type` 形式调用。

## 当前 agent / Current Agents

| Agent `subagent_type` | 角色 | 用途 | 文件 |
|---|---|---|---|
| `plant-simulation-expert` | Discovery + 执行 | Plant Simulation / SimTalk / 模型操作领域的专家 agent——理解用户请求、挑选并调用 `skills/` 下的合适技能、对接知识库（`01-plantsimulation-knowledge/`）与经验沉淀（`02-simulation-file-experience/`）、并在每次技能调用后把全过程记入 `skills/<skill-name>/usage_log/` | [`plant-simulation-expert.md`](plant-simulation-expert.md) |
| `plant-simulation-experience-curator` | 经验策展 | 把 expert 的 session summary 与 `skills/<name>/log/` 累积日志做去重 / 分类 / 索引治理，决定哪些 finding 应该永久沉淀到 `02-simulation-file-experience/` 的 append-only 经验区。报告落 `agents/curator-reports/`，**不改 `02-simulation-file-experience/` 主体**，所有沉淀建议经用户或 `verification` 复核 | [`plant-simulation-experience-curator.md`](plant-simulation-experience-curator.md) |
| `skills-optimizer` | 技能质量差距 | 扫描 `skills/<name>/log/` 失败模式，与 `SKILL.md` / `references/` 做差距分析，产出 `agents/optimizer-reports/<skill>-YYYY-MM-DD.md` 报告 + 候选补丁 | [`skills-optimizer.md`](skills-optimizer.md) |

> 三个 agent **互不重叠**：expert = 跑模型 / 写日志；curator = 沉淀哪些日志；optimizer = 修技能文档。三者通过 report 路径通信，**互不直接 edit 对方的文件**。

## 调用方式 / How to Invoke

在主对话里通过 `Agent` 工具调用：

```text
Agent(
  description: "<任务简述>",
  prompt: "<具体任务>",
  subagent_type: "plant-simulation-expert"        # 或 "plant-simulation-experience-curator" / "skills-optimizer"
)
```

- `plant-simulation-expert` 会在 `skills/` 下挑技能、把执行结果回报主对话，同时把 usage log 写到对应技能的 `log/` 子目录。
- `plant-simulation-experience-curator` 适合"沉淀近期经验"/"整理 02-simulation-file-experience"/"评审 supersede 候选"类请求，产出 `agents/curator-reports/INDEX.md` + 单次报告。
- `skills-optimizer` 适合"优化下技能"/"看看 log 有什么要修的"类请求，产出 `agents/optimizer-reports/<skill>-YYYY-MM-DD.md`。

## 命名约定 / Naming Convention

- 文件名使用 kebab-case，与 frontmatter 的 `name` 字段一致。
- frontmatter 必填字段：`name`、`description`、`tools`。
- 正文用中文写"角色设定 + 工作流 + 硬规则"，与 `skills/<name>/SKILL.md` 的格式保持一致。

## 与 Skills 的关系 / Relationship to Skills

| 维度 | Skill | Agent（本目录） |
|---|---|---|
| 触发方式 | `Skill` 工具 + skill 名 | `Agent` 工具 + `subagent_type` |
| 颗粒度 | 一个具体的操作能力（如"加方法注释"、"读属性"） | 一组能力的编排 + 经验沉淀 |
| 上下文 | 通常作为主对话的旁路工具调用 | 拥有自己的子上下文，能跑多步任务 |
| 留痕 | skill 内部可在 `log/` 写产物 | 在 `skills/<x>/log/` 写调用日志 |

简单说：**Skills 是手，Agent 是大脑**。本目录里的 `plant-simulation-expert` 是大脑，负责挑手并记录每次挑手的理由与结果。

## 安装 / Install

仓库克隆到新机器后，默认不会自动出现在 OpenClaude / Claude Code 的 agent 列表中——需要运行仓库自带的安装脚本把 `agents/*.md` 软链到用户级目录：

```bash
# 一键（推荐）：同时安装 skills + agents
bash scripts/install.sh

# 只装 agents
bash scripts/install.sh --agents-only

# 手动：仅 agents
bash scripts/link-agents.sh

# 卸载
bash scripts/install.sh --unlink
bash scripts/link-agents.sh --unlink
```

默认目标目录：

- `$OPENCLAUDE_AGENTS_DIR`（环境变量覆盖，若设置则用它）
- `~/.openclaude/agents/`（OpenClaude 默认）
- `~/.claude/agents/`（Claude Code 默认，找不到 `~/.openclaude` 时退到这里）

链接器**只创建符号链接**，不复制文件——仓库内的修改会立即生效。详见仓库根 `README.md` 的「安装与使用」节。
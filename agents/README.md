# Agents / Agent 集合

本目录存放**面向 Plant Simulation 的专用 agent**，由 Claude Code / OpenClaude 通过 `Agent` 工具以 `subagent_type` 形式调用。

---

## 一、5 个 Agent 总览

| # | Agent `subagent_type` | 角色 | 一句话职责 | 文件 |
|---|---|---|---|---|
| 1 | `plant-simulation-expert` | **大脑** — Discovery + 执行 | 接收用户任务、挑选 9 skill(per-skill log 由各 `SKILL.md` 要求)、session 收尾写 summary | [`plant-simulation-expert.md`](plant-simulation-expert.md) |
| 2 | `plant-simulation-experience-curator` | **策展人** — append-only 沉淀 | 把 expert session summary 落成 per-entry file + append-only archive | [`plant-simulation-curator.md`](plant-simulation-curator.md) |
| 3 | `skills-optimizer` | **技能优化师** — 独立优化 skill(精准命中 + 性能 + 瘦身) | 扫 `skills/<x>/log/` → ①**精准命中**(防止 expert 选错 skill)+ ②**性能提升**(silent fail / timeout)+ ③**瘦身**(精简 SKILL.md);产出到 `agents/optimizer-reports/`,**不调 SimTalkClaude 服务**、**不依赖其他 agent 产出**,可独立调度 | [`skills-optimizer.md`](skills-optimizer.md) |
| 4 | `plant-simulation-student` | **学生** — 严格只读 5 维镜像 | 学习当前打开的模型,写 5 维镜像笔记,不动任何东西(**per-skill log 由各 `SKILL.md` 要求**) | [`plant-simulation-student.md`](plant-simulation-student.md) |
| 5 | `plant-simulation-knowledge-synthesizer` | **合成者** — 主题合成长文档 | 把 curator archive 合成为 `02-domain-know-how/` 的 active 主题文档 | [`plant-simulation-knowledge-synthesizer.md`](plant-simulation-knowledge-synthesizer.md) |

---

## 二、Agent 之间的关系图

### 2.1 整体协作流(端到端视角)

```
                            ┌─────────────────────────┐
                            │      用户主对话           │
                            │  (OpenClaude / Claude Code) │
                            └────────────┬────────────┘
                                         │ Agent 工具 + subagent_type
                                         ▼
        ┌──────────────────────────────────────────────────────────┐
        │                                                          │
   写任务要执行                  纯读分析                           知识重构
        │                                                          │
        ▼                                                          ▼
┌────────────────┐                                         ┌────────────────────┐
│ plant-simulation-│                                │ plant-simulation- │
│ expert        │                                │ student           │
│ (大脑)        │                                │ (学生,只读)       │
└───────┬────────┘                                └────────┬───────────┘
        │                                                  │
        │ ① 执行任务                                         │ ② 5 维镜像笔记
        │  skills/<x>/log/                                   │  03-agent-memory/
        │  03-agent-memory/expert-memory/                    │  student-memory/
        │  (session summary)                                 │
        ▼                                                  │
┌────────────────────────┐                                │
│ plant-simulation-     │ ③ 读 expert session summary    │
│ experience-curator    │                                │
│ (策展人)             │                                │
└─────────┬──────────────┘                                │
          │                                                │
          │ ④ append-only 沉淀                              │
          │  02-simulation-file-experience/.../logs/*.md  │
          │  (per-entry file,append-only)                   │
          │  agents/curator-reports/                        │
          ▼                                                │
┌─────────────────────────────────────┐                  │
│ plant-simulation-knowledge-synthesizer│ ⑤ 主题合成       │
│ (合成者)                          │                  │
└─────────┬───────────────────────────┘                  │
          │                                                │
          │ ⑥ 主题合成长文档                                │
          │  02-domain-know-how/<子目录>/<topic>.md         │
          │  agents/synthesis-reports/                      │
          ▼                                                │
┌─────────────────────┐                                  │
│ skills-optimizer   │ ← ⑦ 独立路径:                 │
│ (技能优化师)       │   扫 skills/<x>/log/ 找        │
│                   │   精准命中/性能/瘦身信号        │
└──────┬──────────────┘                                  │
       │                                                 │
       │ ⑧ 优化报告 + 候选 patches                       │
       │  agents/optimizer-reports/                       │
       │  (🎯精准命中 + ⚡性能 + ✂️瘦身)               │
       ▼                                                 │
┌─────────────────────────┐                            │
│      用户拍板         │ ← ⑨ 最终决策                │
└─────────────────────────┘                            │
                                                         │
        (以上是 memory 双向反馈路径)─────────────────────┘
```

### 2.2 数据流方向(谁读谁写)

```
┌────────────────────────────────────────────────────────────────────┐
│                            数据流方向                                │
└────────────────────────────────────────────────────────────────────┘

expert  ───────写─────→ skills/<x>/log/                       (per-skill 调用日志)
        └────写──────→ 03-agent-memory/plant-simulation-expert-memory/ (session summary)
                │
                ↓ 读
       curator  ──写─→ 02-simulation-file-experience/{01,02,03,04}-*/logs/  (per-entry file,append-only)
              ──写─→ agents/curator-reports/                    (审计报告)
              ──写─→ 04-agent-memory/curator-memory/              (curator 自己的 session log)
                │
                ↓ 读
       synthesizer ──写─→ 02-domain-know-how/<5 维子目录>/<topic>.md (主题合成长文档)
                   ──写─→ agents/synthesis-reports/                (合成审计报告)
                   ──写─→ 04-agent-memory/synthesizer-memory/         (synthesizer 自己的 session log)

student  ───────写─────→ 03-agent-memory/student-memory/             (5 维镜像笔记)

optimizer ────独立路径───→ skills/<x>/log/    (主输入,与 expert/curator 解耦)
             ──写──→ agents/optimizer-reports/   (优化建议 + 候选 patches)
             🎯精准命中 + ⚡性能 + ✂️瘦身
             ↓ user 批准后才可写
         skills/<x>/SKILL.md / scripts/ (经 user 复核)
```

---

## 三、5 个 Agent 的边界规则

### 3.1 边界核心:互不重叠 + 各自独占写入路径

| Agent | 写入路径(独占) | 不写入 |
|---|---|---|
| **expert** | `03-agent-memory/expert-memory/` | 其他 4 agent 的任何路径(`SKILL.md` 自管 per-skill log) |
| **curator** | `03-modeling-experience/<dim>/` + `agents/curator-reports/` + `04-agent-memory/curator-memory/` | `02-domain-know-how/`、`03-agent-memory/` 其他子目录、`SKILL.md`、模型对象 |
| **optimizer** | `agents/optimizer-reports/` + 候选 patches | `SKILL.md` / `scripts/`(除非 user 明确批准)、`02-simulation-file-experience/`、`02-domain-know-how/`、模型对象;**不依赖**其他 agent 的 session 输出 |
| **student** | `03-agent-memory/student-memory/` | 模型对象、`02-simulation-file-experience/`、`02-domain-know-how/`、`SKILL.md`、任何写操作 |
| **synthesizer** | `02-domain-know-how/<子目录>/<topic>.md` + `agents/synthesis-reports/` + `04-agent-memory/synthesizer-memory/` | `02-simulation-file-experience/` 任何文件(append-only 铁律)、`SKILL.md`、模型对象 |

### 3.2 边界可视化

```
                       ┌─────────────────────────────┐
                       │      模型对象 (in-memory)      │
                       │   .Models.*  .UserObjects.*   │
                       └─────────────────────────────┘
                                       ▲
                                       │ 写
              ┌─────────────────────────────┐
              │      expert (写)             │
              │      student (不写)         │
              │      curator (不写)         │
              │      optimizer (不写)       │
              │      synthesizer (不写)     │
              └─────────────────────────────┘
                                       ▲
                                       │ 读
              ┌──────────────────────────────────────────────┐
              │         5 个 agent 共享读取                    │
              └──────────────────────────────────────────────┘
```

---

## 四、5 个 Agent 的核心铁律对比

| 铁律 | expert | curator | optimizer | student | synthesizer |
|---|---|---|---|---|---|
| ❶ | SimTalkClaude 服务在线 Pre-flight | 永不 append 到已有非 README 文件 | 只读分析,绝不擅自改 SKILL.md / scripts;**只读 `skills/<x>/log/`** 即可独立运行 | 严格只读 — 拒绝任何"顺手改一下" | 绝不破坏 append-only archive |
| ❷ | GUI 动作前 infoBox 三要素 | 每次总结必同步 bump README | 🎯精准命中 + ⚡性能 + ✂️瘦身 三类 P0/P1 优先级清晰区分 | 笔记按 5 维镜像 `02-domain-know-how/` | 每条 finding ≥2 来源或 tentative |
| ❸ | session summary 不漏写 | "durable" 必须有 ≥2 个独立来源 | 建议必须有 log 证据链,禁止臆造 | Session 命名 + 索引三件套不漏 | 跨维度 cross-ref 必填 |

---

## 五、典型工作流场景

### 场景 A:用户说"在 Factory51 上加一个 method 到 Station"

```
[1] 主对话路由 → plant-simulation-expert(写操作)
[2] expert 调用 local-simtalk-write-simtalk 失败
[3] expert 通过 README/curator 报告找到 canonical pattern:createAttr + getAttribute
[4] expert 写 method → 完成 → session summary 写到 03-agent-memory/expert-memory/
[5] curator(下一轮)读 session summary → 发现 P0 finding(Station 加 method)
[6] curator quarantine 给 optimizer(因为是 SKILL.md 描述 gap——🎯精准命中)
[7] curator 在 02-simulation-file-experience/01-domain-concepts/logs/ 创建 per-entry file + bump README
[8] optimizer 读 curator quarantine + expert log → 产出 SKILL.md 修改建议(🎯精准命中)
[9] user 复核 → optimizer 落地 SKILL.md 修改
```

### 场景 B:用户说"学习 P4_CTU 模型"

```
[1] 主对话路由 → plant-simulation-student(纯读任务)
[2] student 用 bfs_full.py + read_library.py + probe_inheritance.py(只读 3 skill)
[3] student 按 5 维写笔记到 03-agent-memory/student-memory/
[4] expert(后续若用户问"现在实现 X")根据 student 笔记快速理解模型
[5] curator(下一轮)若发现 student 笔记中的 P0 finding → 转 append-only log
[6] synthesizer(后续)基于 curator 沉淀合成主题文档
```

### 场景 C:用户说"整理 02-domain-know-how/"

```
[1] 主对话路由 → plant-simulation-knowledge-synthesizer
[2] synthesizer 读 02-simulation-file-experience/<dim>/logs/ + curator reports + session summaries
[3] synthesizer 按 5 维路由 → 02-domain-know-how/<子目录>/<topic>.md
[4] synthesizer 写 audit report → agents/synthesis-reports/
[5] synthesizer 写 session log → 04-agent-memory/synthesizer-memory/
[6] user 复核 → 文件落地
```

### 场景 D:用户说"为什么 write_simtalk skill 这么慢"

```
[1] 主对话路由 → skills-optimizer(独立 agent,不需 expert 在线)
[2] optimizer 扫 skills/local-simtalk-write-simtalk/log/ 找三类信号:
    🎯精准命中(选错 skill)、⚡性能(timeout/silent fail)、✂️瘦身(过期章节)
[3] optimizer 读 SKILL.md + scripts/ 交叉验证
[4] optimizer 产出 agents/optimizer-reports/write-simtalk-YYYY-MM-DD.md + 候选 patches/
[5] user 复核后 → optimizer 才可 Edit SKILL.md(或 user 自己修)
```

### 场景 E:用户说"优化 skill 让 expert 选得更准"

```
[1] 主对话路由 → skills-optimizer
[2] optimizer 跨技能扫所有 skills/<x>/log/ 找 "用错 skill" / "should use X instead" 模式
[3] optimizer 产出 cross-cutting-YYYY-MM-DD.md 报告,列出"用户问 Y 时,N 个 skill 都被试过,实际 Z 最优"
[4] optimizer 产出候选 patch 指向 02-domain-know-how/03-modeling-know-how/03-software/skill-orchestration-guide.md
[5] user 复核 → 落地到 skill-orchestration-guide.md 决策矩阵
```

---

## 六、Agent 与 Skills 的关系(README 原话)

> **Skills 是手,Agent 是大脑**。

| 维度 | Skill | Agent |
|---|---|---|
| 触发方式 | `Skill` 工具 + skill 名 | `Agent` 工具 + `subagent_type` |
| 颗粒度 | 一个具体的操作能力(如"加方法注释"、"读属性") | 一组能力的编排 + 经验沉淀 |
| 上下文 | 通常作为主对话的旁路工具调用 | 拥有自己的子上下文,能跑多步任务 |
| 留痕 | skill 内部可在 `log/` 写产物 | agent 在 `skills/<x>/log/` 写调用日志 |

---

## 七、调用方式

在主对话里通过 `Agent` 工具调用:

```text
Agent(
  description: "<任务简述>",
  prompt: "<具体任务>",
  subagent_type: "<以下 5 个之一>"
)
```

**5 个 subagent_type 的使用场景**:

| subagent_type | 使用场景 |
|---|---|
| `plant-simulation-expert` | 用户想在 PS 里做 X / 跑 SimTalk / 改模型对象 / 扫模型结构 / 写 SimTalk 等**写操作任务** |
| `plant-simulation-experience-curator` | 用户说"沉淀近期经验"/"整理 02-simulation-file-experience"/"评审 supersede 候选" |
| `skills-optimizer` | 用户说"优化下技能"/"看看 log 有什么要修的"/"清理技能文档"/"把新发现沉淀进 SKILL.md"/"为什么这个 skill 这么慢"/"优化 skill 让 expert 选得更准"——产出 🎯精准命中 + ⚡性能 + ✂️瘦身 三类建议 |
| `plant-simulation-student` | 用户希望"学习 / 读懂 / 分析 / 对照 / 扫一遍模型结构 / 提炼某模型可借鉴模式"等**纯观察任务** |
| `plant-simulation-knowledge-synthesizer` | 用户说"整理领域知识"/"把经验沉淀到主题文档"/"刷新 02-domain-know-how"/"去重 + 合成跨 session findings" |

---

## 八、Memory 目录结构

每个 agent 都有自己的 memory 目录,记录自己的 session log:

```
04-agent-memory/
├── CONTRIBUTING.md                          ← 跨 agent 公共纪律
├── plant-simulation-expert-memory/            ← expert session summary (15 篇)
├── curator-memory/                            ← curator session log(空,待写)
├── student-memory/                            ← student session 笔记(空,待写)
└── synthesizer-memory/                        ← synthesizer session log(空,待写)
```

**核心规则**:
- 每个 agent session = 一份新文件(不 append 到已有 session)
- 每文件 ≤300 行
- 文件名:`YYYY-MM-DD_session-summary_<topic>.md`
- 索引文件 README.md 是 cold-start 第一动作

---

## 九、安装 / Install

仓库克隆到新机器后,默认不会自动出现在 OpenClaude / Claude Code 的 agent 列表中——需要运行仓库自带的安装脚本把 `agents/*.md` 软链到用户级目录:

```bash
# 一键(推荐):同时安装 skills + agents
bash scripts/install.sh

# 只装 agents
bash scripts/install.sh --agents-only

# 手动:仅 agents
bash scripts/link-agents.sh

# 卸载
bash scripts/install.sh --unlink
bash scripts/link-agents.sh --unlink
```

**默认目标目录**(按优先级):

- `$OPENCLAUDE_AGENTS_DIR`(环境变量覆盖)
- `~/.openclaude/agents/`(OpenClaude 默认)
- `~/.claude/agents/`(Claude Code 默认,找不到 `~/.openclaude` 时退到这里)

链接器**只创建符号链接**,不复制文件——仓库内的修改会立即生效。详见仓库根 `README.md` 的「安装与使用」节。

---

## 十、命名约定

- 文件名使用 kebab-case,与 frontmatter 的 `name` 字段一致
- frontmatter 必填字段:`name`、`description`、`tools`
- 正文用中文写"角色设定 + 工作流 + 硬规则",与 `skills/<name>/SKILL.md` 的格式保持一致

---

## 十一、历史

- **2026-08-28** — 创建 `plant-simulation-expert`(最初的大脑 agent)
- **2026-08-28** — 创建 `plant-simulation-experience-curator`(append-only 沉淀)
- **2026-08-31** — 创建 `skills-optimizer`(初版:SKILL.md 差距分析)
- **2026-09-01** — 强化 `skills-optimizer` 为**独立技能优化师**,聚焦 🎯精准命中 + ⚡性能提升 + ✂️瘦身 三类产出,可独立调度不依赖其他 agent
- **2026-09-01** — 创建 `plant-simulation-student`(5 维镜像只读笔记)
- **2026-09-01** — 创建 `plant-simulation-knowledge-synthesizer`(主题合成长文档);同时建 `04-agent-memory/synthesizer-memory/` 目录
- **5 agent 协作链 + 1 个独立路径**:expert 写 → curator 沉 → synthesizer 合 → student 只读镜像;**skills-optimizer 独立路径** 直接扫 skills/<x>/log/ 出优化建议,帮 expert 选对 skill

---

*Maintained by `@plant-simulation-expert` 与 `@plant-simulation-experience-curator`。*
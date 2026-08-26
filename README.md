# skills_of_plant_simulation

Plant Simulation（Siemens Tecnomatix）的 **Claude Code / OpenClaude 技能集**。以技能（Skill）形式封装「本地 SimTalk 执行、OS 函数速查、模型结构抽取」等能力，通过 TCP 驱动一台正在运行的 Plant Simulation 进程拿到真实执行结果，并复用 [knowledge_of_plant_simulation](https://github.com/CrazyCarlG/knowledge_of_plant_simulation) 知识库作为权威数据源。

> A collection of **Claude Code / OpenClaude skills** for Siemens Tecnomatix Plant Simulation — local SimTalk execution, OS-function reference, and model-structure extraction.

## 目录结构 / Directory Structure

```
skills_of_plant_simulation/
├── 01-plantsimulation-knowledge/               # [子模块] 知识库（帮助文档 Markdown + PDF→MD 工具链）
├── skills/                                     # 技能集（每个技能一个目录）
│   ├── local-simtalk-execution/                # 本地 SimTalk 执行（TCP 客户端，传输层底座）
│   ├── local-simtalk-os-functions/             # SimTalk OS 函数参考与实测
│   ├── local-simtalk-get-folder-tree/          # 模型对象层级抽取为 JSON 树
│   ├── local-simtalk-get-class-inheritance/    # 类继承结构（parent → children map）
│   ├── local-simtalk-read-library/             # 读 Method 源码（metadata + program）
│   ├── local-simtalk-class-management/         # 写：derive / duplicate / rename / delete / move 类
│   ├── local-simtalk-modify-object-atrribute/  # 读 & 写：对象属性（带 verify & restore）
│   ├── local-simtalk-add-note-to-method/       # 写：往单个 Method 插入注释行
│   └── local-simtalk-write-simtalk/            # 写：把 SimTalk 源代码写入 Method
├── agents/                                     # Agent 定义（由 Agent 工具以 subagent_type 调用）
│   └── plant-simulation-expert.md              #  Plant Simulation 专家 agent —— 选技能 + 用知识库 + 写 usage_log
├── docs/
│   └── skill-authoring.md                      # 技能编写规范
└── scripts/
    ├── install.sh                              # 一键安装（skills + agents 软链）
    ├── link-skills.sh                          # 仅软链 skills
    └── link-agents.sh                          # 仅软链 agents
```

## 技能清单 / Skills

底层只有一个 TCP 传输技能；其余 8 个都建立在它之上，按「读 / 写」两侧分组。

> One TCP-transport skill at the bottom; the other 8 build on it, grouped by **read** vs **write** side.

### 传输层 / Transport

| 技能 Skill | 用途 Description |
|---|---|
| `local-simtalk-execution` | 通过 TCP 连接在本机/局域网 Plant Simulation 进程中执行 SimTalk 代码（语法检查、方法调用、对象查询、模型运行、异常诊断），拿回真实执行结果 |

### 只读侧 / Read-only Inspection

| 技能 Skill | 用途 Description |
|---|---|
| `local-simtalk-get-folder-tree` | 把当前加载到 Plant Simulation 的模型（`.current`）对象层级（Frame / Folder / 物料流 / Method / Variable）抽取为结构化 JSON 树 |
| `local-simtalk-get-class-inheritance` | 对每个候选类查询 `Origin` / `OriginRoot` / `Class` / `InternalClassType`，渲染 parent → children 继承图谱；列出用户派生类 |
| `local-simtalk-read-library` | 读出所有 Method 对象的 metadata（path / name / type / Encrypted / HasSyntaxError / NumInExecution）+ 完整 `&Method.Program` 源码 |
| `local-simtalk-os-functions` | 20 个 SimTalk 预定义操作系统函数（内存 / 进程 / 目录 / 环境变量 / 注册表 / 文件 / 剪贴板 / 外部进程 / 系统命令等）的参考与本地实测助手 |

### 写入侧 / Write-side Mutation

| 技能 Skill | 用途 Description |
|---|---|
| `local-simtalk-class-management` | 在 Class Library 里 derive / duplicate / rename / delete / move 类，以及管理 user-defined attribute（createAttr / deleteAttr / setAttribute / inheritAttribute） |
| `local-simtalk-modify-object-atrribute` | 在单个对象上 **read → write → read → restore** 一个属性（boolean / integer / real / string / dateTime / time / object ref），每次写后回读验证 |
| `local-simtalk-add-note-to-method` | 往单个 Method 对象的 `program` 里插入注释行（`--` / `//` / `/* */`），**保留原始可执行代码字节级不变**，只增不删不改 |
| `local-simtalk-write-simtalk` | 把完整 SimTalk 源代码写入 Method：现有 Method → 直接改 `program`；新 Method → `.&Method.duplicate(<frame>, <name>)` 后再写入 |

### 依赖关系 / Dependency Graph

```
local-simtalk-execution                ← 传输层底座（其它 8 个都依赖它）
        │
        ├── local-simtalk-os-functions
        ├── local-simtalk-get-folder-tree
        │       │
        │       ├── local-simtalk-get-class-inheritance
        │       └── local-simtalk-read-library
        │
        ├── local-simtalk-class-management
        ├── local-simtalk-modify-object-atrribute
        └── local-simtalk-add-note-to-method
                └── local-simtalk-write-simtalk
```

> 所有「会挂死」的硬规则（`type` 字段白名单、模态陷阱、回复分帧、WSL2 连接方式等）统一维护在 `local-simtalk-execution/references/lifelines.md`，硬规则变更只改那一个文件。

## Agent / Agent 列表

| Agent `subagent_type` | 用途 Description | 文件 |
|---|---|---|
| `plant-simulation-expert` | Plant Simulation / SimTalk / 模型操作领域专家：根据请求挑技能、调用 `skills/` 下的对应能力、对接 `01-plantsimulation-knowledge/` 知识库，并在每次技能调用后把全过程记入 `skills/<skill>/usage_log/` | [`agents/plant-simulation-expert.md`](agents/plant-simulation-expert.md) |

调用示例：

```text
Agent(
  subagent_type: "plant-simulation-expert",
  description: "<任务简述>",
  prompt: "<具体任务>"
)
```

## 安装与使用 / Install & Use

### 一键安装 / One-shot Install

```bash
# 克隆（含子模块）/ Clone with submodule
git clone --recurse-submodules <repo-url>
# 已有仓库补拉子模块 / For an existing clone, fetch the submodule
git submodule update --init --recursive
cd skills_of_plant_simulation

# 一键把 skills + agents 软链到用户级目录（推荐）
# Symlink everything (skills + agents) into user-level dirs (recommended)
bash scripts/install.sh

# 仅装 skills / skills only
bash scripts/install.sh --skills-only

# 仅装 agents / agents only
bash scripts/install.sh --agents-only

# 卸载（只删除本脚本创建的符号链接，不会删真实文件）
# Uninstall (removes symlinks only, never touches real files)
bash scripts/install.sh --unlink
```

### 分步安装 / Manual Install

```bash
# 只软链 skills
bash scripts/link-skills.sh

# 只软链 agents
bash scripts/link-agents.sh

# 卸载对应链接
bash scripts/link-skills.sh --unlink
bash scripts/link-agents.sh --unlink
```

### 目标目录 / Target Dirs

| 资源 | 默认目标 | 覆盖环境变量 |
|---|---|---|
| skills | `~/.claude/skills/` | `OPENCLAUDE_SKILLS_DIR` |
| agents | `~/.openclaude/agents/`（若 `~/.openclaude` 不存在则退到 `~/.claude/agents/`） | `OPENCLAUDE_AGENTS_DIR` |

> 安装器**只创建符号链接**，不会复制 / 移动任何源文件——仓库更新后下次 `Skill` / `Agent` 调用自动看到最新内容。但请保持仓库目录结构不被移动，否则相对路径（`01-plantsimulation-knowledge/...`）会断裂。

## 路径约定 / Path Convention

所有技能通过「以仓库根为基准」的相对路径引用知识库，例如 `01-plantsimulation-knowledge/01-plant-simulation-help/objects/`。详见 [docs/skill-authoring.md](docs/skill-authoring.md)。

> All skills reference the knowledge base via repo-root-relative paths. See [docs/skill-authoring.md](docs/skill-authoring.md).

## 许可证与版权 / License & Copyright

- 技能与脚本：**GPL-3.0**，见 [LICENSE](LICENSE)。**English:** Skills & scripts: **GPL-3.0**, see [LICENSE](LICENSE).
- 知识库内容：来源于 Siemens《Plant Simulation Help》（© 2026 Siemens，Unpublished work），仅用于学习与知识管理，版权归 Siemens 所有。
  **English:** Knowledge content is sourced from Siemens *Plant Simulation Help* (© 2026 Siemens, Unpublished work), for learning and knowledge management only; all rights belong to Siemens.

# Plant Simulation Skills 2.0

用一套 **OpenClaude / Claude Code 技能（Skill）** 把 Siemens Tecnomatix Plant Simulation 接入 AI Agent：

- **查** —— 官方 CoPilot RAG 服务回答 SimTalk 语法、对象方法、API 行为，并附带官方文档引文。
- **做** —— 把 SimTalk 代码真正送进运行中的 Plant Simulation 执行、查状态、读模型结构。

Agent 负责决策与编排，Skill 负责"手脚"；两者之间用两条本机链路连接：

```
┌──────────────┐   ① 知识层    ┌──────────────────────────────┐
│              │ ────────────► │ 官方 CoPilot RAG 服务        │
│   Agent      │   HTTP/SSE   │ FastAPI @ 127.0.0.1:8002    │
│              │ ◄──────────── │ RAG 检索 + LLM + 引文        │
│  skills/     │              └──────────────────────────────┘
│  10 个技能   │
│              │   ② 执行层    ┌──────────────────────────────┐
│              │ ────────────► │ SimtalkClaude.pslib 注入 PS   │
│              │   TCP 帧协议  │ SocketServer @ 127.0.0.1:50007│
└──────────────┘ ◄──────────── └──────────────────────────────┘
```

| 层 | 技术 | 默认端点 | 职责 |
| --- | --- | --- | --- |
| 知识层 | 官方 CoPilot（LangGraph + FAISS + arctic-embed） | `127.0.0.1:8002` | 官方文档检索与问答，返回 `answer` / `citations` / `metrics` |
| 执行层 | `SimtalkClaude.pslib` 注入进 PS 模型 | `127.0.0.1:50007` | 在真实 PS 进程内执行 SimTalk、读对象树与源码 |
| 编排层 | `skills/` + `agent/plant-simulation.agent.md` | — | 技能路由、硬规则、前置检查 |

---

## 目录结构

```
skills_of_plant_simulation/
├── agent/
│   └── plant-simulation.agent.md   # 专项 agent：技能路由表 + 工作流程 + 任务边界
├── skills/                          # 10 个技能，每个含 SKILL.md（frontmatter 描述触发场景）
│   ├── local-get-rag-knowledge/     # 查：RAG 知识问答（HTTP wrapper）
│   ├── local-window-com-start-plant-simulation/  # 起：通过 COM 启动 PS
│   ├── local-simtalk-ping/          # 探：TCP 连通性
│   ├── local-simtalk-checksyntax/   # 查：SimTalk 语法/编译检查（不执行）
│   ├── local-simtalk-runsimtalk/    # 执行：真跑 SimTalk（改模型状态）
│   ├── local-simtalk-read-rootfolder/    # 读：根目录对象树
│   ├── local-simtalk-read-foldertree/    # 读：子目录对象树
│   ├── local-simtalk-read-program/       # 读：Method 的 SimTalk 源码
│   ├── local-simtalk-read-console/       # 读：GUI Console 输出（技能名 local-simtalk-readlog）
│   └── local-simtalk-read-userdefine-attri/  # 读：对象自定义属性
├── Copilot-using/                   # 官方 CoPilot 的本机客户端与启停脚本
│   ├── start_copilot.bat            # 后台启动 RAG 服务（双击）
│   ├── stop_copilot.bat             # 停止 RAG 服务（双击）
│   ├── ask_copilot.py               # 纯标准库 HTTP 客户端
│   ├── copilot_config.py            # 读取 config/local.properties 的 Python 侧
│   ├── 00-原理总结.md                # CoPilot 架构原理
│   └── 使用教程.md                   # 命令行使用教程
├── config/                          # 路径与依赖的单一事实源
│   ├── local.properties             # CoPilot 安装路径 / 主机 / 端口（cmd + Python 共读）
│   ├── load_paths.cmd               # 供 .bat 调用的配置加载器
│   └── copilot-requirements.txt     # CoPilot 服务自身的依赖（官方 requirements 的副本）
├── simtalkclaude-client/
│   └── SimtalkClaude.pslib          # 注入 PS 模型的桥接库（SocketServer 宿主）
├── requirements.txt                 # 本仓库自身脚本的依赖（pywin32 / PyYAML）
├── .openclaude/                     # 本地权限配置 + skill-creator
├── .gitignore                       # 忽略 Copilot/（本地运行时，见下文）
└── README.md
```

> `Copilot/` 目录是**本机 CoPilot 运行时**（内嵌 Python 3.14.5 + arctic-embed 模型权重，约 1.6 GB），含 >100 MB 的单个文件，GitHub 拒绝接收。它**不在版本库里**，运行时装在 `C:\ProgramFiles\Siemens\TecnomatixPlantSimulation2606\Copilot`——这个路径写在 `config/local.properties` 里，不再散落在脚本中。

---

## 配置（单一事实源）

所有 CoPilot 运行时路径集中在 `config/local.properties`（`KEY=VALUE`，`;` 起注释，**保持 ASCII**，因为 cmd.exe 与 Python 都要解析它）：

| 键 | 默认值 | 用途 |
| --- | --- | --- |
| `COPILOT_DIR` | `C:\ProgramFiles\Siemens\TecnomatixPlantSimulation2606\Copilot` | CoPilot 运行时根目录 |
| `COPILOT_PYTHON` | `python-3.14.5-embed\pythonw.exe` | 内嵌 Python（相对 `COPILOT_DIR`） |
| `COPILOT_SERVICE_FILE` | `copilot_service.py` | 服务入口文件 |
| `COPILOT_SERVICE` | `copilot_service:app` | uvicorn 的 `module:app` |
| `COPILOT_HOST` / `COPILOT_PORT` | `127.0.0.1` / `8002` | 知识层 HTTP 端点 |
| `COPILOT_LOG_SUBDIR` / `COPILOT_LOG_FILE` | `logs` / `copilot.log` | 日志位置（相对 `COPILOT_DIR`） |

改完直接生效，两条链路都会跟着变：

- **cmd.exe 侧** —— `config/load_paths.cmd` 用 `for /f` 解析，被 `start_copilot.bat` / `stop_copilot.bat` `call`。缺键时脚本报错退出，不会带着半截路径往下跑。
- **Python 侧** —— `Copilot-using/copilot_config.py` 解析同一份文件，提供 `get(key)`（带默认值兜底）。`ask_copilot.py` 与 `skills/local-get-rag-knowledge/scripts/rag_ask.py` 都从这里取 `BASE`，不再各自硬编码 `8002` 或机器绝对路径。

### 依赖

| 文件 | 装什么 | 怎么装 |
| --- | --- | --- |
| `requirements.txt` | 本仓库脚本的依赖：`pywin32`（COM 启动 PS）、`PyYAML`（skill-creator 的 frontmatter 校验） | `python -m venv .venv && .venv\Scripts\python -m pip install -r requirements.txt` |
| `config/copilot-requirements.txt` | CoPilot **服务自身**的依赖（fastapi / uvicorn / langgraph / faiss-cpu / sentence-transformers …） | 通常不用手动装——`Copilot/setup.bat` 会用内嵌 Python 执行 `pip install -r requirements.txt` |

> `skills/` 下的 socket 脚本、`Copilot-using/ask_copilot.py`、`copilot_config.py` 全部只用标准库（`socket` / `json` / `urllib`），不装任何东西也能跑。

---

## 前置条件

| 依赖 | 要求 | 验证 |
| --- | --- | --- |
| 操作系统 | Windows（COM 启动技能仅支持 Windows） | — |
| Plant Simulation | 2606 已安装，COM 类 `Tecnomatix.PlantSimulation.RemoteControl.26.6` 已注册 | `python -c "import win32com.client; win32com.client.Dispatch('Tecnomatix.PlantSimulation.RemoteControl.26.6')"` 不报错 |
| Python | 仓库自带 `.venv`（3.13，已装 `pywin32`）；RAG wrapper 只用标准库 | `.venv/Scripts/python --version` |
| CoPilot | 已随 PS 安装（路径见 `config/local.properties` 的 `COPILOT_DIR`），且 LLM 凭据已配置（`/health` 的 `agent_ready == true`） | `python skills/local-get-rag-knowledge/scripts/rag_ask.py --health` |
| 模型文件 | 至少一个 `.spp`（启动 PS 必需） | — |

安装本仓库脚本的依赖（只有 COM 启动和 frontmatter 校验需要）：

```bash
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
```

---

## 使用指南（How to use）

三条使用路线，按需要选一条或多条：

| 路线 | 做什么 | 需要启动的东西 | 章节 |
| --- | --- | --- | --- |
| **A. 走 Agent**（推荐） | 用自然语言提需求，Agent 自己选技能、查文档、连 PS 执行 | CoPilot 服务 + （需要执行时）Plant Simulation | [§1](#路线-a--走-agent推荐) |
| **B. 只查知识** | 命令行问官方文档，拿答案 + 引文 | CoPilot 服务 | [§2](#路线-b--只查知识层) |
| **C. 只操作模型** | 命令行启 PS、跑 SimTalk、读模型结构 | Plant Simulation | [§3](#路线-c--只操作执行层) |

---

### 0. 一次性准备

```bash
# 1) 依赖（只有 COM 启动脚本和 skill-creator 需要第三方包）
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# 2) 确认 CoPilot 运行时已安装；路径在 config/local.properties 的 COPILOT_DIR
#    不在本机就改这一行，其余脚本自动跟着走
notepad config\local.properties

# 3) 确认 PS 的 COM 类已注册
.venv\Scripts\python -c "import win32com.client; win32com.client.Dispatch('Tecnomatix.PlantSimulation.RemoteControl.26.6')"
```

第 3 步不报错就说明 COM 链路可用。报 `0x80080005` 通常是**有多个 PS 实例在跑**，先清场：

```bash
taskkill /IM "Plant Simulation.exe" /F
```

> 下文所有示例都用 `python` 指代你的解释器。除 `start_plant_simulation.py` 外，脚本只用标准库，系统 Python 直接跑也行；只有 COM 那个必须用装了 `pywin32` 的 `.venv\Scripts\python.exe`。

---

### 路线 A — 走 Agent（推荐）

在 OpenClaude / Claude Code 里加载本仓库的 agent（`agent/plant-simulation.agent.md`），然后直接用自然语言提需求：

```
/plant-simulation 帮我看看 Buffer 的 create 方法签名，并到跑着的模型上验证一下
```

Agent 会按 `agent/plant-simulation.agent.md` 的路由表自动选技能，标准流程是 6 步：

1. **先查 RAG** —— 带上你的原始问题 + 相关上下文摘要
2. **读 `answer` / `citations` / `metrics`** —— 判断是纯知识问题还是要动模型
3. **按依赖执行技能** —— 启动 → ping → syntax check → 执行 → 读结构
4. **把新增结果回交 RAG** —— 让它基于实测结果再解释一遍
5. **按进展迭代** —— 没有必要的新动作就停
6. **综合收尾** —— 明确区分「文档知识」/「实测结果」/「推论」

**Agent 侧两条硬规矩**（写进了 agent 文件，务必遵守）：

- RAG **必须**走 `skills/local-get-rag-knowledge/scripts/rag_ask.py` wrapper，**不要**直接调 `ask_copilot.py`——后者会把 SSE token 流持续打到 stdout，污染上下文。
- 提问前先做 `/health` 探测。服务冷启动时直接发 `/query/stream` 会撞上连接挂死。

Agent 端 timeout 建议 **≥ 120 s**（复杂问题实测 30–90 s）。

---

### 路线 B — 只查知识层

#### B1. 启动 RAG 服务

```bash
# 方式 1：双击 Copilot-using\start_copilot.bat
# 方式 2：命令行跑同一个脚本（能看到输出）
cmd //c "Copilot-using\start_copilot.bat"
```

脚本做这几件事：读 `config/local.properties` → 检查内嵌 Python 与服务文件 → 后台 `start /B` 拉起 uvicorn → 轮询 `/health` 直到 200 → 打印 `/health` 的 JSON。

想手动拉起（日志直接打在终端里）：

```bash
cd "<COPILOT_DIR>"
"<COPILOT_DIR>\python-3.14.5-embed\python.exe" -m uvicorn copilot_service:app --host 127.0.0.1 --port 8002
```

- `pythonw.exe` 不弹窗（后台跑），`python.exe` 会在终端实时打日志。
- 日志文件固定落在 `%COPILOT_DIR%\logs\copilot.log`。

> **冷启动要等**：实测首次约 **5 分钟**（加载 torch + arctic-embed 模型 + FAISS 索引）。`start_copilot.bat` 自己会轮询等最多 480 s，**别在这个窗口里重复启动**。

确认就绪：

```bash
curl -s http://127.0.0.1:8002/health
# {"status":"ok","agent_ready":true,"has_credentials":true,"local_tools":4,"mcp_tools":0}
```

`agent_ready` 必须是 `true`（否则是 LLM 凭据没配）。

停止：

```bash
cmd //c "Copilot-using\stop_copilot.bat"
# 或
curl -X POST http://127.0.0.1:8002/shutdown
```

#### B2. 提问

```bash
# 普通模式：答案正文 + 引文列表 + [metrics]
python skills/local-get-rag-knowledge/scripts/rag_ask.py "How do I create a Buffer in SimTalk?"

# 原始 JSON（给程序消费）
python skills/local-get-rag-knowledge/scripts/rag_ask.py --json "Buffer 和 PlaceBuffer 有什么区别?"

# 只探测就绪状态
python skills/local-get-rag-knowledge/scripts/rag_ask.py --health

# 实时 token 流（人工看效果用；Agent 不要用）
python skills/local-get-rag-knowledge/scripts/rag_ask.py --stream "What is a Drain?"

# 从 stdin 读问题（长问题避免命令行转义地狱）
echo "How do I create a Buffer in SimTalk?" | python skills/local-get-rag-knowledge/scripts/rag_ask.py
```

输出长这样：

```
<答案正文>

[citations]
  - Drain [object]  https://docs.sw.siemens.com/.../id15363
  - Methods of the Drain  https://docs.sw.siemens.com/.../id67037

[metrics] 87.73s  tools=22  tokens_in/out=0/0
```

引文里的 `tDocLink` 是官方文档直链，**可以放心给用户**。

#### B3. 直接用底层客户端（仅人工调试）

```bash
python Copilot-using/ask_copilot.py "How do I create a Buffer in SimTalk?"
```

`ask_copilot.py` 会把 SSE token 流**逐字打到 stdout**。人看没问题，**Agent 用会污染上下文**，所以 Agent 侧一律用 `rag_ask.py`。

---

### 路线 C — 只操作执行层

#### C1. 启动 Plant Simulation

```bash
.venv\Scripts\python skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model "C:\ProgramFiles\Siemens\TecnomatixPlantSimulation2606\Examples\Demo\BIW_ConceptSimulation.spp" \
  --simtalkclaudefile "simtalkclaude-client/SimtalkClaude.pslib" \
  --port 50007 --print-pid
```

脚本做四件事：COM `Dispatch` → `LoadModel` → `basis.loadObjectAs` 注入 `SimtalkClaude.pslib` → 把第一个可用端口写进 `.SimtalkClaude.Main.SocketServer.mysocket.port`。

**flag 说明**：

| Flag | 默认 | 说明 |
| --- | --- | --- |
| `-m / --model` | 无（**必填**） | `.spp` 模型文件路径；不存在退出码 `4` |
| `-s / --simtalkclaudefile` | 无（**必填**） | `SimtalkClaude.pslib` 路径；不存在退出码 `4` |
| `-p / --port` | `50007` | 端口扫描起点，被占用就往上找 |
| `--no-visible` | 显示窗口 | 隐藏 PS 窗口（CI / 无人值守） |
| `--allow-message-box` | 禁弹窗 | 允许模型加载失败时弹窗（排查用） |
| `--print-pid` | 关 | 打印所有 `Plant Simulation.exe` 的 PID |

**退出码**：`0` 成功 / `2` 参数或端口错 / `3` COM 错 / `4` 文件不存在 / `5` 其它异常。

> ⚠️ **退出码 0 不代表可用**——它只证明「COM + 注入 + 改端口」三步通过，**不含 socket 验证**。必须接着 ping 一次。

#### C2. 验证链路

```bash
python skills/local-simtalk-ping/scripts/simtalk_send.py
```

ping 成功才算 PS 侧真的可用了。

#### C3. 语法检查（不执行、不改状态）

```bash
python skills/local-simtalk-checksyntax/scripts/simtalk_send.py --timeout 10 'var n: integer := 3; print n'

# 限定命名空间（可选）
python skills/local-simtalk-checksyntax/scripts/simtalk_send.py --target-path ".Models.Model" 'n := 3'
```

#### C4. 真正执行（**会改模型状态**）

```bash
python skills/local-simtalk-runsimtalk/scripts/simtalk_runsimtalk.py --timeout 30 'print("hello from SimTalk")'
```

#### C5. 读模型结构

```bash
# 根目录对象树
python skills/local-simtalk-read-rootfolder/scripts/simtalk_readrootfolder.py

# 某个文件夹的对象树（不带前导点）
python skills/local-simtalk-read-foldertree/scripts/simtalk_readfoldertree.py --foldername "Models.Model"

# 某个 Method 的 SimTalk 源码（带前导点的绝对路径）
python skills/local-simtalk-read-program/scripts/simtalk_readprogram.py --methodpath ".Models.Model.Method2"

# 对象的自定义属性（带前导点的绝对路径）
python skills/local-simtalk-read-userdefine-attri/scripts/simtalk_readuserdefine.py --target ".Models.Model.Source"

# GUI Console 输出
python skills/local-simtalk-read-console/scripts/simtalk_readlog.py
```

> **路径格式坑**：`readfoldertree` 的 `--foldername` **不带**前导点（`Models.Model`）；`readprogram` / `readuserdefine` 的路径**必须带**前导点（`.Models.Model.Method2`）。写错会回 `not exists!` / `invalid path`，退出码 `10`。先用 `readrootfolder` / `readfoldertree` 拿到真实路径再传。

#### C6. 执行层脚本的公共 flag

所有 `skills/local-simtalk-*/scripts/*.py` 都支持：

| Flag | 默认 | 说明 |
| --- | --- | --- |
| `--host` | `127.0.0.1` | PS 侧 socket 地址 |
| `--port` | `50007` | PS 侧 socket 端口 |
| `--timeout` | `30` | 秒 |

> WSL2 / 容器里 `127.0.0.1` 指向容器自身，连不上 Windows 上的 PS，必须显式写 `--host host.docker.internal`；Windows 原生环境一律用默认的 `127.0.0.1`（本机实测 `host.docker.internal` 会被解析到公网 IP `129.103.156.108`，原生环境千万别用）。

---

### 端到端完整演练

从零跑通「查文档 → 起 PS → 验证 → 执行 → 读回」：

```bash
# ① 查知识层
cmd //c "Copilot-using\start_copilot.bat"
python skills/local-get-rag-knowledge/scripts/rag_ask.py --health
python skills/local-get-rag-knowledge/scripts/rag_ask.py "How do I create a Buffer in SimTalk?"

# ② 起 PS 并注入桥接库
.venv\Scripts\python skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model "<你的 .spp>" --simtalkclaudefile "simtalkclaude-client/SimtalkClaude.pslib" --print-pid

# ③ 验证链路
python skills/local-simtalk-ping/scripts/simtalk_send.py

# ④ 先语法检查，再真跑
python skills/local-simtalk-checksyntax/scripts/simtalk_send.py 'var n: integer := 3; print n'
python skills/local-simtalk-runsimtalk/scripts/simtalk_runsimtalk.py 'print("hello")'

# ⑤ 读回结果
python skills/local-simtalk-read-rootfolder/scripts/simtalk_readrootfolder.py
python skills/local-simtalk-read-console/scripts/simtalk_readlog.py

# ⑥ 收工
cmd //c "Copilot-using\stop_copilot.bat"
```

---

### 常见任务速查

| 我想…… | 命令 |
| --- | --- |
| 查 SimTalk 某个对象/方法的官方用法 | `rag_ask.py "How do I use <Object>?"` |
| 确认服务活着 | `rag_ask.py --health` |
| 起 PS 并装上桥接库 | `start_plant_simulation.py --model <x.spp> --simtalkclaudefile simtalkclaude-client/SimtalkClaude.pslib` |
| 确认 PS 侧可连 | `local-simtalk-ping/scripts/simtalk_send.py` |
| 试一段 SimTalk 语法（不执行） | `local-simtalk-checksyntax/scripts/simtalk_send.py '<code>'` |
| 真的执行一段 SimTalk | `local-simtalk-runsimtalk/scripts/simtalk_runsimtalk.py '<code>'` |
| 看模型里有什么对象 | `local-simtalk-read-rootfolder/scripts/simtalk_readrootfolder.py` |
| 看某个 Method 写了什么 | `local-simtalk-read-program/scripts/simtalk_readprogram.py --methodpath ".Models.X.init"` |
| 看 Console 里的输出 | `local-simtalk-read-console/scripts/simtalk_readlog.py` |

---

## 技能一览

| 技能 | 帧类型 | 作用 | 改模型状态 |
| --- | --- | --- | --- |
| `local-get-rag-knowledge` | HTTP `/query/stream` | 官方文档问答 + 引文 | 否 |
| `local-window-com-start-plant-simulation` | COM | 启动 PS、加载 `.spp`、注入 pslib、配端口 | 是（起进程） |
| `local-simtalk-ping` | `ping` | 链路连通性 | 否 |
| `local-simtalk-checksyntax` | `simtalk_syntax` | 编译检查 | 否 |
| `local-simtalk-runsimtalk` | `simtalk_run` | 真正执行 SimTalk | **是** |
| `local-simtalk-read-rootfolder` | `readrootfolder` | 根目录对象树 | 否 |
| `local-simtalk-read-foldertree` | `readfoldertree` | 子目录对象树 | 否 |
| `local-simtalk-read-program` | `readprogram` | Method 源码 | 否 |
| `local-simtalk-read-console` | `readlog` | GUI Console 输出 | 否 |
| `local-simtalk-read-userdefine-attri` | `readcustomatrributes` | 自定义属性 | 否 |

每个技能的 `SKILL.md` 带 YAML frontmatter（`name` + `description`），`description` 描述触发场景——Agent 靠它决定何时加载该技能。

---

## TCP 帧协议（执行层）

所有请求是 `JSON + "||END||"` 一次 TCP 连接，响应同样以 `||END||` 结尾。

| 方向 | 示例 |
| --- | --- |
| 请求 | `{"type":"simtalk_run","action_id":"<hex>","simtalk_code":"print(1)"}` |
| 响应 | `{"type":"simtalk_run","result":"success","log":"execute success"}` |

必需参数：

| `type` | 附加字段 |
| --- | --- |
| `ping` | — |
| `simtalk_syntax` | `simtalk_code`（可选 `target_path` 限定命名空间） |
| `simtalk_run` | `simtalk_code` |
| `readlog` | — |
| `readrootfolder` | — |
| `readfoldertree` | `foldername` |
| `readprogram` | `methodpath`（点分路径，如 `Models.Model.init`） |
| `readcustomatrributes` | `target` |

### 退出码约定

| 码 | 含义 |
| --- | --- |
| `0` | 成功（`ping` / `simtalk_syntax` / `simtalk_run` 的成功路径） |
| `1` | socket 超时 |
| `2` | 无法连接 |
| `3` | 连接中途断开 / 回包非 JSON |
| `10` | 回包合法但 `result`/`status` ≠ success |
| `11` | `simtalk_run` 运行时异常（`result=success` 但 `log` 以 `code execute failed` 开头） |
| `12` | 语法检查失败，或回包非 JSON |
| `20` | 只读类技能成功路径——**stdout 是有效内容，不要当失败丢弃** |

> 只读类技能（`readlog` / `readfoldertree` / `readprogram` / `readuserdefine`）成功时返回 `20` 而非 `0`，这是脚本实现约定，判定结果请看 stdout。`readrootfolder` 是例外，成功返回 `0`。

---

## 默认连接地址

所有 `skills/*/scripts/*.py` 的 socket 脚本共用同一组默认值：

| 场景 | `--host` | `--port` | `--timeout` |
| --- | --- | --- | --- |
| 原生 Windows（默认） | `127.0.0.1` | `50007` | `30` |
| WSL2 / 容器 → PS 主机 | `host.docker.internal` | `50007` | `30` |

- WSL2 / 容器里写 `127.0.0.1` 会落到容器自身，连接被拒，必须显式传 `--host host.docker.internal`。
- Windows 原生环境**不要**用 `host.docker.internal`：本机实测该名字会解析到公网 IP `129.103.156.108`，而非本机回环。

---

## 硬规则与已知坑

- **RAG 是首轮知识入口**，但不等于模型实测结果；文档知识与实测结论必须分开陈述。
- **不要绕过 `/health` 探测直接问**——服务冷启动时直接发 `/query/stream` 会撞到连接挂死。
- **`simtalk_syntax` 抓不到模态陷阱**：`prompt()` / `infoBox()` / `promptList*()` 会弹窗等 GUI 点 OK，卡死进程。改用 `print`。
- **不要向未声明的全局 attr 赋值**（`MyAttr := X`），用局部 `var` 或先在 GUI 建好属性。
- **`simtalk_run` 的 `data` 字段恒为空**，`retsult` 是服务端拼写错误的缓存字段——两者都别读。看 `result` 和 `log`。
- **`print(X)` 的值不经 socket 回传**，要去 PS GUI（Window ribbon → Console）肉眼读，或用 `readlog` 拉。
- **多个 PS 实例并存会导致 COM 报 `0x80080005`**，先 `taskkill /IM "Plant Simulation.exe" /F` 清场。
- **`start_plant_simulation.py` 不落盘 console log**，输出由 PS GUI 自行决定。

各技能的完整故障排查表在对应 `SKILL.md` 与 `references/` 下（RAG：`references/troubleshooting.md`；启动 PS：`references/lifelines.md` + `references/cli-args.md`）。

---

## 文档索引

| 文档 | 内容 |
| --- | --- |
| `agent/plant-simulation.agent.md` | Agent 的技能路由表、6 步工作流、任务边界 |
| `config/local.properties` | CoPilot 路径 / 主机 / 端口的唯一配置源 |
| `requirements.txt` | 本仓库脚本的依赖 |
| `config/copilot-requirements.txt` | CoPilot 服务自身的依赖（官方 requirements 副本） |
| `Copilot-using/使用教程.md` | CoPilot 命令行使用教程 |
| `Copilot-using/00-原理总结.md` | CoPilot 客户端-服务器架构与内部原理 |
| `skills/local-get-rag-knowledge/references/quick-start.md` | RAG 三种调用模式 + 退出码速查 |
| `skills/local-window-com-start-plant-simulation/references/cli-args.md` | 启动脚本逐 flag 详解 |
| `skills/local-window-com-start-plant-simulation/examples/` | e2e 示例与冒烟测试 |
| `simtalkclaude-client/SimtalkClaude.pslib` | 桥接库本体（注入 PS） |

---

## 分支

- `main` —— 主线。
- `fea/20261018-dev` —— **当前开发分支**：技能 2.0 架构（10 个细分技能替代原单一大技能）。

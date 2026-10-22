# Plant Simulation Skills 2.0

本项目通过 Agent 调用 Plant Simulation Copilot RAG 查询官方文档，并通过本地桥接在 Plant Simulation 中检查或执行 SimTalk。

This project uses an Agent to query official documentation through Plant Simulation Copilot RAG, and a local bridge to inspect or execute SimTalk in Plant Simulation.

| 部分 / Component | 位置 / 默认端点 / Location or default endpoint | 用途 / Purpose |
| --- | --- | --- |
| Agent | `agent/plant-simulation.agent.md` | 路由任务并编排技能 / Routes tasks and orchestrates skills |
| Skills | `skills/` | RAG 查询、启动、检查、执行及模型读取 / RAG queries, startup, checks, execution, and model inspection |
| Copilot RAG | `127.0.0.1:8002` | 官方知识检索与问答 / Official documentation retrieval and Q&A |
| Plant Simulation bridge | `127.0.0.1:50007` | 连接运行中的模型 / Connects to a running model |

## 环境要求 / Requirements

- Windows、Plant Simulation 2606，以及已注册的 COM 接口。 / Windows, Plant Simulation 2606, and a registered COM interface.
- Python 3.13 虚拟环境；COM 启动脚本需要 `pywin32`。 / A Python 3.13 virtual environment; the COM launcher requires `pywin32`.
- Plant Simulation Copilot-Full 和已配置的 provider，见 [安装视频](Copilot-FULL-Setup.mp4)。 / Plant Simulation Copilot-Full with a provider configured; see the [setup video](Copilot-FULL-Setup.mp4).
- 支持 Agent/Skills 的 CLI 工具，例如 OpenClaude、GitHub Copilot 或 OpenClaw。 / A CLI agent that supports Agents/Skills, such as OpenClaude, GitHub Copilot, or OpenClaw.
- 需要控制模型时，准备 `.spp` 文件。安装与检查步骤见下方 How to use。 / To control a model, provide an `.spp` file. See How to use below for setup and verification.

---

## 使用指南 / How to use



#### 一次性准备 / One-time setup

```bash
# 1) 依赖 / Dependencies (only the COM launcher and skill-creator need third-party packages)
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt

# 2) 确认 CoPilot 已安装 / Confirm CoPilot is installed; its path is set in config/local.properties
#    按本机情况修改 / Update it for this machine; scripts use the configured path.
notepad config\local.properties

# 3) 确认 Plant Simulation COM 类已注册 / Confirm the Plant Simulation COM class is registered.
.venv\Scripts\python -c "import win32com.client; win32com.client.Dispatch('Tecnomatix.PlantSimulation.RemoteControl.26.6')"
```

第 3 步不报错就说明 COM 链路可用。报 `0x80080005` 通常是**有多个 PS 实例在跑**，先清场：

If step 3 completes without an error, the COM connection is available. Error `0x80080005` usually means multiple Plant Simulation instances are running; close them first:

```bash
taskkill /IM "Plant Simulation.exe" /F
```

> 下文所有示例都用 `python` 指代你的解释器。除 `start_plant_simulation.py` 外，脚本只用标准库，系统 Python 直接跑也行；只有 COM 那个必须用装了 `pywin32` 的 `.venv\Scripts\python.exe`。
>
> In the examples below, `python` means your selected interpreter. All scripts except `start_plant_simulation.py` use only the standard library and can run with system Python. The COM launcher must use `.venv\Scripts\python.exe` with `pywin32` installed.

---


#### 启动 Plant Simulation CoPilot RAG 服务 / Start the Plant Simulation CoPilot RAG service

使用 Agent 查询官方 Plant Simulation 文档前，先启动 CoPilot RAG 服务。以下两种方式任选其一：

Start the CoPilot RAG service before asking the Agent to search official Plant Simulation documentation. Choose either method below:

1. **从 Plant Simulation 客户端启动 / Start from the Plant Simulation client.** 打开 Plant Simulation 2606，在客户端中打开 Copilot-Full 的 Copilot 面板/弹窗，并按界面提示启动或连接服务。确保已在 Copilot-Full 中配置 provider；服务就绪后，`http://127.0.0.1:8002/health` 应返回 `agent_ready: true`。

    Open Plant Simulation 2606, open the Copilot-Full panel or dialog, and follow the prompts to start or connect to the service. Make sure a provider is configured. When ready, `http://127.0.0.1:8002/health` should return `agent_ready: true`.

2. **运行仓库启动脚本 / Use the repository launcher.** 先检查并按本机安装情况编辑 [`config/local.properties`](config/local.properties) 中的 `COPILOT_DIR`、`COPILOT_PYTHON`、服务入口及端口等参数。

    Review and update `COPILOT_DIR`, `COPILOT_PYTHON`, the service entry point, port, and other settings in [`config/local.properties`](config/local.properties) for your installation.

| 键 / Key | 默认值 / Default | 用途 / Purpose |
| --- | --- | --- |
| `COPILOT_DIR` | `C:\ProgramFiles\Siemens\TecnomatixPlantSimulation2606\Copilot` | CoPilot 运行时根目录 / CoPilot runtime root |
| `COPILOT_PYTHON` | `python-3.14.5-embed\pythonw.exe` | 内嵌 Python（相对 `COPILOT_DIR`）/ Embedded Python (relative to `COPILOT_DIR`) |
| `COPILOT_SERVICE_FILE` | `copilot_service.py` | 服务入口文件 / Service entry file |
| `COPILOT_SERVICE` | `copilot_service:app` | uvicorn 的 `module:app` / uvicorn `module:app` target |
| `COPILOT_HOST` / `COPILOT_PORT` | `127.0.0.1` / `8002` | 知识层 HTTP 端点 / Knowledge-layer HTTP endpoint |
| `COPILOT_LOG_SUBDIR` / `COPILOT_LOG_FILE` | `logs` / `copilot.log` | 日志位置（相对 `COPILOT_DIR`）/ Log path (relative to `COPILOT_DIR`) |

保存配置后，在命令提示符（`cmd.exe`）中运行仓库的配置加载器，检查配置文件是否完整、可解析：

After saving the settings, run the repository configuration loader in Command Prompt (`cmd.exe`) to verify that the configuration is complete and parseable:

```cmd
call "C:\Users\z004bjuu\Documents\skills_of_plant_simulation\config\load_paths.cmd"
if errorlevel 1 (echo Configuration load failed / 配置加载失败) else (echo Configuration loaded / 配置加载成功：%COPILOT_DIR%)
```

确认显示“配置加载成功”后，再双击启动脚本。若加载器报告缺少配置项，请修正 `local.properties` 后重新运行。`load_paths.cmd` 只在当前命令提示符会话中设置变量；`start_copilot.bat` 会自行再次读取配置文件。

After the loader reports success, double-click the launcher. If it reports a missing setting, fix `local.properties` and run it again. `load_paths.cmd` sets variables only in the current Command Prompt session; `start_copilot.bat` reads the configuration file again on its own.

然后双击 [`Copilot-using/start_copilot.bat`](Copilot-using/start_copilot.bat) 启动服务。窗口会显示启动日志并等待服务就绪；通常约需 120 秒，初始化较慢时会更久，请耐心等待，不要提前关闭窗口或重复启动。脚本最多等待 480 秒，并在完成时显示 `/health` 结果。

Then double-click [`Copilot-using/start_copilot.bat`](Copilot-using/start_copilot.bat). The window streams startup logs and waits for readiness. Startup usually takes about 120 seconds and may take longer; be patient, and do not close the window or launch it again prematurely. The script waits for up to 480 seconds and displays the `/health` result when finished.




改完直接生效，两条链路都会跟着变：

Changes take effect immediately and are used by both access paths:

- **cmd.exe 侧 / cmd.exe:** `config/load_paths.cmd` parses the file and is called by `start_copilot.bat` and `stop_copilot.bat`. Missing keys cause an error and stop startup.
- **Python 侧 / Python:** `Copilot-using/copilot_config.py` reads the same file and exposes `get(key)` with defaults. Both `ask_copilot.py` and `skills/local-get-rag-knowledge/scripts/rag_ask.py` use it for the service endpoint.

无论采用哪种方式，都以健康检查确认服务已就绪：

Whichever startup method you use, verify the service is ready with the health check:

```bash
python skills/local-get-rag-knowledge/scripts/rag_ask.py --health
```

确认输出中的 `agent_ready` 为 `true` 后，再让 Agent 发起知识查询。若服务未就绪，检查 Copilot-Full 的 provider 配置及 `config/local.properties`，并查看 `%COPILOT_DIR%\logs\copilot.log`。

Ask the Agent to query documentation only after `agent_ready` is `true`. If the service is not ready, check the Copilot-Full provider settings, `config/local.properties`, and `%COPILOT_DIR%\logs\copilot.log`.



#### 加载 Agent 和 Skills / Load the Agent and Skills

先在 AI 工具中打开本仓库根目录 `skills_of_plant_simulation/` 作为工作区。Agent 的说明文件是 `agent/plant-simulation.agent.md`；各项技能及其操作脚本、示例和参考资料位于 `skills/<技能名>/`。技能不是需要单独安装的程序包，Agent 根据任务读取相应的 `SKILL.md`，再按其中说明调用仓库脚本。

Open the repository root, `skills_of_plant_simulation/`, as the workspace in your AI tool. The Agent definition is `agent/plant-simulation.agent.md`; skills, scripts, examples, and references are under `skills/<skill-name>/`. Skills are not packages to install: the Agent reads the relevant `SKILL.md` and follows its instructions to run repository scripts.

1. **选择或注册 Agent / Select or register the Agent.** 在工具的 Agent / Custom Agent 选择器中选择 Plant Simulation Agent；若工具支持手动指定文件，就指定 `agent/plant-simulation.agent.md`。如果工具只自动扫描约定目录，需要把该文件注册到工具支持的自定义 Agent 目录，或在工具设置中添加此文件所在位置。不要假设工具会自动扫描仓库的 `agent/` 目录。

    Select Plant Simulation Agent in the Agent/Custom Agent picker, or specify `agent/plant-simulation.agent.md` directly. If the tool scans only conventional directories, register the file in its supported custom-agent location. Do not assume it automatically scans this repository's `agent/` directory.
2. **让工具能读取 Skills / Make the skills available.** 配置工具把仓库根目录作为上下文，并允许读取 `skills/` 下的文件。执行任务时，Agent 会按路由表打开对应的 `skills/<技能名>/SKILL.md`；不要只把技能名称列表交给模型而不提供技能文件内容。

    Set the repository root as context and allow the tool to read files under `skills/`. The Agent should open the routed `skills/<skill-name>/SKILL.md`; names alone are not enough.
3. **启用必要的本地工具 / Enable required local tools.** 允许 AI 工具在仓库根目录读取文件并执行终端命令。RAG 问答需要访问本机 CoPilot 服务（默认 `127.0.0.1:8002`）；模型操作需要运行 Python 脚本并连接 Plant Simulation（默认 `127.0.0.1:50007`）。按工具的安全提示授予所需权限；首次执行会改变模型状态的操作时仍应由用户明确提出。

    Allow the AI tool to read repository files and run terminal commands from the repository root. RAG queries need access to CoPilot at `127.0.0.1:8002`; model operations need Python execution and Plant Simulation at `127.0.0.1:50007`. Follow the tool's permission prompts, and require an explicit user request before changing model state.
4. **确认加载成功 / Verify loading.** 先让 Agent 报出它读取的 Agent 文件路径，并针对一个示例任务指出将先读哪个 `SKILL.md`。它应能访问仓库内相应脚本；若报文件不存在，先检查工作区根目录和工具的 Agent / Skills 搜索路径。

    Ask the Agent to report the Agent file it read and identify which `SKILL.md` it would read for a sample task. If files are not found, check the workspace root and the tool's Agent/Skills search paths.

不同工具的自动发现约定并不完全相同：OpenClaude、Claude Code、GitHub Copilot 和 OpenClaw 可能使用不同的 Agent / Skills 配置目录或选择方式。若工具未识别仓库现有目录，按上面步骤手动选择或注册 Agent，并将 `skills/` 配置为技能来源；也可以把下面的指令发给当前会话，要求它显式读取这些文件：

Agent/Skills discovery differs across OpenClaude, Claude Code, GitHub Copilot, and OpenClaw. If the tool does not recognize these repository folders, register the Agent and configure `skills/` as described above, or give the current session the following instruction to load the files explicitly:

```text
请以当前仓库为工作区。先完整读取 agent/plant-simulation.agent.md，并遵守其中的路由、工作流程和任务边界。处理 Plant Simulation / SimTalk 请求时，按 Agent 路由表选择技能，先完整读取对应的 skills/<技能名>/SKILL.md，再遵循该技能要求读取 references、examples 并调用脚本。所有相对路径都以仓库根目录为基准。如果任务需要读取或控制模型，而用户尚未提供 .spp 模型文件的完整路径，先询问路径；收到后使用仓库 COM 启动脚本打开 Plant Simulation 并加载该模型，注入 simtalkclaude-client/SimtalkClaude.pslib，再执行 ping 验证链路，成功后才能进行模型操作。不要猜路径、绕过前置检查或声称未验证的操作已成功。如果无法读取文件或执行脚本，请明确报告。
```

English version:

```text
Use the current repository as the workspace. Read agent/plant-simulation.agent.md in full and follow its routing, workflow, and task boundaries. For Plant Simulation or SimTalk requests, select a skill from the Agent routing table, read the relevant skills/<skill-name>/SKILL.md in full, and follow its instructions for any references, examples, and scripts. Resolve relative paths from the repository root. If a task requires model access or control and the user has not provided the full path to an .spp file, ask for it first. Once provided, use the repository COM launcher to open Plant Simulation, load the model, inject simtalkclaude-client/SimtalkClaude.pslib, and verify the connection with the ping skill before any model operation. Do not guess paths, skip prerequisites, or claim unverified success. Clearly report if files cannot be read or scripts cannot be run.
```

#### 提供并启动 Plant Simulation 模型 / Provide and start a Plant Simulation model

如果路线 A 的任务需要读取或控制 Plant Simulation 模型，必须先给 Agent 一个 `.spp` 模型文件的完整路径。若本轮对话还没有提供路径，Agent 应先询问，不要猜测路径，也不要声称已经连接或控制模型。拿到路径后，Agent 使用仓库的 COM 启动脚本打开 Plant Simulation、加载该模型并注入 `SimtalkClaude.pslib`，然后运行 ping 技能确认 TCP 链路可用；确认成功后才能继续读取或操作模型。

For Route A tasks that need to inspect or control a Plant Simulation model, provide the Agent with the full path to an `.spp` file first. If the path has not been provided, the Agent must ask for it rather than guess or claim it is connected. Once provided, the Agent uses the repository COM launcher to open Plant Simulation, load the model, inject `SimtalkClaude.pslib`, and run the ping skill. Model access can continue only after the ping succeeds.

启动命令模板（将 `<模型文件完整路径>` 替换为用户提供的实际路径）：

Command template (replace `<full-model-path>` with the path provided by the user):

```powershell
.venv\Scripts\python skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py `
  --model "<full-path-to-model.spp>" `
  --simtalkclaudefile "simtalkclaude-client/SimtalkClaude.pslib" `
  --port 50007 --print-pid
```

脚本成功退出后，还必须执行 `python skills/local-simtalk-ping/scripts/simtalk_send.py`；只有 ping 成功，才算 Plant Simulation 已准备好供后续技能控制。启动需要的模型路径不可省略。

After the launcher exits successfully, run `python skills/local-simtalk-ping/scripts/simtalk_send.py`. Plant Simulation is ready for subsequent skills only when ping succeeds. The model path is required.


Agent 会按 `agent/plant-simulation.agent.md` 的路由表自动选技能，标准流程是 6 步：

The Agent selects skills using the routing table in `agent/plant-simulation.agent.md`. Its standard workflow has six steps:

1. **先查 RAG / Query RAG first** —— 带上你的原始问题 + 相关上下文摘要 / Include the original question and relevant context.
2. **读 `answer` / `citations` / `metrics` / Review the response** —— 判断是纯知识问题还是要动模型 / Decide whether the task needs model operations.
3. **按依赖执行技能 / Run required skills in order** —— 启动 → ping → syntax check → 执行 → 读结构 / Start → ping → syntax check → execute → inspect.
4. **把新增结果回交 RAG / Send new evidence back to RAG** —— 让它基于实测结果再解释一遍 / Ask it to interpret the measured results.
5. **按进展迭代 / Iterate as needed** —— 没有必要的新动作就停 / Stop when no relevant action remains.
6. **综合收尾 / Summarize** —— 明确区分「文档知识」/「实测结果」/「推论」 / Distinguish documentation, measured results, and inference.

**Agent 侧两条硬规矩 / Two mandatory Agent rules**（写进了 agent 文件，务必遵守 / defined in the Agent file）：

- RAG **必须**走 `skills/local-get-rag-knowledge/scripts/rag_ask.py` wrapper，**不要**直接调 `ask_copilot.py`——后者会把 SSE token 流持续打到 stdout，污染上下文。 / Always use the `rag_ask.py` wrapper; do not call `ask_copilot.py` directly, because its SSE token stream clutters the Agent context.
- 提问前先做 `/health` 探测。服务冷启动时直接发 `/query/stream` 会撞上连接挂死。 / Check `/health` before querying. Sending `/query/stream` while the service is still starting may hang.

Agent 端 timeout 建议 **≥ 120 s**（复杂问题实测 30–90 s）。 / Set the Agent timeout to **at least 120 seconds**; complex queries typically take 30–90 seconds.

---

### 端到端完整演练 / End-to-end walkthrough

从零跑通「查文档 → 起 PS → 验证 → 执行 → 读回」：

Run the complete flow from documentation lookup to model startup, verification, execution, and result retrieval:
```bash
# ① Query the knowledge layer
cmd //c "Copilot-using\start_copilot.bat"
python skills/local-get-rag-knowledge/scripts/rag_ask.py --health
python skills/local-get-rag-knowledge/scripts/rag_ask.py "How do I create a Buffer in SimTalk?"

# ② Start Plant Simulation and inject the bridge library
.venv\Scripts\python skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model "<full-path-to-model.spp>" --simtalkclaudefile "simtalkclaude-client/SimtalkClaude.pslib" --print-pid

# ③ Verify the connection
python skills/local-simtalk-ping/scripts/simtalk_send.py

# ④ Check syntax, then execute
python skills/local-simtalk-checksyntax/scripts/simtalk_send.py 'var n: integer := 3; print n'
python skills/local-simtalk-runsimtalk/scripts/simtalk_runsimtalk.py 'print("hello")'

# ⑤ Read the results
python skills/local-simtalk-read-rootfolder/scripts/simtalk_readrootfolder.py
python skills/local-simtalk-read-console/scripts/simtalk_readlog.py

# ⑥ Stop the service
cmd //c "Copilot-using\stop_copilot.bat"
```

---

### 常见任务速查 / Common tasks

| 我想…… / Task | 命令 / Command |
| --- | --- |
| 查 SimTalk 某个对象/方法的官方用法 / Look up official SimTalk documentation | `rag_ask.py "How do I use <Object>?"` |
| 确认服务活着 / Check service health | `rag_ask.py --health` |
| 起 PS 并装上桥接库 / Start PS and load the bridge | `start_plant_simulation.py --model <x.spp> --simtalkclaudefile simtalkclaude-client/SimtalkClaude.pslib` |
| 确认 PS 侧可连 / Test the PS connection | `local-simtalk-ping/scripts/simtalk_send.py` |
| 试一段 SimTalk 语法（不执行）/ Check SimTalk syntax without execution | `local-simtalk-checksyntax/scripts/simtalk_send.py '<code>'` |
| 真的执行一段 SimTalk / Execute SimTalk | `local-simtalk-runsimtalk/scripts/simtalk_runsimtalk.py '<code>'` |
| 看模型里有什么对象 / List model objects | `local-simtalk-read-rootfolder/scripts/simtalk_readrootfolder.py` |
| 看某个 Method 写了什么 / Read a Method's source | `local-simtalk-read-program/scripts/simtalk_readprogram.py --methodpath ".Models.X.init"` |
| 看 Console 里的输出 / Read Console output | `local-simtalk-read-console/scripts/simtalk_readlog.py` |

---

## 技能一览 / Skills overview

技能位于 `skills/`，覆盖 RAG 问答、PS 启动、链路与语法检查、SimTalk 执行，以及模型结构、源码、Console 和自定义属性读取。路由和具体使用方式见各技能的 `SKILL.md` 与 [Agent 配置](agent/plant-simulation.agent.md)。

Skills under `skills/` cover RAG queries, Plant Simulation startup, connection and syntax checks, SimTalk execution, and model structure, source, Console, and custom-attribute reads. See each `SKILL.md` and the [Agent configuration](agent/plant-simulation.agent.md) for routing and instructions.

## TCP 帧协议 / TCP frame protocol

请求与响应均为 JSON，并以 `||END||` 结束。帧类型包括 `ping`、`simtalk_syntax`、`simtalk_run` 和各类 `read*`。详细参数由对应技能脚本处理。

Requests and responses are JSON frames terminated by `||END||`. Frame types include `ping`, `simtalk_syntax`, `simtalk_run`, and the `read*` operations. The corresponding skill scripts handle the parameters.

### 退出码约定 / Exit codes

`0` 表示成功；`1`–`3` 表示连接或传输错误；`10`–`12` 表示技能执行或语法检查失败。只读技能可能以 `20` 成功退出，判断结果时请检查 stdout。具体定义见各技能说明。

`0` indicates success; `1`–`3` indicate connection or transport errors; `10`–`12` indicate skill execution or syntax-check failures. Read-only skills may exit with `20` on success, so check stdout. See each skill for details.

---


## 硬规则与已知坑 / Rules and caveats

- 区分 RAG 文档答复与模型实测结果；调用 RAG 前先检查 `/health`。 / Distinguish RAG documentation from model-tested results; check `/health` before querying RAG.
- `simtalk_syntax` 不会发现 GUI 弹窗风险；避免在自动执行中使用 `prompt()`、`infoBox()` 等函数。 / Syntax checks do not detect GUI dialogs; avoid functions such as `prompt()` and `infoBox()` in automated runs.
- 执行代码前确认属性已声明；模型修改必须符合用户明确要求。 / Confirm attributes are declared before execution; modify models only when explicitly requested.
- 以技能文档定义的结果字段和退出码判断成功。Console 输出在 Plant Simulation GUI 中查看。 / Use each skill's documented result fields and exit codes. View Console output in the Plant Simulation GUI.
- COM 启动异常时检查是否存在多个 PS 实例。故障排查见各技能的 `references/`。 / If COM startup fails, check for multiple Plant Simulation instances. See each skill's `references/` for troubleshooting.

---

## 文档索引 / Documentation index

详细说明按需查看： / See these files for details:

- Agent 路由 / Agent routing: [`agent/plant-simulation.agent.md`](agent/plant-simulation.agent.md)
- Copilot 配置 / Copilot configuration: [`config/local.properties`](config/local.properties)
- 技能操作与故障排查 / Skill instructions and troubleshooting: `skills/<技能名>/SKILL.md` and the corresponding `references/`
- PS 桥接库 / Plant Simulation bridge: [`simtalkclaude-client/SimtalkClaude.pslib`](simtalkclaude-client/SimtalkClaude.pslib)

---

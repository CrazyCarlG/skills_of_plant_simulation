# Plant Simulation Skills 2.0

本项目通过 Agent 调用 Plant Simulation Copilot RAG 查询官方文档，并通过本地桥接在 Plant Simulation 中检查或执行 SimTalk。

| 部分 | 位置 / 默认端点 | 用途 |
| --- | --- | --- |
| Agent | `agent/plant-simulation.agent.md` | 路由任务并编排技能 |
| Skills | `skills/` | RAG 查询、启动、检查、执行及模型读取 |
| Copilot RAG | `127.0.0.1:8002` | 官方知识检索与问答 |
| Plant Simulation bridge | `127.0.0.1:50007` | 连接运行中的模型 |

## 环境要求

- Windows、Plant Simulation 2606，以及已注册的 COM 接口。
- Python 3.13 虚拟环境；COM 启动脚本需要 `pywin32`。
- Plant Simulation Copilot-Full 和已配置的 provider，见 [安装视频](Copilot-FULL-Setup.mp4)。
- 支持 Agent/Skills 的 CLI 工具，例如 OpenClaude、GitHub Copilot 或 OpenClaw。
- 需要控制模型时，准备 `.spp` 文件。安装与检查步骤见下方 How to use。

---

## 使用指南（How to use）



#### 一次性准备

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


#### 启动 Plant Simulation CoPilot RAG 服务

使用 Agent 查询官方 Plant Simulation 文档前，先启动 CoPilot RAG 服务。以下两种方式任选其一：

1. **从 Plant Simulation 客户端启动。** 打开 Plant Simulation 2606，在客户端中打开 Copilot-Full 的 Copilot 面板/弹窗，并按界面提示启动或连接服务。确保已在 Copilot-Full 中配置 provider；服务就绪后，`http://127.0.0.1:8002/health` 应返回 `agent_ready: true`。

2. **运行仓库启动脚本。** 先检查并按本机安装情况编辑 [`config/local.properties`](config/local.properties) 中的 `COPILOT_DIR`、`COPILOT_PYTHON`、服务入口及端口等参数。

| 键 | 默认值 | 用途 |
| --- | --- | --- |
| `COPILOT_DIR` | `C:\ProgramFiles\Siemens\TecnomatixPlantSimulation2606\Copilot` | CoPilot 运行时根目录 |
| `COPILOT_PYTHON` | `python-3.14.5-embed\pythonw.exe` | 内嵌 Python（相对 `COPILOT_DIR`） |
| `COPILOT_SERVICE_FILE` | `copilot_service.py` | 服务入口文件 |
| `COPILOT_SERVICE` | `copilot_service:app` | uvicorn 的 `module:app` |
| `COPILOT_HOST` / `COPILOT_PORT` | `127.0.0.1` / `8002` | 知识层 HTTP 端点 |
| `COPILOT_LOG_SUBDIR` / `COPILOT_LOG_FILE` | `logs` / `copilot.log` | 日志位置（相对 `COPILOT_DIR`） |

保存配置后，在命令提示符（`cmd.exe`）中运行仓库的配置加载器，检查配置文件是否完整、可解析：

```cmd
call "C:\Users\z004bjuu\Documents\skills_of_plant_simulation\config\load_paths.cmd"
if errorlevel 1 (echo 配置加载失败) else (echo 配置加载成功：%COPILOT_DIR%)
```

确认显示“配置加载成功”后，再双击启动脚本。若加载器报告缺少配置项，请修正 `local.properties` 后重新运行。`load_paths.cmd` 只在当前命令提示符会话中设置变量；`start_copilot.bat` 会自行再次读取配置文件。

然后双击 [`Copilot-using/start_copilot.bat`](Copilot-using/start_copilot.bat) 启动服务。窗口会显示启动日志并等待服务就绪；通常约需 120 秒，初始化较慢时会更久，请耐心等待，不要提前关闭窗口或重复启动。脚本最多等待 480 秒，并在完成时显示 `/health` 结果。




改完直接生效，两条链路都会跟着变：

- **cmd.exe 侧** —— `config/load_paths.cmd` 用 `for /f` 解析，被 `start_copilot.bat` / `stop_copilot.bat` `call`。缺键时脚本报错退出，不会带着半截路径往下跑。
- **Python 侧** —— `Copilot-using/copilot_config.py` 解析同一份文件，提供 `get(key)`（带默认值兜底）。`ask_copilot.py` 与 `skills/local-get-rag-knowledge/scripts/rag_ask.py` 都从这里取 `BASE`，不再各自硬编码 `8002` 或机器绝对路径。

无论采用哪种方式，都以健康检查确认服务已就绪：

```bash
python skills/local-get-rag-knowledge/scripts/rag_ask.py --health
```

确认输出中的 `agent_ready` 为 `true` 后，再让 Agent 发起知识查询。若服务未就绪，检查 Copilot-Full 的 provider 配置及 `config/local.properties`，并查看 `%COPILOT_DIR%\logs\copilot.log`。



#### 加载 Agent 和 Skills

先在 AI 工具中打开本仓库根目录 `skills_of_plant_simulation/` 作为工作区。Agent 的说明文件是 `agent/plant-simulation.agent.md`；各项技能及其操作脚本、示例和参考资料位于 `skills/<技能名>/`。技能不是需要单独安装的程序包，Agent 根据任务读取相应的 `SKILL.md`，再按其中说明调用仓库脚本。

1. **选择或注册 Agent。** 在工具的 Agent / Custom Agent 选择器中选择 Plant Simulation Agent；若工具支持手动指定文件，就指定 `agent/plant-simulation.agent.md`。如果工具只自动扫描约定目录，需要把该文件注册到工具支持的自定义 Agent 目录，或在工具设置中添加此文件所在位置。不要假设工具会自动扫描仓库的 `agent/` 目录。
2. **让工具能读取 Skills。** 配置工具把仓库根目录作为上下文，并允许读取 `skills/` 下的文件。执行任务时，Agent 会按路由表打开对应的 `skills/<技能名>/SKILL.md`；不要只把技能名称列表交给模型而不提供技能文件内容。
3. **启用必要的本地工具。** 允许 AI 工具在仓库根目录读取文件并执行终端命令。RAG 问答需要访问本机 CoPilot 服务（默认 `127.0.0.1:8002`）；模型操作需要运行 Python 脚本并连接 Plant Simulation（默认 `127.0.0.1:50007`）。按工具的安全提示授予所需权限；首次执行会改变模型状态的操作时仍应由用户明确提出。
4. **确认加载成功。** 先让 Agent 报出它读取的 Agent 文件路径，并针对一个示例任务指出将先读哪个 `SKILL.md`。它应能访问仓库内相应脚本；若报文件不存在，先检查工作区根目录和工具的 Agent / Skills 搜索路径。

不同工具的自动发现约定并不完全相同：OpenClaude、Claude Code、GitHub Copilot 和 OpenClaw 可能使用不同的 Agent / Skills 配置目录或选择方式。若工具未识别仓库现有目录，按上面步骤手动选择或注册 Agent，并将 `skills/` 配置为技能来源；也可以把下面的指令发给当前会话，要求它显式读取这些文件：

```text
请以当前仓库为工作区。先完整读取 agent/plant-simulation.agent.md，并遵守其中的路由、工作流程和任务边界。处理 Plant Simulation / SimTalk 请求时，按 Agent 路由表选择技能，先完整读取对应的 skills/<技能名>/SKILL.md，再遵循该技能要求读取 references、examples 并调用脚本。所有相对路径都以仓库根目录为基准。如果任务需要读取或控制模型，而用户尚未提供 .spp 模型文件的完整路径，先询问路径；收到后使用仓库 COM 启动脚本打开 Plant Simulation 并加载该模型，注入 simtalkclaude-client/SimtalkClaude.pslib，再执行 ping 验证链路，成功后才能进行模型操作。不要猜路径、绕过前置检查或声称未验证的操作已成功。如果无法读取文件或执行脚本，请明确报告。
```

加载完成后

#### 提供并启动 Plant Simulation 模型

如果路线 A 的任务需要读取或控制 Plant Simulation 模型，必须先给 Agent 一个 `.spp` 模型文件的完整路径。若本轮对话还没有提供路径，Agent 应先询问，不要猜测路径，也不要声称已经连接或控制模型。拿到路径后，Agent 使用仓库的 COM 启动脚本打开 Plant Simulation、加载该模型并注入 `SimtalkClaude.pslib`，然后运行 ping 技能确认 TCP 链路可用；确认成功后才能继续读取或操作模型。

启动命令模板（将 `<模型文件完整路径>` 替换为用户提供的实际路径）：

```powershell
.venv\Scripts\python skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py `
  --model "<模型文件完整路径>" `
  --simtalkclaudefile "simtalkclaude-client/SimtalkClaude.pslib" `
  --port 50007 --print-pid
```

脚本成功退出后，还必须执行 `python skills/local-simtalk-ping/scripts/simtalk_send.py`；只有 ping 成功，才算 Plant Simulation 已准备好供后续技能控制。启动需要的模型路径不可省略。


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

### 端到端完整演练

从零跑通「查文档 → 起 PS → 验证 → 执行 → 读回」：
Agent将遵从如下流程完成任务
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

技能位于 `skills/`，覆盖 RAG 问答、PS 启动、链路与语法检查、SimTalk 执行，以及模型结构、源码、Console 和自定义属性读取。路由和具体使用方式见各技能的 `SKILL.md` 与 [Agent 配置](agent/plant-simulation.agent.md)。

---

## TCP 帧协议（执行层）

请求与响应均为 JSON，并以 `||END||` 结束。帧类型包括 `ping`、`simtalk_syntax`、`simtalk_run` 和各类 `read*`。详细参数由对应技能脚本处理。

### 退出码约定

`0` 表示成功；`1`–`3` 表示连接或传输错误；`10`–`12` 表示技能执行或语法检查失败。只读技能可能以 `20` 成功退出，判断结果时请检查 stdout。具体定义见各技能说明。

---


## 硬规则与已知坑

- 区分 RAG 文档答复与模型实测结果；调用 RAG 前先检查 `/health`。
- `simtalk_syntax` 不会发现 GUI 弹窗风险；避免在自动执行中使用 `prompt()`、`infoBox()` 等函数。
- 执行代码前确认属性已声明；模型修改必须符合用户明确要求。
- 以技能文档定义的结果字段和退出码判断成功。Console 输出在 Plant Simulation GUI 中查看。
- COM 启动异常时检查是否存在多个 PS 实例。故障排查见各技能的 `references/`。

---

## 文档索引

详细说明按需查看：

- Agent 路由：[`agent/plant-simulation.agent.md`](agent/plant-simulation.agent.md)
- Copilot 配置：[`config/local.properties`](config/local.properties)
- 技能操作与故障排查：`skills/<技能名>/SKILL.md` 及对应 `references/`
- PS 桥接库：[`simtalkclaude-client/SimtalkClaude.pslib`](simtalkclaude-client/SimtalkClaude.pslib)

---

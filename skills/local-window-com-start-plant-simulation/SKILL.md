---
name: local-window-com-start-plant-simulation
description: 在本机 Windows 通过 COM `Tecnomatix.PlantSimulation.RemoteControl.26.6` 启动 Plant Simulation 2606、加载 `.spp` 模型、注入 `SimtalkClaude.pslib`、把 SocketServer 端口改成给定值,并把 console log 落盘到 `log_dir`。触发场景:用户说"启动 Plant Simulation"、"打开这个 .spp 模型"、"把 SimtalkClaude 注入模型"、"先把 server 跑起来"、"50007 端口起一个 PS 进程"、"start PS for me"。本技能是 `local-simtalk-execution` / `local-simtalk-write-simtalk` 等下游技能的**前置条件**——必须先用本技能把 PS 进程 + SimtalkClaude socket 跑起来,下游技能才能通过 TCP 发消息。本技能只管"启动 + 加载 + 注入 + 配置端口 + 日志落盘"五件事,**不**执行业务 SimTalk,**不**维护 socket 通信。
---

# local-window-com-start-plant-simulation

把一台本机 Windows 上的 Plant Simulation 2606 进程通过 COM 拉起来:加载一个用户给定的 `.spp` 模型,把用户指定的 `SimtalkClaude.pslib` 用 `basis.loadObjectAs` 注入,然后把 `.SimtalkClaude.Main.SocketServer.mysocket.port` 设到指定端口。所有 PS console 输出经 `OpenConsoleLogFile` 落到 `--log-dir` 下的 `run_<时间戳>.txt`。

> 本技能**只负责把 PS 进程 + SimtalkClaude socket 准备好**。不执行任何业务 SimTalk、不解析模型结构、不维护 socket 连接、不重试 COM 错误——这些属于下游技能(`local-simtalk-execution` / `local-simtalk-write-simtalk` 等)或调用方 agent。

## 工作前提 / Prerequisites

- **Windows 操作系统**(本技能通过 `win32com.client` 调用 COM;Linux/macOS 不支持)。
- **Plant Simulation 2606 已安装**且 COM 类 `Tecnomatix.PlantSimulation.RemoteControl.26.6` 已注册。验证:`python3 -c "import win32com.client; win32com.client.Dispatch('Tecnomatix.PlantSimulation.RemoteControl.26.6')"` 不报错。
- **Python `pywin32` 已装**:`pip install pywin32`(Windows-only 包)。
- 用户提供四类输入:**`.spp` 模型路径**、**`SimtalkClaude.pslib` 路径**(必传)、**log 目录**(必传,须可写)、**SocketServer 端口**(默认 50007)。

## 硬规则（必读）

> 所有"必须 / 禁止 / 会挂"的铁律集中在 `references/lifelines.md`。SKILL.md / `examples/` / `cli-args.md` 一律用简短引用,不重复展开。

## 任务流程 / Workflow

1. 校验 `--model` 路径存在(脚本内 `FileNotFoundError` → 退出码 4)。
2. 校验 `--port` 是 1-65535 整数(`type=int` + `ValueError` → 退出码 2)。
3. 校验 `--simtalkclaudefile` 路径存在(argparse `required=True` + 脚本内 `FileNotFoundError` → 退出码 2 / 4)。
4. 校验 `--log-dir` 已传(argparse `required=True`);创建目录(不存在则 `os.makedirs`)。
5. `Dispatch("Tecnomatix.PlantSimulation.RemoteControl.26.6")`,按需 `SetVisible` / `SetNoMessageBox`。
6. `OpenConsoleLogFile(log_dir/run_<时间戳>.txt)`。
7. `LoadModel(<model>)` + `SetTrustModels(True)`。
8. `ExecuteSimTalk('basis.loadObjectAs("<path>","", true, false)')`(注入 SimtalkClaude 库)。
9. `ExecuteSimTalk('.SimtalkClaude.Main.SocketServer.mysocket.port:=<port>')`。
10. (可选 `--wait-ready`) TCP 轮询 `127.0.0.1:<port>` 直到连上或超时,详见 `references/cli-args.md`。
11. (可选 `--print-pid`) `tasklist` 查 `Plant Simulation.exe` PID 打到 stdout,详见 `references/cli-args.md`。
12. 打印成功消息,退出码 0。

## 关键文件 / Key Files

- `scripts/start_plant_simulation.py` — 本技能唯一脚本(启动 + 注入 + 改端口 + 可选探活 + 可选 PID 查询)。
- `examples/launch-and-probe.md` — 完整 e2e 示例:本脚本启动 + 下游 `local-simtalk-execution` 的 ping 探针。
- `examples/smoke-test.md` — 仅本脚本的最小冒烟流程(不含下游 ping),用于快速验证环境。
- `references/cli-args.md` — 所有 CLI flag + 退出码详解。
- `references/lifelines.md` — 硬规则 / "会挂死"的坑(必读)。

## 故障排查 / Troubleshooting

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `pywin32 (win32com) is required` | 没装 pywin32 | `pip install pywin32`(只支持 Windows) |
| `COMError ... hresult=0x80040154` | 类未注册(PS 未装 / COM 没注册) | 装 PS 2606,或 `regsvr32 "<PS安装目录>\\Tecnomatix.PlantSimulation.RemoteControl.dll"` |
| `COMError ... hresult=0x80080005` | COM 服务端启动失败(PS 单例被占) | 任务管理器关掉旧 `Plant Simulation.exe`,或 `taskkill /IM "Plant Simulation.exe" /F` |
| 退出码 4 + `Model file not found` | `--model` 路径不对 | 检查路径是否存在,绝对路径更稳 |
| 退出码 4 + `SimtalkClaude library not found` | `--simtalkclaudefile` 路径不对 | 同上 |
| 退出码 2 + 缺 `--simtalkclaudefile` | argparse 强制要求未传 | 传 `<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib` 路径 |
| 退出码 2 + 缺 `--log-dir` | argparse 强制要求未传 | 传一个可写目录(如 `C:\logs` 或自选路径) |
| 退出码 2 + `Port must be in 1..65535` | `--port` 越界 | 传 1-65535 整数 |
| 退出码 3 + `socket readiness check failed` | `--wait-ready` 超时 | 见 `references/lifelines.md` §1 + §5 |
| 模型加载报错但 SetNoMessageBox 把弹窗吞了 | 关了消息框 | 排查期传 `--allow-message-box` 看弹窗 |
| 退出码 3 + 提示`taskkill` | 多个 PS 实例并存(详见 `lifelines.md` §2) | 关掉旧实例,只留一个 |

## Logging / 日志

本技能**不写 `log/`** —— 它是一次性启动脚本,无 session 语义。每次运行的 PS console 输出经 `--log-dir/run_<时间戳>.txt` 落盘。

若需在 `log/` 记录**整个工作流**(包含本脚本启动 + 下游探针),由调用方 agent (`plant-simulation-expert`) 写,详见 `log/CONTRIBUTING.md`。

## 知识库路径 / Knowledge Paths

- SimtalkClaude 服务端实现(注入模型、被下游 socket 协议调用):`04-simtalkclaude-client/`
- Plant Simulation COM 接口参考:`01-plantsimulation-knowledge/01-plant-simulation-help/communication-interface/COM/`
- 下游 TCP socket 协议 / 消息 schema / 服务端 quirks:`skills/local-simtalk-execution/references/`

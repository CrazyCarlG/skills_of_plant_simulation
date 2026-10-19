---
name: local-window-com-start-plant-simulation
description: 在本机 Windows 通过 COM `Tecnomatix.PlantSimulation.RemoteControl.26.6` 启动 Plant Simulation 2606、加载 `.spp` 模型、注入 `SimtalkClaude.pslib`、把 SocketServer 端口改成给定值。触发场景:用户说"启动 Plant Simulation"/"load PS"/"boot PS"/"打开这个 .spp 模型"/"把 SimtalkClaude 注入模型"/"先把 server 跑起来"/"50007 端口起一个 PS 进程"/"start PS for me"/"prepare PS"/"launch ps"/"server up"/"warm up PS"/".spp 加载"/"加载模型"/"PS 起来"/"init ps"/"open the model"/"bring up PS"/"spin up PS"/"preload model"。同义动作归一态(拼写/语序/中英混杂都算命中):"ps boot"/"plant simulation 启动"/"open .spp"/"加载 .spp"/"模型加载"/"PS 进程起来"也算。本技能是 `local-simtalk-execution` / `local-simtalk-write-simtalk` 等下游技能的**前置条件**——必须先用本技能把 PS 进程 + SimtalkClaude socket 跑起来,下游技能才能通过 TCP 发消息。本技能只管"启动 + 加载 + 注入 + 配置端口"四件事,**不**执行业务 SimTalk,**不**维护 socket 通信,**不**落盘 console log。
---

# local-window-com-start-plant-simulation

把一台本机 Windows 上的 Plant Simulation 2606 进程通过 COM 拉起来:加载一个用户给定的 `.spp` 模型,把用户指定的 `SimtalkClaude.pslib` 用 `basis.loadObjectAs` 注入,然后从默认端口 `50007`(或用户指定的起始端口)开始,逐个尝试直到找到空闲 TCP 端口并配置 SocketServer。脚本不落盘任何 PS console log;console 输出由 PS GUI / 用户自行决定怎么收。

> 本技能**只负责把 PS 进程 + SimtalkClaude socket 准备好**。不执行任何业务 SimTalk、不解析模型结构、不维护 socket 连接、不重试 COM 错误——这些属于下游技能(`local-simtalk-execution` / `local-simtalk-write-simtalk` 等)或调用方 agent。

## 快速命中决策树(agent 30 秒判断)

读完下面 4 条 + 3 条反例,决定要不要调本技能。

### ✅ 命中(以下任一信号 → 调本技能)

1. **用户给了 `.spp` 路径**(+ 可选起始端口,默认 50007),且要求"起来" / "加载" / "准备好"。例:"用 UR10.spp 把 PS 起来,端口从 50007 开始"。
2. **用户要做的事依赖于 PS 在某个端口监听**,但 PS 还没起。例:"先起 PS,我后面要发 TCP 命令"。
3. **用户要做的事属于 PS 业务 SimTalk**(查询/修改模型),且没说 PS 已起。例:"帮我查 UR10 里 Buffer 的当前 MU 数"。
4. **下游技能(`local-simtalk-execution` / `local-simtalk-write-simtalk` 等)的前提没满足**——不管用户原话是什么,只要依赖项是 PS socket 就先调本技能。

### ❌ 不命中(以下任一信号 → 不要调本技能,路由给别的)

1. 用户说"**执行** SimTalk 写代码 / 改模型 / 读统计" → 调 `local-simtalk-write-simtalk` / `local-simtalk-execution`,**不**调本技能。
2. 用户说"**关掉** PS" / "杀进程" → 直接 `taskkill /IM "Plant Simulation.exe" /F`,**不**调本技能。
3. 用户在 Linux / macOS → **不**调本技能(只 Windows 支持)。改用对应平台的 PS 启动方式。

### ⚠️ 调用前必查

调之前先问用户 / 看上下文三件事,缺一就问:
- `.spp` 模型路径(必)
- `SimtalkClaude.pslib` 路径(必)
- 端口(可选,默认 50007)

如果用户没说,先问,**别瞎猜**。

## 工作前提 / Prerequisites

- **Windows 操作系统**(本技能通过 `win32com.client` 调用 COM;Linux/macOS 不支持)。
- **Plant Simulation 2606 已安装**且 COM 类 `Tecnomatix.PlantSimulation.RemoteControl.26.6` 已注册。验证:`python3 -c "import win32com.client; win32com.client.Dispatch('Tecnomatix.PlantSimulation.RemoteControl.26.6')"` 不报错。
- **Python `pywin32` 已装**:`pip install pywin32`(Windows-only 包)。
- 用户提供三类输入:**`.spp` 模型路径**、**`SimtalkClaude.pslib` 路径**(必传)、**SocketServer 端口**(默认 50007)。本技能**不**落盘 PS console log——console 输出由 PS GUI / 用户自行决定怎么收。

## 硬规则（必读）

> 所有"必须 / 禁止 / 会挂"的铁律集中在 `references/lifelines.md`。SKILL.md / `examples/` / `cli-args.md` 一律用简短引用,不重复展开。

## 任务流程 / Workflow

1. 校验 `--model` 路径存在(脚本内 `FileNotFoundError` → 退出码 4)。
2. 校验 `--port` 是 1-65535 整数(`type=int` + `ValueError` → 退出码 2),并从该端口起向上扫描第一个可绑定端口(默认起点 50007)。
3. 校验 `--simtalkclaudefile` 路径存在(argparse `required=True` + 脚本内 `FileNotFoundError` → 退出码 2 / 4)。
4. `Dispatch("Tecnomatix.PlantSimulation.RemoteControl.26.6")`,按需 `SetVisible` / `SetNoMessageBox`。
5. `LoadModel(<model>)` + `SetTrustModels(True)`。
6. `ExecuteSimTalk('basis.loadObjectAs("<path>","", true, false)')`(注入 SimtalkClaude 库)。
7. 把找到的第一个可用端口配置到 `.SimtalkClaude.Main.SocketServer.mysocket.port`。
8. (可选 `--print-pid`) `tasklist` 查 `Plant Simulation.exe` PID 打到 stdout,详见 `references/cli-args.md`。
9. 打印成功消息和实际选中的端口,退出码 0。默认从 50007 向上扫描;端口被占用时依次尝试下一个端口,直到找到可用端口或耗尽 65535。

> 本技能成功退出只表示 **COM + 注入 + 改端口** 三步通过,**不**验证 SimtalkClaude socket 已可连。
> 调用方应紧跟一步 `local-simtalk-ping`(发协议级 `{type:"ping"}`),拿到 `result:success` 才视为真正可用。

## 关键文件 / Key Files

- `scripts/start_plant_simulation.py` — 本技能唯一脚本(启动 + 注入 + 改端口 + 可选 PID 查询)。
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
| 退出码 2 + `Port must be in 1..65535` | `--port` 越界 | 传 1-65535 整数 |
| 退出码 0 但 `local-simtalk-ping` 失败 | COM 链路 OK 但 SimtalkClaude 没真起来 | 检查 PS GUI / console;确认 `--simtalkclaudefile` 没拼错路径 |
| 模型加载报错但 SetNoMessageBox 把弹窗吞了 | 关了消息框 | 排查期传 `--allow-message-box` 看弹窗 |
| 退出码 3 + 提示`taskkill` | 多个 PS 实例并存(详见 `lifelines.md` §2) | 关掉旧实例,只留一个 |

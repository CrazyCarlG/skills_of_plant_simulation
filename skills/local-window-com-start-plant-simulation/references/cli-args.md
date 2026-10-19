# CLI 参数详解 — `scripts/start_plant_simulation.py`

> 与 `SKILL.md` 配套;`SKILL.md` 给高层流程,本文件给逐 flag 细节。变更约定:CLI 加新 flag 只改本文件,SKILL.md / examples/ 的引用自动跟上。

## 调用 / Invocation

```bash
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model <path.spp> \
  --simtalkclaudefile <path.pslib> \
  [--port <starting-port>] \
  [--no-visible] \
  [--allow-message-box] \
  [--print-pid]
```

脚本退出码 0 只代表 **COM + 注入 + 改端口** 三步通过,**不**含 socket 验证。
要确认真可用,跟随 `local-simtalk-ping` 发一次协议级 ping。

## 全部 flag / All flags

| Flag | 类型 | 默认 | 必填 | 说明 |
|---|---|---|---|---|
| `-m / --model` | path | 无 | **是** | `.spp` 模型文件路径。`os.path.abspath` 后做 `os.path.isfile` 校验,不存在退出码 4。 |
| `-p / --port` | int | `50007` | 否 | 端口扫描起点。范围 1-65535,越界或非整数退出码 2。从该端口向上逐个 bind 检查,遇占用则尝试下一个,选出第一个可用端口供 SocketServer 监听;若从起点到 65535 全被占用则退出码 2。 |
| `-s / --simtalkclaudefile` | path | 无 | **是** | `SimtalkClaude.pslib` 绝对/相对路径(argparse `required=True`)。脚本会用 `basis.loadObjectAs("<path>","", true, false)` 注入。缺失触发 argparse 报错 + 退出码 2;路径不存在退出码 4。 |
| `--no-visible` | flag | `visible=True` | 否 | 关闭 PS GUI 窗口(`SetVisible(False)`)。CI / 无人值守场景用。 |
| `--allow-message-box` | flag | `no_message_box=True` | 否 | 关闭 `SetNoMessageBox`(允许模型加载失败时弹窗出现)。排查期用。 |
| `--print-pid` | flag | 关 | 否 | 加载完后,用 `tasklist /FI "IMAGENAME eq Plant Simulation.exe"` 查所有 PS 进程的 PID 打到 stdout。用于下游 agent 锁定"自己的" PS 实例。 |

## 退出码 / Exit codes

| 退出码 | 含义 | 触发条件 |
|---|---|---|
| **0** | 成功 | COM Dispatch + LoadModel + 注入 + 改端口 全部成功(socket 验证由调用方用 `local-simtalk-ping` 完成)。 |
| **2** | 参数错 / 端口错 | `--port` 非整数(argparse 层);或 `--port` 不在 1-65535;或起点到 65535 均无可用端口;或 `--simtalkclaudefile` 未传(argparse `required=True`)。 |
| **3** | COM 错 | `pywintypes.com_error`(详细 HRESULT 与 hint 见 `lifelines.md`)。 |
| **4** | 文件不存在 | `--model` 路径找不到;或 `--simtalkclaudefile` 路径找不到。 |
| **5** | 其它未捕获异常 | 兜底;bug 报告时附 stderr。 |

## 输出格式 / Output

**stdout**(成功时):

```
Plant Simulation launched, model loaded, socket port set to <actual-port>.
Plant Simulation PID: [<pid1>, <pid2>, ...]    # 仅 --print-pid 时
```

成功行(`Plant Simulation launched ...`)走 stdout,保持 stdout 只含终态判定信号。socket 验证交给调用方(用 `local-simtalk-ping`)。

**stderr**(失败时,退出码 2/3/4/5):

- 退出码 2:`Error: Port must be in 1..65535, got <port>`、`Error: No available TCP port at or above <port> (maximum is 65535)` 或 argparse `invalid int value: '<port>'`。
- 退出码 3:`COMError: <msg> (hresult=0xHHHHHHHH)` 后跟 hint。
- 退出码 4:`Error: Model file not found: <abs path>` 或 `Error: SimtalkClaude library not found: <abs path>`。
- 退出码 5:`Error: <exception text>`(兜底)。

## 已知交互 / Known interactions

- **退出 0 但 `local-simtalk-ping` 失败**:COM 链路 + 注入 + 改端口 全跑通,但 PS 进程实际
  没起来 SocketServer(或被防病毒/防火墙拦了)。规避:启动前 `netstat -ano | findstr :<port>`
  确认端口空闲;启动后必跑 `local-simtalk-ping`,而不是相信脚本退出码 0。
- **`--print-pid` + 多 PS 实例**:若有多个 `Plant Simulation.exe` 同时跑(违反 `lifelines.md` §2),
  tasklist 会返回多个 PID,脚本会全部打印,不做过滤。
- **`--no-visible` + `--allow-message-box`**:互不冲突,组合后是无 GUI + 有弹窗的 CI 模式,
  详见 `examples/launch-and-probe.md` 的 CI Variant。

# CLI 参数详解 — `scripts/start_plant_simulation.py`

> 与 `SKILL.md` 配套;`SKILL.md` 给高层流程,本文件给逐 flag 细节。变更约定:CLI 加新 flag 只改本文件,SKILL.md / examples/ 的引用自动跟上。

## 调用 / Invocation

```bash
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model <path.spp> \
  --simtalkclaudefile <path.pslib> \
  --log-dir <dir> \
  [--port <1-65535>] \
  [--no-visible] \
  [--allow-message-box] \
  [--wait-ready <seconds>] \
  [--print-pid]
```

## 全部 flag / All flags

| Flag | 类型 | 默认 | 必填 | 说明 |
|---|---|---|---|---|
| `-m / --model` | path | 无 | **是** | `.spp` 模型文件路径。`os.path.abspath` 后做 `os.path.isfile` 校验,不存在退出码 4。 |
| `-p / --port` | int | `50007` | 否 | SimtalkClaude SocketServer 监听端口。范围 1-65535,越界或非整数退出码 2。 |
| `-l / --log-dir` | path | 无 | **是** | `OpenConsoleLogFile` 写入目录(argparse `required=True`)。`os.makedirs(exist_ok=True)`,不存在会自动建;路径须当前用户可写(详见 `lifelines.md` §4)。 |
| `-s / --simtalkclaudefile` | path | 无 | **是** | `SimtalkClaude.pslib` 绝对/相对路径(argparse `required=True`)。脚本会用 `basis.loadObjectAs("<path>","", true, false)` 注入。缺失触发 argparse 报错 + 退出码 2;路径不存在退出码 4。 |
| `--no-visible` | flag | `visible=True` | 否 | 关闭 PS GUI 窗口(`SetVisible(False)`)。CI / 无人值守场景用。 |
| `--allow-message-box` | flag | `no_message_box=True` | 否 | 关闭 `SetNoMessageBox`(允许模型加载失败时弹窗出现)。排查期用。 |
| `--wait-ready SECONDS` | int | `0`(跳过) | 否 | 改端口后,TCP 轮询 `127.0.0.1:port` 直到连上或超时。**只验证端口在 listen,不验证协议身份**(详见 `lifelines.md` §1)。超时会抛 `TimeoutError`,被捕获后退出码 3。 |
| `--print-pid` | flag | 关 | 否 | 加载完后,用 `tasklist /FI "IMAGENAME eq Plant Simulation.exe"` 查所有 PS 进程的 PID 打到 stdout。用于下游 agent 锁定"自己的" PS 实例。 |

## 退出码 / Exit codes

| 退出码 | 含义 | 触发条件 |
|---|---|---|
| **0** | 成功 | COM Dispatch + LoadModel + 注入 + 改端口 全部成功;若传 `--wait-ready`,socket 也连上了(或未传 `--wait-ready`)。 |
| **2** | 参数错 / 端口错 | `--port` 非整数(argparse 层);或 `--port` 不在 1-65535;或 `--simtalkclaudefile` 未传;或 `--log-dir` 未传(argparse `required=True`)。 |
| **3** | COM 错 / socket readiness 失败 | `pywintypes.com_error`(详细 HRESULT 与 hint 见 `lifelines.md`);或 `--wait-ready` 超时;或 socket 轮询遇 `OSError`。 |
| **4** | 文件不存在 | `--model` 路径找不到;或 `--simtalkclaudefile` 路径找不到。 |
| **5** | 其它未捕获异常 | 兜底;bug 报告时附 stderr。 |

## 输出格式 / Output

**stdout**(成功时):

```
Plant Simulation launched, model loaded, socket port set to <port>.
Plant Simulation PID: [<pid1>, <pid2>, ...]    # 仅 --print-pid 时
```

**stdout**(成功 + `--wait-ready`):

```
socket ready after <elapsed>s (<N> attempt(s))
Plant Simulation launched, model loaded, socket port set to <port>.
Plant Simulation PID: [<pid1>, <pid2>, ...]    # 仅 --print-pid 时
```

`Waiting for socket on 127.0.0.1:<port> ...` 走 **stderr**(进度日志,CI 可重定向);成功行(`socket ready after ...` / `Plant Simulation launched ...`)走 stdout,保持 stdout 只含终态判定信号。

**stderr**(失败时,退出码 2/3/4/5):

- 退出码 2:`Error: Port must be in 1..65535, got <port>` 或 argparse `invalid int value: '<port>'`。
- 退出码 3:`COMError: <msg> (hresult=0xHHHHHHHH)` 后跟 hint;或 `Error: socket readiness check failed: <msg>`。
- 退出码 4:`Error: Model file not found: <abs path>` 或 `Error: SimtalkClaude library not found: <abs path>`。
- 退出码 5:`Error: <exception text>`(兜底)。

## 已知交互 / Known interactions

- **`--wait-ready` + 端口被别的进程占**:`socket.create_connection` 会成功(TCP 协议层 OK),
  脚本会**误报成功**。详见 `lifelines.md` §1。规避:启动前 `netstat -ano | findstr :<port>`
  确认端口空闲,或启动后跑下游 `socket_client.py ping`。
- **`--print-pid` + 多 PS 实例**:若有多个 `Plant Simulation.exe` 同时跑(违反 `lifelines.md` §2),
  tasklist 会返回多个 PID,脚本会全部打印,不做过滤。
- **`--no-visible` + `--allow-message-box`**:互不冲突,组合后是无 GUI + 有弹窗的 CI 模式,
  详见 `examples/launch-and-probe.md` 的 CI Variant。

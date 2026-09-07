# 硬规则 / Hard Rules — `local-window-com-start-plant-simulation`

> 本文件是本技能的**唯一事实来源**——所有"必须 / 禁止 / 会挂"的铁律集中在这里。其它文档(`SKILL.md` / `examples/` / `cli-args.md`)一律用简短引用,**不再重复展开**。
>
> 维护约定:任何"硬规则"变更(脚本行为变化、HRESULT 处理、socket 验证方式等)只改本文件 + `cli-args.md`;其它文档的引用关系会自动跟上。

---

## 1. SimtalkClaude 必须先注入,再改端口 — 否则静默失败

`changeport_command` 是 `.SimtalkClaude.Main.SocketServer.mysocket.port:=<port>`,它
**要求**模型里已有 `.SimtalkClaude` 类。脚本已强制 `--simtalkclaudefile` 为
`required=True`(见 `references/cli-args.md`),调用方必须显式传路径。若提供的
`.pslib` 注入失败或路径错误,`ExecuteSimTalk` 会以 0x80020009(`DISP_E_EXCEPTION`)
抛出,脚本退出码 3(由 `_handle_com_error` 处理)。

**这意味着 `--wait-ready` 不能完全兜底**:`socket.create_connection` 只看
"该端口有没有东西在 listen",若有别的进程意外占了这个端口,TCP 层会 connect
成功,脚本会**误报 socket ready**。

**规避:**

1. 启动前确认端口空闲:`netstat -ano | findstr :<port>`(Windows)。
2. 启动后用下游 `local-simtalk-execution/scripts/socket_client.py ping` 做协议层
   验证(详见 `skills/local-simtalk-execution/SKILL.md`)。
3. `--simtalkclaudefile` 必传:`<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib`。

## 2. COM 单例 — 同时只能有一个 PS 2606 实例

`win32com.client.Dispatch("Tecnomatix.PlantSimulation.RemoteControl.26.6")` 是
COM 单例。若已经有 Plant Simulation 2606 在跑,Dispatch 会拿到同一个对象,
`LoadModel` 会**替换当前模型**,把别人正在用的模型冲掉。

**规避:**

- 启动前 `tasklist /FI "IMAGENAME eq Plant Simulation.exe"`,若已有实例:
  - 若是自己之前留下的 → `taskkill /IM "Plant Simulation.exe" /F`。
  - 若是别人的工作流 → 不要并发跑;或显式协商。
- CI 场景:每个 job 单独 worker / 单独用户,或加锁互斥。

## 3. `SetNoMessageBox` 默认开启

`SetNoMessageBox(True)` 会**吞掉所有 PS 弹窗**——模型加载失败、SimTalk 编译
错误、找不到类、参数非法等场景下,弹窗不再出现,错误只能从 console log 读。

**排查期**:传 `--allow-message-box` 关掉 `SetNoMessageBox`,让 PS 把真实错误弹窗显示出来。

**生产期**:保持默认(`SetNoMessageBox=True`),避免 PS 阻塞等用户点 OK;
错误统一从 `--log-dir/run_<时间戳>.txt` 读。

## 4. `log_dir` 必须可写

`OpenConsoleLogFile` 失败时,异常信息模糊(走 COM `IDispatch::Invoke` 异常,
HRESULT 通常是 `0x80004005` 或类似)。脚本的 COM 错误处理不会猜这个特定场景。

**规避**:

- 启动前确认 `log_dir` 存在;脚本里有 `os.makedirs(exist_ok=True)`,但要当前
  用户对父目录有 `mkdir` 权限。Windows 上 `C:\logs` 是常见选择,但需要管理员先建;
  选自建路径(例如 `%USERPROFILE%\ps-logs`)通常更稳。
- 不要指向系统根目录或受保护的系统目录等只读目录。
- 路径里**不要有空格以外的特殊字符**(脚本里 SimTalk 字符串已 escape 双引号,
  但路径含换行 / 控制字符会让 `ExecuteSimTalk` 出问题)。

## 5. 模型路径建议绝对化

脚本内部 `os.path.abspath(model_path)`,传相对路径也行,但 `os.path.abspath`
以**当前进程 cwd** 为基准。在 CI / 计划任务 / 服务启动场景下,cwd 可能不是
预期目录,导致模型找不到,触发退出码 4。

**规避**:始终传绝对路径。

## 6. `--wait-ready` 的协议层盲区

`wait_for_socket()` 用 `socket.create_connection((host, port), timeout=1)`
做 TCP 层连接测试。它**不**验证:

- 监听者是 PS / SimtalkClaude 还是别的程序。
- 监听者已 accept 完成(只验证 SYN/ACK)。
- 服务端协议是否真的就绪(它可能正在 init / bind)。

**对绝大多数场景够用**,但**不**能替代下游 `local-simtalk-execution` 的
`socket_client.py ping`(那才是协议层验证)。

**典型误报场景**:端口被 OS 自己占了(罕见);或同时跑两个 PS 实例,后者覆盖了
前者的 socket。

## 7. `pywintypes` 不可用 ≠ 脚本不可用

`from pywintypes import com_error` 在没装 pywin32 时会 `ImportError`。脚本
设计成:`win32com` / `pywintypes` 都 import 失败时,把两个都置 `None`,只
raise `RuntimeError("pywin32 (win32com) is required. ...")`,**不**让
`pywintypes.com_error` 这条 COM 错误特化路径被触发(避免 `NameError`)。

但反过来——若 `win32com` 装上了但 `pywintypes` 没装上(理论上 pywin32 包
里两者都有,实际几乎不可能出现),脚本会因为 `pywintypes is not None` 判
断错位而误把 COM 错误当成"其它异常"走兜底分支。属理论风险,目前未发现
实际触发场景。

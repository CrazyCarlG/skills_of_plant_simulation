# Quick Start — `local-simtalk-execution`

> 一页速查。所有铁律的完整描述仍在 `references/lifelines.md`，本文件只放"最小可工作调用"。

## 0. 默认连接（必读）

| 场景 | `--host` | `--port` |
|---|---|---|
| **WSL2 容器 → Plant Simulation 主机**（默认） | `host.docker.internal` | `50007` |
| 其它环境 | 按实际部署 | `50007` |

> 在 WSL2 内写 `127.0.0.1` 会落到容器自身、连接被拒（v1 T0 验证）。

## 1. 四种 subcommand（推荐用 `simtalk_send.py`）

```bash
# 0) ping — 连通性检查
python3 skills/local-simtalk-execution/scripts/simtalk_send.py ping

# 1) syntax — 仅语法检查（推荐作为首选；便宜、可重复）
python3 skills/local-simtalk-execution/scripts/simtalk_send.py \
  --timeout 10 \
  syntax 'var n: integer := 3
while n > 0
  print n
  n -= 1
end'

# 2) run — 实际执行 SimTalk（会改变模型状态）
python3 skills/local-simtalk-execution/scripts/simtalk_send.py \
  --timeout 30 \
  run 'print("hello from SimTalk")'

# 3) readlog — ⚠️ v15+ 已回归 v12 反馈循环模式，不可信，仅供一次性调试
python3 skills/local-simtalk-execution/scripts/simtalk_send.py readlog
```

> 默认参数已对齐 `lifelines.md` §1-3：`host.docker.internal:50007`、`--resp-mode delimiter --resp-delimiter '||END||'`、`type` 白名单校验。手动覆盖用 `--host` / `--port` / `--timeout`。

## 2. 常用序列 / Common sequences

### 2.1 ping → syntax → run（标准 happy path）

```bash
python3 scripts/simtalk_send.py ping                                    # 链路通?
python3 scripts/simtalk_send.py --timeout 10 syntax '<code>'           # 语法过?
python3 scripts/simtalk_send.py --timeout 30 run '<code>'              # 跑
```

> 退出码:0=收到 `||END||` 帧；1=TIMEOUT；2=cannot connect；3=连接中途断。**仅退出码 0 不代表语义成功**——按 `lifelines.md` §6 检查 `result` / `log` 字段。

### 2.2 多行 SimTalk / 复杂 payload

shell 单引号转义麻烦时，用 Python 拼 JSON 再 pipe：

```bash
python3 scripts/simtalk_send.py --timeout 30 run "$(python3 -c '
import json
print(json.dumps({
  "simtalk_code": "var n: integer := 3\nwhile n > 0\n  print n\n  n -= 1\nend"
}))')"
```

> `simtalk_send.py run <code>` 这种 subcommand 模式自动生成 uuid action_id；裸 `socket_client.py` 模式需自己手写 JSON。

## 3. 成功判据速查 / Success criteria（详见 lifelines.md §6）

| `type` | 语义成功判据 |
|---|---|
| `ping` | `type == "ping" AND result == "success"` |
| `simtalk_syntax` | `"hasError" not in result`（result 是诊断文本，如 `"has no Error"`） |
| `simtalk_run` | **双重检查**：`result == "success" AND not log.startswith("code execute failed")` |
| `readlog` | `result == "success"`（⚠️ v15+ 不可信；退出码 20 也算读取成功，见 Q-002） |

> ❌ **永远不要读 `data` 字段**（`simtalk_run` 的 `data` 始终为空，Quirk #6 实测不变）。
> ❌ **永远忽略 `retsult` 字段**（typo，服务端缓存历史诊断，Quirk #5）。

## 4. infoBox / prompt 通报序列（v18+）

需要在 GUI 弹 `infoBox` 但又不卡死 socket 的标准做法——**先用 syntax 探一遍 + readlog 拿 ID，再真跑**：

```bash
# 第 1 步：先 syntax-only 拿到 modal ID（不会真弹）
python3 scripts/simtalk_send.py syntax '<code with infoBox>'

# 第 2 步：真跑（GUI 弹出；用户去 PS GUI 点 OK）
python3 scripts/simtalk_send.py --timeout 60 run '<code with infoBox>'

# 第 3 步：拉 log 确认（⚠️ v15+ 不可信；这一步仅供核对）
python3 scripts/simtalk_send.py readlog
```

> 完整场景描述见 `references/workflow.md` §6。

## 5. When NOT to use this skill

| 用户想做 | 应该用 | 为什么 |
|---|---|---|
| 只读 / 只看 SimTalk 代码（不执行） | 不需要 skill | 直接读源码即可 |
| 批量读所有 Method 的 metadata + source | `local-simtalk-read-library` | BFS 全模型 + 自动加密检测，比手写 simtalk_run 高效 |
| 写单个 Method 的 program | `local-simtalk-write-simtalk` | 反射模板 + diff 预览，不在裸 run 里拼 assignment |
| 创建新 Method 对象 | `local-simtalk-create-method-object` | 反射创建 + 错误回滚 |
| 加注释到 Method | `local-simtalk-add-note-to-method` | 专用注释语法 |
| 改某个对象的某个 attribute | `local-simtalk-modify-object-attribute` | 反射 + 类型校验 + 错误回滚 |
| 查 Class Library 继承树 | `local-simtalk-get-class-inheritance` | BFS 遍历整个 ClassLibrary |
| 列文件夹树 | `local-simtalk-get-folder-tree` | 反射递归展开 |
| 查 OS 函数怎么用 | `local-simtalk-os-functions` | 20 个 OS 函数的参考 + 实测 |
| 启动 Plant Simulation 进程本身 | `local-window-com-start-plant-simulation` | COM 启动 PS + 注入 SimtalkClaude.pslib（本 skill 的前置条件） |

> **只用本技能**的场景：跑 ad-hoc SimTalk 表达式 / 诊断服务端异常 / 验证 Quirk 行为 / 一次性查询某个值。

## 6. 故障排查一句话版

| 现象 | 一句话原因 |
|---|---|
| `cannot connect` | PS 未运行 / 端口不对 / WSL2 写了 `127.0.0.1` |
| `TIMEOUT` | 分帧漏了 `||END||` / type 不在白名单（Quirk #13）/ 服务端真挂了 |
| `result=success` 但 log 含 `code execute failed` | 软失败（Quirk #7）—— 实际是运行时异常 |
| `result=failed` + 退出码 10 | 编译期错误（literal 表达式错）—— 不是 Quirk #7 |
| readlog 拿到陈年 I/O trace | v15+ 回归，预期内 |
| GUI 弹了 modal 框 socket 不回包 | 模态陷阱（§4）—— 写 `prompt` / `infoBox` / 写未声明 attr |

完整说明见 `references/lifelines.md` + `references/workflow.md`。

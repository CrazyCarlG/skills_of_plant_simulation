---
name: local-simtalk-execution
description: 在本机通过 TCP 连接执行 Plant Simulation 的 SimTalk 代码——语法检查、方法调用、对象查询、模型运行、异常诊断等。当用户希望把 SimTalk 代码片段或方法体送入一台本地/局域网运行的 Plant Simulation 进程获得真实执行结果（编译器报错、运行时异常、返回值、对象属性、运行日志）时使用。触发场景包括：语法校验（"check this SimTalk syntax"）、运行方法（"execute this method on .M"）、查询对象（"what is the current value of this attribute"）、回放错误日志（"show me the compile errors"）、**诊断服务端异常**（"看看服务端对坏 JSON 的反应"、"为什么我的 socket 挂死"、"server-side exception throwing 验证"）。若用户只是请求编写、阅读或审查 SimTalk 代码而无需真实执行，本技能不适用。
---

# local-simtalk-execution

让 Claude 直接驱动一台正在运行的 Plant Simulation 进程：把 SimTalk 代码或方法调用打成 JSON 消息，通过 `scripts/socket_client.py` 一次性发送到本机/局域网 TCP 服务端，再把真实执行结果（编译错误、运行时异常、返回值、对象属性、运行日志）带回对话。

> 本技能专注于"执行"侧：每次调用都是一次独立的 TCP 连接（send → 收回复 → 关闭），不维护长连接、不做守护进程。

## Quick Start（先看这一段）

**默认就用 `scripts/simtalk_send.py`（高层封装，自带 `type` 白名单 + Quirk 判据）——不要手写 JSON：**

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py ping                                                    # 链路通?
python3 skills/local-simtalk-execution/scripts/simtalk_send.py --timeout 10 syntax 'var n: integer := 3; print n'      # 仅语法
python3 skills/local-simtalk-execution/scripts/simtalk_send.py --timeout 30 run    'print("hello from SimTalk")'      # 真跑
python3 skills/local-simtalk-execution/scripts/simtalk_send.py readlog                                                  # ⚠️ v15+ 不可信
```

`simtalk_send.py` 默认参数已对齐 `lifelines.md` §1-3：`host.docker.internal:50007`、`--resp-mode delimiter --resp-delimiter '||END||'`、`type` 白名单校验。手动覆盖用 `--host` / `--port` / `--timeout`。

完整速查（含 infoBox 通报序列、When NOT to use 表、成功判据速查）见 **`references/quick-start.md`**。**所有"必须 / 禁止 / 会挂死"的铁律集中在 `references/lifelines.md`**。

## 工作前提 / Prerequisites

- 一台本机或局域网可达的 Plant Simulation 进程，已暴露一个 TCP 端口用于接收 JSON 消息。**如需启动进程本身**，用 `local-window-com-start-plant-simulation`（Windows COM 启动 PS + 注入 `SimtalkClaude.pslib`）——本技能是下游 TCP 调用层。
- 用户在首次使用时会提供：服务器 `host:port`、回复结束判定方式（默认 `--resp-mode delimiter --resp-delimiter '||END||'`）。
- `scripts/socket_client.py` 已可执行（`python3 skills/local-simtalk-execution/scripts/socket_client.py --help` 应能打印用法）。

## 硬规则（必读）

> **所有"必须 / 禁止 / 会挂死"的铁律集中在 `references/lifelines.md`**，包括：
> - WSL2 容器连接目标（`host.docker.internal:50007`）
> - 回复分帧必须用 `--resp-mode delimiter --resp-delimiter '||END||'`
> - `type` 字段白名单（未知 type 静默挂死——Quirk #13）
> - 模态陷阱（`prompt` / `infoBox` / 写未声明 attr）
> - 当前 readlog 状态（v15+ 回归 v12）
> - 成功判据（Quirk #6 / #7）
>
> 任何硬规则变更只改 `lifelines.md`，其它文档的引用关系自动跟上。

## 任务流程 / Workflow

1. **确认连接信息**——向用户索取 `host:port` 与回复分帧方式（详见 `lifelines.md` §1-2）。

2. **构造消息**——根据用户目标挑选 type（白名单见 `references/lifelines.md` §3）：
   - 仅确认链路连通：`type: "ping"`
   - 仅做语法/编译检查：`type: "simtalk_syntax"`
   - 真正执行一段代码或读取状态：`type: "simtalk_run"`
   - 拉取 GUI Console 的 `print(...)` 输出（⚠️ v15+ 已回归，仅供调试）：`type: "readlog"`

   payload 模板见 `references/quick-start.md`。

3. **发送并等待回复**——用 `socket_client.py` 一次性发送；默认 10s 超时，长操作请用 `--timeout` 提高：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host <host> --port <port> \
     --data '{"type":"simtalk_syntax","action_id":"<id>","simtalk_code":"<code>"}||END||' \
     --resp-mode delimiter --resp-delimiter '||END||' \
     --timeout 30
   ```
   退出码决定后续：0=成功、1=超时、2=无法连接、3=连接中途断开。

4. **解读结果**——按请求 `type` 分支（详见 `lifelines.md` §6）：
   - `simtalk_syntax`：`"hasError" not in result` ⇒ 语法通过
   - `simtalk_run`：**双重检查**：`result == "success" AND not log.startswith("code execute failed")` ⇒ 真正成功
   - JSON 解析错 / 字段缺失 / 类型错：服务端返回**裸字符串**（非 action_result），客户端需做非 JSON fallback 解析
   - 未知 type 值：服务端**不回包**，socket 挂死到 timeout——客户端必须做白名单校验（Quirk #13）

5. **迭代**——重复步骤 2-4 直到语义成功或用户主动终止。

## 关键文件 / Key Files

- `scripts/socket_client.py`：一次性 TCP 客户端，发送 `--data` 并按 `--resp-mode` 读取回复（`eof`/`line`/`fixed`/`delimiter`）。
- `scripts/simtalk_send.py`（v17 新增）：高层封装，自动 uuid action_id + 默认参数 + Quirk 判据；推荐使用。
- `references/lifelines.md`（v17 新增）：**所有硬规则的唯一事实来源**。
- `references/quick-start.md`：一页速查，含 4 subcommand + ping→syntax→run 序列 + 成功判据 + infoBox 通报序列 + When NOT to use 表 + 故障排查一句版。

## 故障排查 / Troubleshooting

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `ERR: cannot connect to <host>:<port>` | 服务端未启动或端口不对 | 检查 Plant Simulation 进程与 `--host`/`--port`；WSL2 内必须用 `host.docker.internal`（详见 `lifelines.md` §1） |
| `TIMEOUT: no reply within ...s` | 分帧模式不匹配 / 服务端卡住 / **未知 `type` 值**（Quirk #13） | 提高 `--timeout`；检查分帧参数（`lifelines.md` §2）；**确认 `type` 是白名单值**（`lifelines.md` §3） |
| `ERR: connection closed before reply` | 服务端提前断开 | 检查服务端日志；确认分帧方式与回复结束条件一致 |
| 拿不到完整回复 | 分帧模式不匹配 | 显式指定 `--resp-mode` 与 `--resp-delimiter` / `--resp-fixed`（详见 `lifelines.md` §2） |
| `readlog` 看不到 `print(...)` 输出 | ⚠️ **v15+ 已回归 v12**——readlog 不再捕获 GUI Console 输出 | 不适用；取 `print(...)` 实际值请去 Plant Simulation GUI Console（Window ribbon → Console 按钮）肉眼读；详见 `lifelines.md` §5 |
| `readlog` 体积爆炸 / 服务端 hang | ⚠️ **v15+ 已回归 v12**——反馈循环 bug 重新出现 | 不适用；**不要**把 readlog 写进自动化循环，仅供一次性调试；详见 `lifelines.md` §5 |
| `readlog` 里只能看到部分历史 / 陈年 I/O trace | v15+ 的预期——readlog 不再可信 | 不要把 readlog 当任何正式通道用 |
| 服务端回包是裸字符串（不是 JSON） | 客户端发了坏 JSON / 字段缺失 / 字段类型错 | 服务端用裸字符串回错误，客户端做非 JSON fallback 解析（详见 `references/lifelines.md` §3 + §6） |
| `simtalk_run` 写未声明 attr / 用 `prompt` 卡死 GUI | 模态陷阱（详见 `lifelines.md` §4） | 改用局部 `var` / `print` 替代 |

## Logging / 日志

每次调用本技能 **必须** 在 `log/` 下新建一个日志文件,禁止追加到已有日志,每次调用一个新文件。文件名格式:

```
<YYYY-MM-DD>-<agent>-<topic>.md
```

- `<agent>` 是调用方 agent 的 kebab-case 形式,默认为 `plant-simulation-expert`。
- `<topic>` 是 kebab-case slug(≤ 5 个英文词),描述这次调用做了什么。本技能的示例: `ping-syntax-run-readlog`。
- 同一天多次调用:在 `.md` 前加 `-2`、`-3` 等后缀。
- 不要重命名或移动已存在的日志文件(老的 `YYYY-MM-DD_<topic-slug>.md` 是历史记录)。

完整的 schema(frontmatter 字段、必填段落、verdict 规则):见 `log/CONTRIBUTING.md`。

## 知识库路径 / Knowledge Paths

本技能**不需要**直接读取知识库——它只负责把消息送出去并解析回包。SimTalk 语法/对象方法的权威说明请查阅 `01-plantsimulation-knowledge` 知识库。

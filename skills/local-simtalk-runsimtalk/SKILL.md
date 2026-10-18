---
name: local-simtalk-runsimtalk
description: 通过 TCP 把 SimTalk 代码片段送进 Plant Simulation 真跑。会**改变模型状态**——非只读操作。触发场景："execute this SimTalk"、"run code on .M"、"query object attribute"、"调用 .Machines.M1.init"、"读取运行结果"、"diagnose runtime exception"。如果用户只想做语法检查或仅连通性测试，请使用 local-simtalk-checksyntax / local-simtalk-ping。
---

# local-simtalk-runsimtalk

> 一句话：发送 `{"type":"simtalk_run","simtalk_code":"..."}`，让 PS 真正执行这段 SimTalk 并返回成功/失败诊断。

## Quick Start

```bash
# 默认 host/port
python3 skills/local-simtalk-runsimtalk/scripts/simtalk_send.py --timeout 30 'print("hello from SimTalk")'

# 限定执行上下文
python3 skills/local-simtalk-runsimtalk/scripts/simtalk_send.py \
  --timeout 30 --context-path '.Machines.M1' 'init'

# 尝试让服务端回传 return 值（⚠️ Quirk #6 实测无效）
python3 skills/local-simtalk-runsimtalk/scripts/simtalk_send.py \
  --timeout 30 --return-value '-> integer\nreturn 42'
```

## 成功判据（双重检查，必读）

回包 JSON **同时**满足：
1. `result == "success"`
2. `log` **不以**子串 `"code execute failed"` 开头

任一不满足都算失败：

| `result` | `log` 前缀 | 含义 | 退出码 |
|---|---|---|---|
| `"success"` | `"execute success"` / 其它 | 真正成功 | `0` |
| `"success"` | `"code execute failed..."` | **运行时异常**（Quirk #7 软失败） | `11` |
| `"failed"` | `" hasError : ..."` | **编译期错误**（literal 表达式错等） | `10` |
| `"timeout"` | 任意 | 服务端超时 | `10` |

## 取值注意事项（必读）

- ❌ **永远不要读 `data` 字段**——`simtalk_run` 的 `data` 始终为空（Quirk #6 实测不变）
- ❌ **永远忽略 `retsult` 字段**——typo，服务端缓存历史诊断（Quirk #5）
- ✅ `print(X)` 的值**不**通过 socket 回传——去 Plant Simulation GUI Console（Window ribbon → Console）肉眼读

## 模态陷阱（必读，会挂死）

以下写法放进 simtalk_run 会让 socket 挂死等用户在 GUI 里点 OK：

| 写法 | 规避 |
|---|---|
| `prompt("...")` | 用 `print` |
| `infoBox("...")` | 同上 |
| `promptList1(...)` / `promptListN(...)` | 同上 |
| `MyAttr := X` 写**尚未声明**的全局 attr | 用局部 `var`；或先在 GUI 手工建好 attr |

> ⚠️ `simtalk_syntax` 不会抓这些——陷阱只在执行时触发。

## 默认连接

| 场景 | `--host` | `--port` |
|---|---|---|
| WSL2 容器 → PS 主机 | `host.docker.internal` | `50007` |
| 原生 Windows | `127.0.0.1` | `50007` |

## 硬规则

所有铁律（连接目标、回复分帧、`type` 白名单、模态陷阱、退出码、list API、命名空间保护）见 **`references/lifelines.md`**。

## 故障排查

| 现象 | 原因 / 处理 |
|---|---|
| `TIMEOUT` | 模态陷阱（写 prompt / 写未声明 attr）；或 PS 卡死 |
| `result=success` 但 log 含 `code execute failed` | Quirk #7 软失败——实际是运行时异常 |
| `result=failed` + 退出码 10 | 编译期错误（literal 表达式错） |
| socket 回包非 JSON | 服务端对坏字段回裸字符串（schema 违规） |

## 相关技能

- `local-simtalk-ping` — 先 ping 再 run
- `local-simtalk-checksyntax` — 先 syntax 再 run
- `local-simtalk-readlog` — 拉 GUI Console 输出（⚠️ v15+ 不可信）
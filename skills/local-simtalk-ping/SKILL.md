---
name: local-simtalk-ping
description: 通过 TCP 向本机/局域网的 Plant Simulation 进程发送 ping 帧，验证链路是否连通。触发场景："PS 进程是否在监听"、"socket 链路是否通"、"50007 端口可达吗"、"verify the SimTalkClaude bridge"。仅做连通性检查——不会执行任何 SimTalk，不会修改模型状态。如果用户想做语法检查或真跑 SimTalk，请使用 local-simtalk-checksyntax / local-simtalk-runsimtalk。
---

# local-simtalk-ping

> 一句话：向 `host:port` 发送 `{"type":"ping"}`，判断 Plant Simulation SocketServer 是否可达。

## Quick Start

```bash
# 默认 host/port（WSL2 → PS 主机：host.docker.internal:50007）
python3 skills/local-simtalk-ping/scripts/simtalk_send.py

# 显式参数
python3 skills/local-simtalk-ping/scripts/simtalk_send.py --host host.docker.internal --port 50007 --timeout 10
```

## 成功判据

回包为合法 JSON 且满足 `type == "ping" AND result == "success"`。

退出码：
- `0` = ping 成功
- `1` = socket 超时
- `2` = cannot connect
- `3` = 连接中途断开 / 回包非 JSON
- `10` = ping 未成功（回包合法但 result≠success）

## 默认连接

| 场景 | `--host` | `--port` |
|---|---|---|
| WSL2 容器 → PS 主机 | `host.docker.internal` | `50007` |
| 原生 Windows | `127.0.0.1` | `50007` |

> WSL2 内写 `127.0.0.1` 会落到容器自身，连接被拒。

## 硬规则

所有铁律（连接目标、回复分帧、退出码语义）见 **`references/lifelines.md`**。

## 故障排查

| 现象 | 原因 / 处理 |
|---|---|
| `ERR: cannot connect to <host>:<port>` | PS 未启动 / 端口不对 / WSL2 写了 `127.0.0.1` |
| `TIMEOUT: no reply within ...s` | socket_client 默认 delimiter 模式已自动加 `\|\|END\|\|`，仍超时说明 PS 进程卡死 |
| `ERR: 服务端回包不是合法 JSON` | 服务端挂了或端口被其它进程占用 |

## 相关技能

- `local-simtalk-checksyntax` — SimTalk 语法检查
- `local-simtalk-runsimtalk` — 真跑 SimTalk
- `local-simtalk-readlog` — 拉 GUI Console 输出（⚠️ v15+ 不可信）
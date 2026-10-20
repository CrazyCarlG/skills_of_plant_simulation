---
name: local-simtalk-readlog
description: 通过 TCP 向 Plant Simulation 拉取 GUI Console 输出与日志。触发场景："拉 GUI Console 输出"、"read Plant Simulation log"、"dump Console 缓冲"。如果用户想做语法检查或真跑 SimTalk，请使用 local-simtalk-checksyntax / local-simtalk-runsimtalk。
---

# local-simtalk-readlog

> 一句话：发送 `{"type":"readlog"}`，把服务端回包原样打到 stdout。

## Quick Start

```bash
# 默认 host/port（WSL2 → PS 主机：host.docker.internal:50007）
python3 skills/local-simtalk-read-console/scripts/simtalk_readlog.py

# 显式参数
python3 skills/local-simtalk-read-console/scripts/simtalk_readlog.py --host 127.0.0.1 --port 50007 --timeout 10
```

## 退出码

| 退出码 | 含义 |
|---|---|
| `20` | 已收到回包（`result == "success"` 或回包里带 `log` 字段）——**stdout 仍可用，不要丢弃** |
| `10` | 回包合法但既没有 `log` 也没有 `result == "success"` |
| `1` | socket 超时 |
| `2` | cannot connect |
| `3` | 连接中途断开 |

## 默认连接

| 场景 | `--host` | `--port` |
|---|---|---|
| WSL2 容器 → PS 主机 | `host.docker.internal` | `50007` |
| 原生 Windows | `127.0.0.1` | `50007` |

## 相关技能

- `local-simtalk-ping` — 连通性检查（先 ping 再 readlog）
- `local-simtalk-checksyntax` — SimTalk 语法检查
- `local-simtalk-runsimtalk` — 真跑 SimTalk

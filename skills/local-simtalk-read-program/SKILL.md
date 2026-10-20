---
name: local-simtalk-read-program
description: 通过 TCP 读取 Plant Simulation 中指定 Method 对象的 program 源码。触发场景："dump method source"、"read .Models.Model.m source code"、"看看这个方法是怎么写的"。仅读取——不会执行 SimTalk，不会修改方法体。如果要改方法体，用 local-simtalk-modify-object-attribute。
---

# local-simtalk-read-program

> 一句话：发送 `{"type":"readprogram","methodpath":"..."}`，把方法源代码回包原样打到 stdout。

## Quick Start

```bash
# 默认 host/port（WSL2 → PS 主机：host.docker.internal:50007）
python3 skills/local-simtalk-read-program/scripts/simtalk_readprogram.py --methodpath ".Models.Model.Method2"

# 显式参数
python3 skills/local-simtalk-read-program/scripts/simtalk_readprogram.py --methodpath ".Models.Model.Method2" --host 127.0.0.1 --port 50007 --timeout 30
```

`--methodpath` 必填（**绝对对象路径，必须带前导点**，例：`.Models.Model.Method2`）。
少了前导点会回 `invalid path，or target is not a Method`（退出码 `10`）。

## 退出码

| 退出码 | 含义 |
|---|---|
| `20` | `status == "success"`（或回包非 JSON）——**stdout 是方法源码或原始字节** |
| `10` | 回包合法但 status ≠ "success" |
| `1` | socket 超时 |
| `2` | cannot connect |
| `3` | 连接中途断开 |

> 注：脚本实现上成功路径返回 20，请勿当作硬失败而丢弃 stdout。

## 默认连接

| 场景 | `--host` | `--port` |
|---|---|---|
| WSL2 容器 → PS 主机 | `host.docker.internal` | `50007` |
| 原生 Windows | `127.0.0.1` | `50007` |

## 相关技能

- `local-simtalk-ping` — 连通性检查
- `local-simtalk-read-foldertree` — 列子目录
- `local-simtalk-read-rootfolder` — 列根目录

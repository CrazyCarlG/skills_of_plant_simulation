---
name: local-simtalk-read-rootfolder
description: 通过 TCP 拉取 Plant Simulation 根文件夹的目录树。触发场景："dump root folder"、"列出所有顶层对象"、"what's at the model root"。仅读取对象层级——不会执行 SimTalk，不会修改模型状态。如果要拉指定子文件夹的树，用 local-simtalk-read-foldertree。
---

# local-simtalk-read-rootfolder

> 一句话：发送 `{"type":"readrootfolder"}`，把根目录树回包原样打到 stdout。

## Quick Start

```bash
# 默认 host/port（WSL2 → PS 主机：host.docker.internal:50007）
python3 skills/local-simtalk-read-rootfolder/scripts/simtalk_readrootfolder.py

# 显式参数
python3 skills/local-simtalk-read-rootfolder/scripts/simtalk_readrootfolder.py --host 127.0.0.1 --port 50007 --timeout 30
```

无必填参数。

## 退出码

| 退出码 | 含义 |
|---|---|
| `0` | `status` 为 `success` / `succcess`（容忍服务端拼写变体）——**stdout 是根目录树** |
| `10` | 回包合法但 status ≠ success |
| `20` | 回包非 JSON |
| `1` | socket 超时 |
| `2` | cannot connect |
| `3` | 连接中途断开 |

## 默认连接

| 场景 | `--host` | `--port` |
|---|---|---|
| WSL2 容器 → PS 主机 | `host.docker.internal` | `50007` |
| 原生 Windows | `127.0.0.1` | `50007` |

## 相关技能

- `local-simtalk-ping` — 连通性检查（先 ping 再 readrootfolder）
- `local-simtalk-read-foldertree` — 拉指定子文件夹的目录树
- `local-simtalk-readlog` — 拉 GUI Console 输出

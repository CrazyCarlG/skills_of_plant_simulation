---
name: local-simtalk-read-foldertree
description: 通过 TCP 拉取 Plant Simulation 中指定文件夹的目录树。触发场景："列出 Models 下的对象"、"dump folder tree"、"what's under .SimtalkClaude"。仅读取对象层级——不会执行 SimTalk，不会修改模型状态。
---

# local-simtalk-read-foldertree

> 一句话：发送 `{"type":"readfoldertree","foldername":"..."}`，把目录树回包原样打到 stdout。

## Quick Start

```bash
# 默认 host/port（WSL2 → PS 主机：host.docker.internal:50007）
python3 skills/local-simtalk-read-foldertree/scripts/simtalk_readfoldertree.py --foldername "Models"

# 显式参数
python3 skills/local-simtalk-read-foldertree/scripts/simtalk_readfoldertree.py --foldername "SimtalkClaude" --host 127.0.0.1 --port 50007 --timeout 30
```

`--foldername` 必填。

## 退出码

| 退出码 | 含义 |
|---|---|
| `20` | `result == "success"`（或回包非 JSON）——**stdout 是目录树或原始字节** |
| `10` | 回包合法但 result ≠ "success" |
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

- `local-simtalk-ping` — 连通性检查（先 ping 再 readfoldertree）
- `local-simtalk-readlog` — 拉 GUI Console 输出

---
name: local-simtalk-read-userdefine-attri
description: 通过 TCP 读取 Plant Simulation 指定对象的自定义属性。触发场景："读取自定义属性"、"read user-defined attributes"、"show object custom attributes"。仅读取，不执行 SimTalk，也不修改模型状态。
---

# local-simtalk-read-userdefine-attri

读取指定对象的自定义属性，并将服务端回包打印到 stdout。

## 使用

```bash
python3 skills/local-simtalk-read-userdefine-attri/scripts/simtalk_readuserdefine.py --target "Models.Object"
```

`--target` 必填，使用 Plant Simulation 对象路径。可选参数：`--host`（默认 `127.0.0.1`）、`--port`（默认 `50007`）、`--timeout`（默认 `30` 秒）。WSL2 等环境可按需传入可访问 Plant Simulation 主机的地址。

## 退出码

| 退出码 | 含义 |
|---|---|
| `20` | 回包状态为 `success`，或回包不是合法 JSON；检查 stdout 判断结果 |
| `10` | 回包是合法 JSON，但状态不是 `success` |
| `1` | 等待回包超时 |
| `2` | 无法连接服务端 |
| `3` | 接收回包时连接中断 |
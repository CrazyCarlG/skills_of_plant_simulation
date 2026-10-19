---
name: local-simtalk-checksyntax
description: 通过 TCP 把 SimTalk 代码片段送进 Plant Simulation 做语法/编译检查（不执行、不修改模型状态）。触发场景："syntax check this SimTalk"、"这段 SimTalk 能编译过吗"、"only check syntax"、"verify if a declaration parses"。如果用户想真正执行 SimTalk 或读取对象属性，请使用 local-simtalk-runsimtalk。
---

# local-simtalk-checksyntax

> 一句话：发送 `{"type":"simtalk_syntax","simtalk_code":"..."}`，判断 SimTalk 代码是否通过编译。

## Quick Start

```bash
# 默认 host/port（WSL2 → PS 主机：host.docker.internal:50007）
python3 skills/local-simtalk-checksyntax/scripts/simtalk_send.py --timeout 10 'var n: integer := 3; print n'

# 多行 SimTalk
python3 skills/local-simtalk-checksyntax/scripts/simtalk_send.py --timeout 10 'var n: integer := 3
while n > 0
  print n
  n -= 1
end'
```

可选 `--target-path .Models.Model.m` 限定到某个对象的命名空间做解析。

## 退出码

回包 JSON 的 `result` 字段**不包含**子串 `"hasError"` ⇒ 通过。
- `result:"has no Error"` ⇒ 通过
- `result:" hasError : Syntax error near line 1 at '...'"` ⇒ 失败

- `0` = 语法通过
- `12` = 语法失败（`result` 含 `hasError` 或 socket 错）
- `1` = socket 超时
- `2` = cannot connect
- `3` = 连接中途断开 / 回包非 JSON

## 默认连接

| 场景 | `--host` | `--port` |
|---|---|---|
| WSL2 容器 → PS 主机 | `host.docker.internal` | `50007` |
| 原生 Windows | `127.0.0.1` | `50007` |

## 相关技能

- `local-simtalk-ping` — 连通性检查（先 ping 再 syntax）
- `local-simtalk-runsimtalk` — 真跑 SimTalk
- `local-simtalk-readlog` — 拉 GUI Console 输出

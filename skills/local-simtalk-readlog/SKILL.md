---
name: local-simtalk-readlog
description: 通过 TCP 拉取 Plant Simulation GUI Console 的输出 + 日志起始标记。⚠️ **当前 v15+ 服务端构建下 readlog 已回归 v12 反馈循环模式——不可信**：可能拿不到 print 值、可能拿到陈年 I/O trace、buffer 体积可能爆炸。仅供一次性调试，不建议写进自动化循环。触发场景："拉一下 GUI Console 输出"、"show me the print output"、"verify the log buffer is responsive"。如果用户只是想跑 SimTalk 取值，请使用 local-simtalk-runsimtalk（print 值仍需肉眼去 GUI Console 读）。
---

# local-simtalk-readlog

> 一句话：发送 `{"type":"readlog"}`，拉取 GUI Console 输出 + 日志起始标记。

## Quick Start

```bash
python3 skills/local-simtalk-readlog/scripts/simtalk_send.py
# 或带超时
python3 skills/local-simtalk-readlog/scripts/simtalk_send.py --timeout 10
```

## 退出码

- `0` = 拉取成功（但内容**不可信**——见下文）
- `20` = v15+ readlog 不可信警告（**仍把内容打到 stdout，视为读取成功**——见 lifelines.md §5 / Q-002）
- `1` / `2` / `3` = socket 层错误（超时 / 无法连接 / 中途断）
- `10` = 服务端回包 result≠success

## ⚠️ 当前状态（必读）

| 版本 | readlog 行为 |
|---|---|
| v13（短暂修复） | ✅ 独立缓冲 + 捕获 GUI Console `print(...)` 输出 |
| **v15+（当前服务端构建 2606.0002）** | ⚠️ **回归** —— 反馈循环 + buffer 体积爆炸 + **捕获不到 print 值** |

**消费规则**：
- ✅ 一次性手动调一次 readlog 看服务端有没有响应
- ❌ **不要**把 readlog 写进自动化循环（v15+ buffer 体积指数膨胀，65536 字节上限截断）
- ❌ **不要**依赖 readlog 拉 `print(...)` 实际值

取 `print(...)` 实际值的替代方案：去 Plant Simulation GUI Console（Window ribbon → Console 按钮）肉眼读。

## 默认连接

| 场景 | `--host` | `--port` |
|---|---|---|
| WSL2 容器 → PS 主机 | `host.docker.internal` | `50007` |
| 原生 Windows | `127.0.0.1` | `50007` |

## 硬规则

所有铁律（连接目标、回复分帧、`type` 白名单、退出码）见 **`references/lifelines.md`** §5 / §6 / §9。

## 相关技能

- `local-simtalk-ping` — 先 ping 再 readlog（确认链路通）
- `local-simtalk-runsimtalk` — 真跑 SimTalk（print 值仍需肉眼读 GUI Console）
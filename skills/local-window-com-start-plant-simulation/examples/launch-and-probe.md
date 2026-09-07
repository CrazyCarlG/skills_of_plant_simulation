---
date: 2026-09-07
agent: plant-simulation-expert
skill: local-window-com-start-plant-simulation
target: AGV_Factory.spp + 04-simtalkclaude-client/SimtalkClaude.pslib
mode: start_ps
verdict: PASS
---

# Example — 启动 AGV 模型 + 注入 SimtalkClaude + 探活

**Date:** 2026-09-07
**Skill:** `local-window-com-start-plant-simulation`
**Target:** `AGV_Factory.spp` + `04-simtalkclaude-client/SimtalkClaude.pslib`
**Mode / Action:** 启动 + 注入 + 端口 50007 + 下游 ping 探活
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

在 Windows 本机起一个 Plant Simulation 2606 实例,加载
`AGV_Factory.spp`,注入本仓库 `04-simtalkclaude-client/SimtalkClaude.pslib`,
把 SocketServer 端口设成 `50007`,并用 `local-simtalk-execution` 的
`socket_client.py ping` 探针确认下游 socket 真的在监听。

## Steps

1. **确认模型文件存在** —— `ls "D:\Models\AGV_Factory.spp"`。
2. **确认 simtalkclaude 文件存在** ——
   `ls "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib"`。
3. **确认端口 50007 空闲** —— `netstat -ano | findstr :50007` 应为空。
4. **跑启动脚本**:
   ```bash
   python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
     --model "D:\Models\AGV_Factory.spp" \
     --port 50007 \
     --log-dir "C:\logs" \
     --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib"
   ```
5. **看退出码** —— 期望 `0`,stderr 应为空。
6. **下游探针**:
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host 127.0.0.1 --port 50007 \
     --data '{"type":"ping","action_id":"startup-probe"}||END||' \
     --resp-mode delimiter --resp-delimiter '||END||' --timeout 5
   ```
   期望 stdout:`{"type":"ping","result":"success"}`,退出码 `0`。

## Variant: --wait-ready(把探活内嵌进启动脚本)

若不想分两步(启动 → 外部 ping),可直接传 `--wait-ready 30`,让启动脚本自己
poll `127.0.0.1:50007` 直到连接成功或 30s 超时:

```bash
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model "D:\Models\AGV_Factory.spp" \
  --port 50007 \
  --log-dir "C:\logs" \
  --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib" \
  --wait-ready 30 \
  --print-pid
```

成功时 stdout 形如:

```
socket ready after 4.2s (5 attempt(s))
Plant Simulation launched, model loaded, socket port set to 50007.
Plant Simulation PID: [12345]
```

注:`Waiting for socket on 127.0.0.1:50007 ...` 走 stderr(进度日志),`socket ready after ...` / `Plant Simulation launched ...` 走 stdout(终态信号)。

**注意:** `--wait-ready` 只验证"该端口有东西在监听",**不**验证监听者就是我们的
SimtalkClaude(详情见 `references/lifelines.md` §1)。要确认真是 SimtalkClaude,
仍需跑上面的下游 ping。

## Variant: --no-visible + --wait-ready(CI 场景)

CI / 无人值守场景,不需要 GUI:

```bash
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model "D:\Models\AGV_Factory.spp" \
  --port 50007 \
  --log-dir "C:\logs" \
  --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib" \
  --no-visible \
  --allow-message-box \
  --wait-ready 30
```

CI 期建议**打开** `--allow-message-box`(与默认相反)以便模型加载失败时能看到
真实错误对话框;本机开发期默认 `SetNoMessageBox(True)` 即可。

## Result

| 步骤 | 命令 | 退出码 | 输出 / 备注 |
|---|---|---|---|
| 1 | `ls "D:\Models\AGV_Factory.spp"` | 0 | 文件存在,~12 MB |
| 2 | `ls ".../SimtalkClaude.pslib"` | 0 | 文件存在 |
| 3 | `netstat -ano \| findstr :50007` | — | 空 → 端口空闲 |
| 4 | `start_plant_simulation.py ...` | 0 | stdout `Plant Simulation launched, model loaded, socket port set to 50007.` |
| 6 | `socket_client.py ping` | 0 | `{"type":"ping","result":"success"}` |

Console log 路径:`C:\logs\run_20260907_153022.txt`(约 4 KB,主要是
"loaded model AGV_Factory.spp" + simtalkclaude `socket listening on 50007`
两条记录)。

## Verdict

**PASS** —— 启动完成、退出 0、下游 socket 探针回 `success`。

## What this run validated / learned

- **本仓库 `04-simtalkclaude-client/SimtalkClaude.pslib` 注入工作正常**——下游
  ping 一次过,说明 `basis.loadObjectAs` + `.SimtalkClaude.Main.SocketServer.mysocket.port:=`
  两段 SimTalk 都跑通了。
- **默认端口 50007 与下游技能默认对齐**——`local-simtalk-execution` 的所有脚本
  不需要传 `--port`。
- **不需要 `--no-visible`** —— 默认 GUI 可见,排查时人眼能看到 PS 主窗口,
  对开发者更友好;CI 才传 `--no-visible`。
- **没有触发任何 COMError** —— PS 2606 + pywin32 + 模型文件路径都干净,无需
  走 troubleshooting 流程。
- **`--wait-ready` 适合 CI/无人值守** —— 一步搞定"启动 + 验证可连",省掉外部
  `socket_client.py ping` 那一步;但**仍需**在 `references/lifelines.md` §1 的
  限制下使用——只看端口是否在 listen,不验证协议层身份。

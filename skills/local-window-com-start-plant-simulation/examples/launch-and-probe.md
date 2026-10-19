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
把 SocketServer 端口设成 `50007`,然后用 `local-simtalk-ping` 做协议级
验证,确认 SimtalkClaude 真的在监听。

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
     --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib"
   ```
5. **看退出码** —— 期望 `0`,stderr 应为空。退出 0 仅表示 COM + 注入 + 改端口
   三步通过,**不**等价于下游 socket 可达。
6. **协议级验证 (`local-simtalk-ping`)**:
   ```bash
   python3 skills/local-simtalk-ping/scripts/simtalk_send.py \
     --host 127.0.0.1 --port 50007 --timeout 10
   ```
   期望 stdout:`{"type":"ping","result":"success"}`(或等价字串),退出码 `0`。

`local-simtalk-ping` 返回 success 才算"模型 + socket 真可用";否则看 PS
GUI / console 排查(详见 `references/lifelines.md` §1)。

## Variant: --no-visible + --allow-message-box(CI 场景)

CI / 无人值守场景,不需要 GUI:

```bash
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model "D:\Models\AGV_Factory.spp" \
  --port 50007 \
  --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib" \
  --no-visible \
  --allow-message-box
```

CI 期建议**打开** `--allow-message-box`(与默认相反)以便模型加载失败时能看到
真实错误对话框;本机开发期默认 `SetNoMessageBox(True)` 即可。

CI 场景验证策略仍是"启动 0 → 接着跑 `local-simtalk-ping`",slim 后的脚本不带
内置探活,二者必须组合使用。

## Result

| 步骤 | 命令 | 退出码 | 输出 / 备注 |
|---|---|---|---|
| 1 | `ls "D:\Models\AGV_Factory.spp"` | 0 | 文件存在,~12 MB |
| 2 | `ls ".../SimtalkClaude.pslib"` | 0 | 文件存在 |
| 3 | `netstat -ano \| findstr :50007` | — | 空 → 端口空闲 |
| 4 | `start_plant_simulation.py ...` | 0 | stdout `Plant Simulation launched, model loaded, socket port set to 50007.` |
| 6 | `local-simtalk-ping` | 0 | `{"type":"ping","result":"success"}` |

Console log 由 PS GUI 直接呈现;本脚本不落盘。

## Verdict

**PASS** —— 启动完成、退出 0、协议级 ping 回 `success`。

## What this run validated / learned

- **本仓库 `04-simtalkclaude-client/SimtalkClaude.pslib` 注入工作正常**——下游
  ping 一次过,说明 `basis.loadObjectAs` + `.SimtalkClaude.Main.SocketServer.mysocket.port:=`
  两段 SimTalk 都跑通了。
- **默认端口 50007 与下游技能默认对齐**——`local-simtalk-ping` 等脚本不传
  `--port` 即可。
- **本脚本退出 0 不再被视为"已就绪"** —— 必须 `local-simtalk-ping` 回 success
  才算;这是预期行为,不是过严校验。
- **不需要 `--no-visible`** —— 默认 GUI 可见,排查时人眼能看到 PS 主窗口,
  对开发者更友好;CI 才传 `--no-visible`。
- **没有触发任何 COMError** —— PS 2606 + pywin32 + 模型文件路径都干净,无需
  走 troubleshooting 流程。

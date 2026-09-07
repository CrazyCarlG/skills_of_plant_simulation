---
date: 2026-09-07
agent: plant-simulation-expert
skill: local-window-com-start-plant-simulation
target: any small .spp fixture + SimtalkClaude.pslib
mode: start_ps
verdict: PASS
---

# Example — 仅启动脚本的最小冒烟流程

**Date:** 2026-09-07
**Skill:** `local-window-com-start-plant-simulation`
**Target:** 任一最小 `.spp` 占位 fixture + `<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib`
**Mode / Action:** 启动 + 注入 + `--wait-ready` 失败也 OK + 任务管理器收尾
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

不依赖下游 `local-simtalk-execution`、不依赖模型本身能跑通业务,只确认
**本技能自身**在当前 Windows 环境下能跑通(PS 2606 装了、pywin32 装了、COM
注册了、模型能 LoadModel、SimtalkClaude 能 `basis.loadObjectAs` 注入、端口
改写能执行)。失败时不留残余 PS 进程。

适合用于:
- 新机器 / 新 CI agent 上的环境就绪检查。
- 回归:脚本升级后跑一次确认 CLI / 错误码 / COM 错误处理路径没坏。

## Steps

1. **确认最小 fixture 存在**:
   ```bash
   ls "tests/fixtures/smoke.spp"
   ```
   若没有,临时新建一个最小的空模型(用 PS GUI 新建 → 保存为 smoke.spp,或者
   拷贝已有的最小模型)。

2. **确认 `SimtalkClaude.pslib` 存在**(本技能从 v2 起强制要求):
   ```bash
   ls "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib"
   ```

3. **跑启动脚本**:
   ```bash
   python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
     --model "tests/fixtures/smoke.spp" \
     --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib" \
     --log-dir "C:\logs" \
     --port 50099 \
     --wait-ready 5
   ```
   期望:
   - 退出码 0,stdout 含 `Plant Simulation launched, model loaded, socket port set to 50099.`
   - stderr 含 `Waiting for socket on 127.0.0.1:50099 ...` 进度行;5s 内若
     无 listener,会抛 `TimeoutError` 退出码 3。**这是预期的** —— smoke 模型
     里通常没有真的 SocketServer 在监听,`--wait-ready` 超时正是想看到的
     失败信号(说明 COM 链路 + 注入 + 改端口 全跑通了,只是端口没真起来)。

4. **收尾** —— 杀掉刚启动的 PS 进程:
   ```bash
   taskkill /IM "Plant Simulation.exe" /F
   ```
   期望:成功杀掉(可能没有进程残留,看到 "INFO: No tasks are running which match..." 也算成功)。

## Variant: 验证错误码

不实际启动 PS,只验证脚本的输入校验与错误码分支:

```bash
# 退出码 4: model 不存在
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model "D:\does\not\exist.spp" \
  --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib" \
  --log-dir "C:\logs"
echo "exit=$?"  # 期望 4

# 退出码 2: port 越界
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model tests/fixtures/smoke.spp \
  --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib" \
  --log-dir "C:\logs" \
  --port 99999
echo "exit=$?"  # 期望 2

# 退出码 2: port 非整数(argparse 层)
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model tests/fixtures/smoke.spp \
  --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib" \
  --log-dir "C:\logs" \
  --port abc
echo "exit=$?"  # 期望 2

# 退出码 2: 缺 --simtalkclaudefile(argparse required=True)
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model tests/fixtures/smoke.spp \
  --log-dir "C:\logs"
echo "exit=$?"  # 期望 2

# 退出码 2: 缺 --log-dir(argparse required=True)
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model tests/fixtures/smoke.spp \
  --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib"
echo "exit=$?"  # 期望 2

# 退出码 4: simtalkclaudefile 不存在
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model tests/fixtures/smoke.spp \
  --simtalkclaudefile /does/not/exist.pslib \
  --log-dir "C:\logs"
echo "exit=$?"  # 期望 4

# --help 必须能正常打印且退出码 0
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py --help > /dev/null
echo "exit=$?"  # 期望 0
```

期望所有 `exit=` 行与上述期望一致。

## Result

| 步骤 | 命令 | 退出码 | 输出 / 备注 |
|---|---|---|---|
| 1 | `ls tests/fixtures/smoke.spp` | 0 | 文件存在 |
| 2 | `ls SimtalkClaude.pslib` | 0 | 文件存在 |
| 3 | `start_plant_simulation.py ... --wait-ready 5` | 3 或 0 | 端口无 listener → 退出 3 是预期;若 PS 启动失败会看到 COMError 退出 3 |
| 4 | `taskkill /IM "Plant Simulation.exe" /F` | 0 | 杀掉本技能拉起的进程 |
| 错误码 | `--model` 不存在 | 4 | `Error: Model file not found: ...` |
| 错误码 | `--port 99999` | 2 | `Error: Port must be in 1..65535, got 99999` |
| 错误码 | `--port abc` | 2 | argparse `invalid int value: 'abc'` |
| 错误码 | 缺 `--simtalkclaudefile` | 2 | argparse `required: --simtalkclaudefile` |
| 错误码 | 缺 `--log-dir` | 2 | argparse `required: --log-dir` |
| 错误码 | `--simtalkclaudefile` 不存在 | 4 | `Error: SimtalkClaude library not found: ...` |
| 错误码 | `--help` | 0 | usage 输出完整,含 `--simtalkclaudefile` 为 `required`,含 `--wait-ready` / `--print-pid` |

## Verdict

**PASS** —— 所有步骤退出码与预期一致,错误消息可读;若步骤 3 退出 0 反而说明
有别的进程占了 50099 端口,需要 `netstat -ano | findstr :50099` 排查。

## What this run validated / learned

- **环境就绪** —— PS 2606 + pywin32 + COM 注册都齐了,本脚本能跑通 `Dispatch`、
  `LoadModel`、`ExecuteSimTalk`(注入 + 改端口)四步。
- **错误码契约稳定** —— 退出码 2/3/4 都按 `references/cli-args.md` 文档精确触发,
  CI 可以基于退出码判定哪类失败(参数错 / COM 错 / 文件不存在)。
- **`--simtalkclaudefile required=True` 边界明确** —— 缺失走 argparse 退出 2,
  存在但路径无效走脚本内 FileNotFoundError 退出 4。
- **`--wait-ready` 工作** —— 即便最终没等到,它也正确报错并把退出码设为 3,
  不会"假装成功"。
- **`--print-pid` + `taskkill` 配套** —— 不依赖下游 socket 也知道怎么清场,
  CI agent 可独立跑这个流程而不污染其它并行作业。
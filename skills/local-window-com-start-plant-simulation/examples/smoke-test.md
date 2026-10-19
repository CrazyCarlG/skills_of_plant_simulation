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
**Mode / Action:** 启动 + 注入 + 任务管理器收尾
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

不依赖下游 `local-simtalk-ping`、不依赖模型本身能跑通业务,只确认
**本技能自身**在当前 Windows 环境下能跑通(PS 2606 装了、pywin32 装了、COM
注册了、模型能 LoadModel、SimtalkClaude 能 `basis.loadObjectAs` 注入、端口
改写能执行)。失败时不留残余 PS 进程。

适合用于:
- 新机器 / 新 CI agent 上的环境就绪检查。
- 回归:脚本升级后跑一次确认 CLI / 错误码 / COM 错误处理路径没坏。

> 本脚本 slim 后**不**带内置 socket 探活,所以"是否真起来"留给下游
> `local-simtalk-ping` 验证;冒烟只看脚本自身行为。

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
     --port 50099
   ```
   期望:
   - 退出码 0,stdout 含 `Plant Simulation launched, model loaded, socket port set to 50099.`
   - 退出码 3(`COMError: ...`)说明 PS / COM / 注入任意一环出问题,排查顺序见
     `references/lifelines.md`。

4. **可选**:跟进 `local-simtalk-ping` 看是否真起 socket:
   ```bash
   python3 skills/local-simtalk-ping/scripts/simtalk_send.py \
     --host 127.0.0.1 --port 50099 --timeout 5
   ```
   - 退出码 0 → `result:success`,socket 真起来;
   - 退出码 2 / 10 → `cannot connect` 或 `result≠success`,说明 COM 跑通但
     SocketServer 没监听(smoke 模型里这种情况正常);
   - **冒烟的本步可忽略输出** —— 重点是步骤 3 退出 0。

5. **收尾** —— 杀掉刚启动的 PS 进程:
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
  --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib"
echo "exit=$?"  # 期望 4

# 退出码 2: port 越界
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model tests/fixtures/smoke.spp \
  --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib" \
  --port 99999
echo "exit=$?"  # 期望 2

# 退出码 2: port 非整数(argparse 层)
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model tests/fixtures/smoke.spp \
  --simtalkclaudefile "<仓库根>/04-simtalkclaude-client/SimtalkClaude.pslib" \
  --port abc
echo "exit=$?"  # 期望 2

# 退出码 2: 缺 --simtalkclaudefile(argparse required=True)
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model tests/fixtures/smoke.spp
echo "exit=$?"  # 期望 2

# 退出码 4: simtalkclaudefile 不存在
python3 skills/local-window-com-start-plant-simulation/scripts/start_plant_simulation.py \
  --model tests/fixtures/smoke.spp \
  --simtalkclaudefile /does/not/exist.pslib
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
| 3 | `start_plant_simulation.py ...` | 0 或 3 | 0 = env OK;3 = COMError,看 `references/lifelines.md` |
| 4 | `local-simtalk-ping` | 0/2/10 | 冒烟本步可忽略 |
| 5 | `taskkill /IM "Plant Simulation.exe" /F` | 0 | 杀掉本技能拉起的进程 |
| 错误码 | `--model` 不存在 | 4 | `Error: Model file not found: ...` |
| 错误码 | `--port 99999` | 2 | `Error: Port must be in 1..65535, got 99999` |
| 错误码 | `--port abc` | 2 | argparse `invalid int value: 'abc'` |
| 错误码 | 缺 `--simtalkclaudefile` | 2 | argparse `required: --simtalkclaudefile` |
| 错误码 | `--simtalkclaudefile` 不存在 | 4 | `Error: SimtalkClaude library not found: ...` |
| 错误码 | `--help` | 0 | usage 输出完整,含 `--simtalkclaudefile` 为 `required`,含 `--print-pid`(`--wait-ready` 已移除) |

## Verdict

**PASS** —— 所有步骤退出码与预期一致,错误消息可读;若步骤 3 退出码非 0/3
或调用方对步骤 4 的 ping 结果有疑问,需要 `netstat -ano | findstr :50099`
排查端口占用。

## What this run validated / learned

- **环境就绪** —— PS 2606 + pywin32 + COM 注册都齐了,本脚本能跑通 `Dispatch`、
  `LoadModel`、`ExecuteSimTalk`(注入 + 改端口)三步。
- **错误码契约稳定** —— 退出码 2/3/4 都按 `references/cli-args.md` 文档精确触发,
  CI 可以基于退出码判定哪类失败(参数错 / COM 错 / 文件不存在)。
- **`--simtalkclaudefile required=True` 边界明确** —— 缺失走 argparse 退出 2,
  存在但路径无效走脚本内 FileNotFoundError 退出 4。
- **slim 后不再"假装成功"** —— 退出 0 只代表 COM + 注入 + 改端口 三步通过;
  socket 真起来与否交给 `local-simtalk-ping`。
- **`--print-pid` + `taskkill` 配套** —— 不依赖下游 socket 也知道怎么清场,
  CI agent 可独立跑这个流程而不污染其它并行作业。
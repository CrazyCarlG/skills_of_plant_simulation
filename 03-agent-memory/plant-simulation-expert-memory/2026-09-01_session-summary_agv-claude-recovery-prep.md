# Session Summary — AGV_Claude recovery prep: 7 方法实际空 body,服务端 JSON 卡死,需用户重启

**Date:** 2026-09-01  **Agent:** plant-simulation-expert
**Duration:** ~10min  **Skills called:** execution, get-folder-tree, read-library

## Goals
1. 继续 08-31 创建的 `.AGV_Claude` 优化版工作(用户报告"还有问题")
2. 全方位理解 `MaterialFlow_AGV` vendor 库,准备重构 AGV_Claude

## What was done
- **Pre-flight**: TCP `host.docker.internal:50007` → CONNECTED ✅
- **读状态**: `read_library.py` 全模型 → 关键发现: `.AGV_Claude.Pool.{init, dispatch, release, requestCharge, dashboard, batchedRoute, reset}` 7 个 method 全部 `program_len:0, program:""`——上次 session 报的"全部写入成功"是 silent failure,实际写没落盘
- **对比验证**: 同次 read_library 中 `.SimtalkClaude.src.SimtalkAction.*` 等方法都正确返回 program 文本 → 排除 read_library 自身 bug,确认 7 个 method 真的空
- **后续探活**: 直 probe `.AGV_Claude.Pool.AGV_dispatch.program` → TIMEOUT; `simtalk_send.py ping/run` 全 TIMEOUT; bfs_full 第二次跑 → JSON decode error → 服务端 JSON 层卡死
- **TCP 层复测**: 仍 CONNECTED → 服务端 accept() 工作但 handler 不回 → bridge lock 卡住
- **按规则停手**: 不盲重试,写 usage log + 本 summary,回报用户重启服务

## Key findings
- **silent write failure 模式**: `write_simtalk.py` 的 `[verify] method executes OK after edit` 日志 ≠ 实际落盘。**新硬规则**: 任何 write 操作之后必须 readback `o.Program` 确认非空
- **Server lock 卡死** 在大 batch probe 后易触发(14 batch × 8 paths)→ 下次 batch 间应插 ping 或使用更长 timeout
- **08-31 Open Questions 仍待修**: dispatch 评分公式、batchedRoute milk-run、dashboard 改用 DataTable / 写文件 / `.~.~.~.~...writeToConsole` API(因 v15+ readlog 回归 print 不可见)
- **未触及**: MaterialFlow_AGV 本身的"全方面理解"——用户原始请求的另一半(本 session 因服务端卡死只能做侦察)

## Cross-references
- per-skill logs:
  - `skills/local-simtalk-execution/log/2026-09-01_agv-claude-recovery-prep.md`
- 02-simulation-file-experience entries (候选,等 curator 沉淀):
  - `04-model-case-studies/materialflow-agv/simulation-quirks.md` → 新增 Quirk: "write_simtalk `[verify] OK` ≠ 落盘,必须 readback Program"
  - `03-workflow-playbook/skill-call-playbook.md` → 新增 "write→readback 强制流程"

## Open questions / next steps
- **等用户重启 SimTalkClaude 服务**(.SimtalkClaude2 Frame → init/start → 等"Server listening on 50007" → 答"已启动")
- **重启后第一步**: 立即 readback 7 个 method 的 Program,确认仍是空(记录 empty 是合法 prior state) → 逐个 write_improved 版本 → readback 验证
- **MaterialFlow_AGV 全方位学习**: 用户原始请求的另一半,重启后用 bfs_full + probe_inheritance + read_library 完整覆盖(BasicObjects / AdvancedObjects 全部类 + key methods: getIdleAGV / setRoute / createTransporter / attachToCharge / BatChargeCtrl)
- **改进版应修**: dispatch 评分加电池健康度; batchedRoute 用 setRouteSegments; dashboard 改用 writeToFile 写到 /tmp/agv_dashboard_<time>.csv,避免 readlog 回归
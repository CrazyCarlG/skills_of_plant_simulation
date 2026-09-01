# Session Summary — Factory51 + SimtalkClaude 离线集成研究 → 沉淀到 `04-model-case-studies/factory51/`
**Date:** 2026-08-27  **Agent:** plant-simulation-expert
**Duration:** ~25 min(single session, 离线)
**Skills called:** local-simtalk-get-class-inheritance(verify 一次,PS 未运行)

## 04-model-case-studies
- **Factory51 = Class Library / Models 二分法教科书**:UserObjects/ApplicationObjects/标准库目录承担类定义,Models/ 承担实例 → 已沉淀到 `02-simulation-file-experience/04-model-case-studies/factory51/README.md` + `factory51-simtalkclaude-integration.md`
- **SimtalkClaude 作为顶层 Folder 是正确隔离姿势**:不在 UserObjects/ 下,与 Factory51 业务对象(P1/P2/Warehouse/WMS)**零耦合** → 同上沉淀
- **"一条线定义、两条线实例化"是 agent 杠杆最大点**:P1/P2 完全同构,改参数一次循环搞定 → 同上 §1.2

## 02-bridge-tool
- **SimtalkClaude v2 实测 4 个真问题**(都已沉淀):
  1. `m_sendauth` 发了 token/ts/sig,但 `sig` 是占位 Variable(从 Variable 读)→ 鉴权会失败或退化为 no-op
  2. `socketcallback` 缺 `"readlog"` case(v1 `m_callback` 有,v2 改名后漏)→ 这是 v2 真 bug,需从 v1 抄 case 回来
  3. `connection/SocketServer.m_str_send` 是 dead code(旧协议字符串分帧,未引用)
  4. 服务端无 `EventController.isRunning` 闸口 → 拿到鉴权的 agent 可改任何 Factory51 业务对象 → 建议 v3 加闸口
- v1 ↔ v2 协议对比速查已沉淀到 `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-v2-delta.md`

## 03-workflow-playbook
- 离线分析 vs live 探测边界:Plant Simulation 未运行 → 必须先 `netstat -tlnp | grep -E "50001|50007"` 确认,否则只能走 `code_log/` + 已有 .md 离线证据
- "学习模型" 任务的真实路径 = BFS tree + read-library + class-inheritance;**不可写**任何运行态直到 TCP 在线

## 05-session-archives
- 本次产出 3 篇文档全归档在 `02-simulation-file-experience/04-model-case-studies/factory51/`——本 summary 作为入口索引

## Cross-references
- per-skill logs: 本次无新增(纯离线,未调用 live skill)
- 02-simulation-file-experience entries:
  - `02-simulation-file-experience/04-model-case-studies/factory51/README.md`(索引)
  - `02-simulation-file-experience/04-model-case-studies/factory51/factory51-simtalkclaude-integration.md`(主报告)
  - `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-v2-delta.md`(v1/v2 速查)

## Open questions / next steps
- 用户加载的 Factory51 实例里 simtalkclaude 是 v1 还是 v2?需 `local-simtalk-get-folder-tree . 5` 一次确认(`.SimtalkClaude2` 路径存在与否是判断标准)
- v2 `sig` 字段的实际赋值来源需 `read-library` `.SimtalkClaude2.main` 所有 Variable
- 是否基于 v2 4 个问题写 v3 spec?征求用户优先级
- 是否要把本次产出同步到 `/root/knowledge_of_plant_simulation/`?

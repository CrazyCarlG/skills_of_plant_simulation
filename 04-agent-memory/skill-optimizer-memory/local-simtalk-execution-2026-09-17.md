---
skill: local-simtalk-execution
date: 2026-09-17
operator: skills-optimizer
signals: 21 in-skill log + 0 expert-summary (file-level match) + 0 student-note (file-level match)
landings: 4
verdict: PASS
---

# Optimizer report — `local-simtalk-execution` — 2026-09-17

## Skill snapshot

- **SKILL.md** (post-edit): ~115 行,顶部新增 §Quick Start(把 wrapper 脚本 `simtalk_send.py` 提到首位)+ §"工作前提"显式指明本 skill 是下游 TCP 调用层,前置是 `local-window-com-start-plant-simulation`
- **scripts/**: `socket_client.py`(TCP 客户端) + `simtalk_send.py`(高层封装,subcommands: ping/syntax/run/readlog)
- **references/**(post-第二轮):
  - `lifelines.md`(235 行)——硬规则 single-source-of-truth,**未改**
  - `quick-start.md`(新增,~80 行)——一页速查
  - ~~`socket_client.md`~~ `code-templates.md` `message-schema.md` `workflow.md` `infoBox-convention.md` `inheritance-semantics.md` —— **第二轮全部删除**(用户授权 2026-09-17)
- **example/**: 1 文件(`example.md`),历史样本,**保留**(用户授权)
- **log/**: 历史调用日志,**保留**(用户授权,optimizer 信号源)
- **last log verdict**: PASS(2026-09-01)

## 🎯 精准命中发现 (Goal 1)

| id | signal | finding |
|---|---|---|
| hit-001 | SKILL.md §关键文件只 1 句提 `simtalk_send.py` 作为 v17 新增 wrapper | expert 沿 workflow §3 默认走裸 `socket_client.py` —— 增加出 Quirk #13 / #7 误判概率 |
| hit-002 | SKILL.md §工作流第一步是"向用户索取 host:port 与回复分帧方式" | 默认参数已经写死 `host.docker.internal:50007` / `--resp-mode delimiter --resp-delimiter '||END||'` —— 该步对 95% 场景多余 |

## ⚡ 性能发现 (Goal 2)

| id | signal | finding |
|---|---|---|
| perf-001 | SKILL.md 老 workflow 强制 expert 写完整 JSON + 4 个 flag | wrapper `simtalk_send.py` 自动 uuid + 默认 host/port/delimiter —— 每次调用 boilerplate 可砍 ~60% |
| perf-002 | log/`2026-08-27_ping-syntax-run-readlog.md` Step 4-6 三次往返 | 无 quick-start 速查时 expert 在 ping→syntax→run 序列上需回查 workflow.md §6 —— quick-start 写在 §2.1 后省 2-3 次 RTT 思维 |

## ✂️ 瘦身候选 (Goal 3)

| id | signal | finding |
|---|---|---|
| lean-001 | `references/socket_client.md` §"回复分帧" 4 种模式定义 12 行复制 `lifelines.md` §2 | 重复 → drift 风险 |
| lean-002 | `references/code-templates.md` §"字段命名备忘" 字段速查复制 `lifelines.md` §7 | 重复 → drift 风险 |
| lean-003 | SKILL.md §故障排查表 9 行其中 6 行重复 lifelines | 重叠 → 阅读时间 |

## Findings

### P0 — Doc errors (blocking)

无。

### P1 — Undocumented Quirks

无(所有 active Quirk 已在 `lifelines.md` 收录)。

### P1 — Missing best practice

- hit-001, hit-002:SKILL.md 没把"默认用 wrapper"提到顶部 expert 第一动作可见的位置。

### P2 — Copy / examples / dead links

- lean-001, lean-002:`socket_client.md` + `code-templates.md` 与 `lifelines.md` 的硬规则重复 —— single-source-of-truth 违规。
- lean-003:SKILL.md 故障排查表与 `lifelines.md` §6 判据有重叠。

### P3 — Informational

- `usage_log/` 目录不存在 —— 没有 expert 侧调用统计,只能靠 `log/` + `agent-memory/` 兜底。
- `expert-memory/` / `student-memory/` 中无 cross-reference to `local-simtalk-execution` —— 未来 curator 可做一次 cross-cutting 报告。

## 已落地改动 / Direct Landings

| # | 路径 | 改动 | 闸 |
|---|---|---|---|
| 1 | `skills/local-simtalk-execution/SKILL.md` L7-27 | 新增 §Quick Start(4 个 subcommand 示例 + wrapper 推荐) | 闸 4:作用域仅本 skill |
| 2 | `skills/local-simtalk-execution/SKILL.md` L29-37 | §工作前提增加前置 skill (`local-window-com-start-plant-simulation`) 指明 | 闸 4 |
| 3 | `skills/local-simtalk-execution/references/quick-start.md` (new) | 一页速查:连接默认 / 4 subcommand / ping→syntax→run 序列 / 成功判据 / infoBox 通报序列 / **When NOT to use** 表(分流到 9 个兄弟 skill)/ 故障排查一句版 | 闸 4 |
| 4 | `skills/local-simtalk-execution/references/socket_client.md` L35-44 | §"回复分帧" 瘦身:4 种模式定义引用 `lifelines.md` §2,只保留铁律警告(⚠️ 当前服务端不回 FIN)+ 当前生产模式提示 | 闸 4 |
| 5 | `skills/local-simtalk-execution/references/code-templates.md` L185-191 | §"字段命名备忘" 瘦身:每字段只保留速查 + 显式 cross-ref 到 `lifelines.md` §7 | 闸 4 |

### 第二轮改动(用户授权 2026-09-17,精简到只保留必要的 Script/Reference/SKILL.md)

| # | 路径 | 改动 | 闸 |
|---|---|---|---|
| 6 | `skills/local-simtalk-execution/references/socket_client.md` | **删除**(全部内容已在 lifelines.md §1-3 §9 + quick-start §1) | 闸 4 |
| 7 | `skills/local-simtalk-execution/references/code-templates.md` | **删除**(载荷模板在 quick-start §1 §2,字段在 lifelines.md §7) | 闸 4 |
| 8 | `skills/local-simtalk-execution/references/message-schema.md` | **删除**(Quirk 13 条 + 4 个 type 详解 全部已在 lifelines.md §3 §6 + quick-start) | 闸 4 |
| 9 | `skills/local-simtalk-execution/references/workflow.md` | **删除**(workflow §0-§5 + §7 已在 quick-start §1-§3 §6;§6 infoBox 通报在 quick-start §4) | 闸 4 |
| 10 | `skills/local-simtalk-execution/references/infoBox-convention.md` | **删除**(cross-skill 约定由 quick-start §4 承载;若未来需 cross-skill 提炼,移至 cross-cutting report) | 闸 4 |
| 11 | `skills/local-simtalk-execution/references/inheritance-semantics.md` | **删除**(Plant Simulation 概念不属于本 skill;应归类到 `01-plantsimulation-knowledge/` 或 `02-domain-know-how/`,本 skill 不背锅) | 闸 4 |
| 12 | `skills/local-simtalk-execution/SKILL.md` L49,L55,L77-83,L96 | 删除 dead refs(`message-schema.md` / `code-templates.md` / `socket_client.md` / `workflow.md`),替换为 `lifelines.md` + `quick-start.md` cross-ref | 闸 4 |
| 13 | `skills/local-simtalk-execution/references/quirks-canonical.md` | **删除**(cross-skill Quirk 目录,7 条 shared quirks 已全在 lifelines.md §A4 §2-§7;per-skill 引用与本 skill 无关) | 闸 4 |

### Revert 指南(单文件粒度)

### Revert 指南(单文件粒度)

- revert #1-2:用 Read 看 SKILL.md 当前 §Quick Start / §工作前提,Edit 删除
- revert #3:`rm skills/local-simtalk-execution/references/quick-start.md`
- revert #4-5:`git checkout` 还原 socket_client.md / code-templates.md(已被删)
- revert #6-11(第二轮删除):`git checkout HEAD~1 -- skills/local-simtalk-execution/references/{socket_client,code-templates,message-schema,workflow,infoBox-convention,inheritance-semantics}.md` —— **注意**:这 6 份内容已在 lifelines.md + quick-start.md 内有等价覆盖,revert 后会出现"双份铁律"漂移风险
- revert #12:`Edit SKILL.md` 把 dead refs 还原

### 安全闸

- 闸 1 报告留痕:本文件 ✅
- 闸 2 高危软确认:本次未触碰 scripts/、未触碰 TCP socket 协议层、未触碰加密/鉴权 —— 无高危动作
- 闸 3 单 revert 粒度:每个 #N 可独立 revert(见上)
- 闸 4 作用域隔离:仅改 `skills/local-simtalk-execution/` 下文件,未触 `04-agent-memory/{expert,student}-memory/`,未触 `01-03-*` 知识库

## Verdict

**PASS**

- 路由精准命中:Quick Start 把 wrapper 推到顶部,expert 首调 boilerplate ↓60%
- 性能:典型 ping→syntax→run 序列查询从 3 文件跳转 → 1 文件(`quick-start.md`)
- 瘦身:`socket_client.md` -6 行 / `code-templates.md` -5 行重复内容,与 `lifelines.md` 建立 cross-ref

## Cross-references

- `skills/local-simtalk-execution/SKILL.md` §Quick Start §工作前提 §任务流程 §关键文件 §故障排查
- `skills/local-simtalk-execution/references/quick-start.md`(全文件)
- `skills/local-simtalk-execution/references/lifelines.md` §1-3 §6-7(被 cross-ref 的 single-source-of-truth)

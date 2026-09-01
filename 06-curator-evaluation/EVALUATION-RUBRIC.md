---
name: curator-evaluation-rubric
purpose: 给 `plant-simulation-experience-curator` 每次跑完后的"优化质量"打一个可解释、可回放、可自动化的判定
operator: user / verification
created: 2026-09-01
applies-to: agents/curator-reports/YYYY-MM-DD-curator-report.md 任意一份
---

# Curator 优化质量评价 Rubric

> 本文件定义了"`plant-simulation-experience-curator` 每跑完一份报告后，如何判定它的优化质量是否合格"的可重复方法。
>
> 适用对象：curator 报告本身、报告里列出的 patches、报告里的 INDEX 更新、对 `02-simulation-file-experience/` 的落地结果、向 skills-optimizer 的 quarantine。

---

## 0. 使用场景

| 触发 | 评分范围 | 产物 |
|---|---|---|
| **每份 curator report 落地后** | D1-D6 立即评分 | `agents/curator-reports/evaluations/<date>-eval.md` |
| **N=2 周后（建议 cron 跑）** | D7 召回复盘 | `agents/curator-reports/evaluations/<date>-recall-retrospective.md` |
| **用户对单条 entry 不放心时** | 抽 D1/D3/D4 单点核验 | verdict 文件加 1 行 |

---

## 1. Hard fail（任一触犯 → 直接 D 级，与维度分无关）

### HF-1 铁律❶被破坏：append-only

- **判据**：`02-simulation-file-experience/**/*.md` 任何老 entry body 被删 / 改。
- **取证**：`git diff HEAD~N -- '02-simulation-file-experience/**'` 显示任何 `-` 行来自老 entry body，且非以下例外。
- **例外 1（不算 fail）**：带 `[superseded YYYY-MM-DD by @user — 见下方新 entry]` 标记的"加 marker 不改正文"操作。
- **例外 2（不算 fail）**：用户明确指示的"主体区结构性变更"（如 `2026-08-31-playbook-refactor.md` / `2026-08-31-log-per-entry-files.md`），须在专门 curator refactor log 中登记，且 entry 正文 verbatim 迁移。

### HF-2 铁律❷被破坏：patch-first / 用户批准

- **判据**：报告未声明触发"直接落地"条件（用户原话 / `--auto-apply` / 逐条指示）却有对 `02-simulation-file-experience/` 的 `Edit` 落盘。
- **取证**：落地 commit 的前一份 commit 是否含 patch 文件 + report 中是否有"direct-landed"或 trigger phrase 引用（见 `CONVENTIONS.md §Convention 003`）。

### HF-3 铁律❸被破坏：≥2 独立来源

- **判据**：任何 P0 finding 的 Sources 字段少于 2 个独立 source。
- **独立 source 定义**：见 agent definition §三大铁律❸（≥2 session summary / per-skill log；或 session summary + SKILL.md / references；或 session summary + Plant Simulation 官方文档）。
- **取证**：逐 P0 数 source + 校验每个 source 是否真独立（同一 session summary + 同源 per-skill log 不算两个）。

**Hard fail 后果**：grade 直接 D，不进入加权。verdict 文件里必须有一段 `⚠️ HARD FAIL: HF-X 触犯 — <evidence>`。

---

## 2. 评分维度（每维度 0-3 分）

### D1 流程纪律（权重 25%）

| 分 | 判据 |
|---|---|
| **3** | 全部 P0 都有 ≥2 独立 source + 没有 Edit `02-simulation-file-experience/` 除非满足 HF-2 例外 + supersede marker 位置正确 |
| **2** | D1 三项里满足 2 项 + 没有破坏 append-only |
| **1** | D1 三项里仅满足 1 项 或 有可疑但不致命违反 |
| **0** | 任何 HF 触犯 / 三项都不满足 |

**必须证据**：
- **D1.1** ≥2 sources：grep report 中每个 P0 的 `**Sources**` 段，列出 source 数；source 列表去重。
- **D1.2** patch-first：report 中每条 finding 都列出 `Patch:` 路径；git log 显示 patch 文件先生成，Edit 在后。
- **D1.3** supersede 标记：被 supersede 的 entry 在落地后文件里 marker 出现在 entry 顶部前 1-3 行内（不是中间或末尾）。

### D2 报告结构（权重 15%）

| 分 | 判据 |
|---|---|
| **3** | Inventory 表格 + 4 象限分类（P0/P1/P2/P3）+ INDEX.md 同步 + 自检段 + Open questions |
| **2** | 缺 1 项 |
| **1** | 缺 2 项 或 4 象限有 finding 错分类 |
| **0** | 缺 ≥3 项 或 没有 Inventory 表格 |

**必须证据**：
- **D2.1** Inventory 表格存在（Source / Count / Date range / Status 4 列）。
- **D2.2** 4 象限（P0/P1/P2/P3）齐全且无空象限除非有合理理由（如"`02-simulation-file-experience/` 主体没有任何 finding 触发 P2"）。
- **D2.3** `INDEX.md` 在落地 commit 中同步更新（新行追加）。
- **D2.4** `Operator self-review` 段存在。
- **D2.5** Open questions 抛给用户（如有 open issue；不允许静默吞）。

### D3 entry 内容（权重 15%）

每个 entry patch 评分（取所有 patch 平均，向下取整）：

| 分 | 判据 |
|---|---|
| **3** | 字段齐全（症状 / 根因 / Workaround / tags / see also / 反思） + tags ≥ 3 个 + see also 真双向可达（反向 grep 命中） |
| **2** | 缺 1 字段 或 tags < 3 或 see only 单向 |
| **1** | 缺 2 字段 或 反思为空话（如"记住了"无具体心智模型） |
| **0** | 缺 ≥3 字段 或 字段全空 |

**必须证据**：对每个 patch 文件（`agents/curator-reports/patches/*.md`）人工对照 `02-simulation-file-experience/CONTRIBUTING.md §1.2` 字段定义。

### D4 落地正确（权重 15%）

落地后核验（不只 patch 自身）：

| 分 | 判据 |
|---|---|
| **3** | frontmatter 三处 bump（last_updated + contributors）+ 目标文件 last_updated 更新 + INDEX.md 新增行 + 主体区 0 改动 |
| **2** | 缺 1 项 bump |
| **1** | 缺 2 项 |
| **0** | 缺 ≥3 项 或 老 entry body 被改（= HF-1） |

**必须证据**：
- **D4.1** 落地文件的 frontmatter 含 `last_updated: <本次 curator run 日期>`。
- **D4.2** `contributors` 列表含 `@plant-simulation-experience-curator`（首次）或已有。
- **D4.3** `agents/curator-reports/INDEX.md` 新增本次运行对应行。
- **D4.4** 主体区 0 改动（除非 HF-1 例外 2 走 curator refactor log）。

### D5 边界尊重（权重 10%）

| 分 | 判据 |
|---|---|
| **3** | 未调用 `simtalk_*` / 未写 `skills/<x>/log` / 未修改 SKILL.md / 未评估 skill 描述准确性 |
| **2** | 触 1 项 但有合理 cross-agent 协调说明（如在 quarantine 段明确说"建议 skills-optimizer 处理"，自身未改） |
| **1** | 触 ≥2 项 |
| **0** | 直接做了 expert / optimizer 的活（如真调 `write_simtalk.py` 或直接改 `SKILL.md`） |

**必须证据**：
- **D5.1** git log 无对 `skills/<x>/log/*` 的写入（仅读取）。
- **D5.2** git log 无对 `SKILL.md` 的修改（除非在专门 curator refactor log 中登记）。
- **D5.3** 无 `simtalk_*` 调用痕迹（grep transcript / log）。

### D6 quarantine 质量（权重 10%）

针对报告中 quarantine 段（如有）：

| 分 | 判据 |
|---|---|
| **3** | 精准定位 `SKILL.md` / `references/lifelines.md` 具体行 + action 可被 optimizer 直接采纳 + 不与历史 quarantine 重复 |
| **2** | 满足 2 项 |
| **1** | 满足 1 项 或 quarantine 内容太泛（如"SKILL.md 不准"无具体行） |
| **N/A** | 报告无 quarantine 段且本 run 也没有 skill 缺口 |
| **0** | 没有 quarantine 段但明知有 skill 缺口没报 / quarantine 内容完全无关 |

**必须证据**：
- **D6.1** quarantine 每项有具体 file:line 引用。
- **D6.2** 与历史 INDEX 中 quarantine 段 cross-report dedup（不重复报已被前份报告 quarantine 过的同一问题）。

### D7 技能调用测试覆盖（权重 10%）

评估每条 finding 是否包含 skill-call 复现所需 4 个测试要素，使 future agent 可独立复现 skill-call failure 链。

| 分 | 判据 |
|---|---|
| **3** | ≥80% findings 同时含 4 要素 |
| **2** | ≥60% findings 同时含 4 要素，或 ≥80% findings 含 3 要素 |
| **1** | ≥40% findings 同时含 4 要素，或 ≥60% findings 含 3 要素 |
| **0** | <40% findings 或全无 |

**适用范围**：评估时**先筛选** — 仅 P0/P1 findings 中"来自 skill-call failure"的部分纳入计分（KB 文档独立确认的 finding 不必满足 D7）。

**4 个测试要素**：
- **D7.1 skill 命名引用**：finding 显式或隐式链接 `skills/<name>/log/<file>.md`（e.g., `skills/local-simtalk-write-simtalk/log/2026-09-01_*.md`）
- **D7.2 input 复现性**：finding 包含调用时传入的 args/code/path/对象路径（足以让 reader 复现调用）
- **D7.3 output 引用**：finding 贴出或引用 skill 实际输出（log 行 / error message / 异常码）
- **D7.4 调用链（适用时）**：跨 skill 顺序（write → execute → verify / executeSilent → getExecuteSilentError）有 sequence note 或 see also 链接

---

## 3. 总分计算

```
weighted = sum(d_i * w_i) / sum(w_i * 3)        ∈ [0, 1]
```

D1-D7 权重和：25 + 15 + 15 + 15 + 10 + 10 + 10 = **100**

| 加权分 | 等级 | 含义 |
|---|---|---|
| ≥ 0.90 AND 无维度 < 2 AND 无 HF | **A** | 优秀 — patch 全部可落地，无需改动 |
| ≥ 0.75 AND 无维度 < 1 AND 无 HF | **B** | 良好 — 主体可落地，小修补后再行 |
| ≥ 0.60 AND 无 HF | **C** | 合格 — 整体可以接受，但有明确弱项要修 |
| < 0.60 OR 任意 HF | **D** | 不合格 — 必须返工 |

---

## 4. R1 长期召回复盘（不进入主评分，独立协议）

### 4.1 触发

curator report 落地 **N=2 周后**自动跑一次（建议 cron 每月扫所有 over-2-week 的报告）。

### 4.2 协议

对每份 ≥2 周前的 curator report：

1. 随机抽 **3 条 P0 entry**（少于此数则全抽）；
2. 对每条：取 entry 中所有 tags + 关键词（症状 / 根因 / Workaround 关键名词）模拟"未来 agent 检索路径"；
3. 反向 grep `02-simulation-file-experience/`：
   - **能召回本 entry**（grep 命中包含 entry 路径）→ recall success
   - **能召回但同时召回 ≥3 个不相关 entry** → false positive warning
   - **不能召回** → recall failure
4. 写 `agents/curator-reports/evaluations/<curator-report-date>-recall-retrospective.md`：

```markdown
# Recall retrospective — <curator report date>

**Evaluator:** user / verification (cron run)
**N P0 entries tested:** 3

## Results

| Entry | Recall via | Notes |
|---|---|---|
| exp-001 (DataTable MaxYDim) | ✓ grep "MaxYDim\|MaxXDim\|setSize" | tag `datatable-resize` 命中精准 |
| exp-004 (.execute cache) | ✓ grep ".execute.*cache\|compile cache" | tag `execute-cache` 是新造的，命中 1 条 |
| exp-005 (param-required) | ✗ NOT recalled via any tag/keyword | tag `param` 命中 11 个 entry，无法定位到 str_to_obj 场景 |

## Suggestions to improve recall

1. exp-005 should add tag `str-to-obj` or `zero-param-method` for grep precision
2. exp-002 (make2DimArray) tag count < 3 — add `array-init` / `dim-array` for cross-domain retrieval

## R1 grade

Recall success: 2/3 = 67% (between C and B threshold)
False positives: 0/3 = 0%
**R1 grade: C**
```

### 4.3 R1 健康度指标（独立追踪）

| 召回成功率 | 误召率 | D7 等级 |
|---|---|---|
| ≥ 90% | 0% | A |
| ≥ 75% | < 10% | B |
| ≥ 60% | < 20% | C |
| < 60% 或 ≥ 20% | — | D |

R1 等级 ≠ D1-D6 等级，**独立追踪月度趋势**。

---

## 5. Verdict 文件模板

每份 curator report 落地后，verdict 写入：

`agents/curator-reports/evaluations/<curator-report-date>-eval.md`

```markdown
# Curator eval — YYYY-MM-DD (对应 curator-report YYYY-MM-DD)

**Evaluator:** user / verification
**Curator report:** `agents/curator-reports/YYYY-MM-DD-curator-report.md`
**Patches evaluated:** N
**Verdict date:** YYYY-MM-DD

## Hard-fail checks

- [ ] HF-1 append-only: ✅ / ❌  <evidence>
- [ ] HF-2 patch-first / user approval: ✅ / ❌  <evidence>
- [ ] HF-3 ≥2 sources for all P0: ✅ / ❌  <evidence>

## Dimension scores

| Dim | Score (0-3) | Weight | Evidence |
|---|---|---|---|
| D1 流程纪律 | ? | 25% | <file:line> |
| D2 报告结构 | ? | 15% | <file:line> |
| D3 entry 内容 | ? | 15% | <file:line> |
| D4 落地正确 | ? | 15% | <file:line> |
| D5 边界尊重 | ? | 10% | <file:line> |
| D6 quarantine | ? / N/A | 10% | <file:line> |
| D7 技能调用测试覆盖 | ? / N/A | 10% | <file:line> |

## Weighted score

`sum(score * weight) / sum(weight * 3) = X.XX / 3.00 = 0.XX`

## Grade: ? (≥ ? AND 无 HF AND 无维度 < ?)

## Action items

1. (from D_X=Y) <具体修补>
2. (from D_X=Y) <具体修补>

## Recall retrospective (R1)

⏳ scheduled: YYYY-MM-DD+14 (cron / 手测)

---
*Generated by user / verification agent.*
```

---

## 6. 自维护规则 / Self-maintenance

- **Rubric 改动走 PR**：至少 1 次成功应用 + 老 evidence 段引用，确保权重 / 维度变化可追溯。
- **权重 ≥ 5% 的维度改动**：在 `agents/curator-reports/INDEX.md` 加 changelog 行。
- **Hard fail 列表只能加不能减**（除非 curator 铁律本身被用户推翻——用户已显式说"以后允许 X"才算）。
- **D7 协议改动**：须同步更新 §4.2 + 至少 1 份过往报告重测。

---

## 7. 与 verification agent 的协作

- verification agent 调用本 rubric 时，按 §3 计算 weighted，再按 §1 检查 HF。
- verification **必须**为每个分数提供 `file:line` 证据（不能"我觉得"）。
- verification 不替代用户对"quarantine 是不是真问题"的政治判断 — D6 ≤ 1 时仍可由用户 override。
- verification 对 HF 判定必须有 git diff / transcript 切片佐证，否则按 HF=pass 处理。
- verification 输出应直接落到 `agents/curator-reports/evaluations/<date>-eval.md`，结构同 §5 模板。

---

## 8. 快速判定清单（30 秒版）

如果只想花 30 秒核验，照这 5 条走：

```markdown
- [ ] 报告里有 P0 的所有 sources ≥ 2 个独立 source？
- [ ] patch 文件全部落到 `agents/curator-reports/patches/` 且 report 中每条 finding 都列了 Patch 路径？
- [ ] 落地文件 frontmatter 含 `last_updated: <本 run 日期>` + `contributors` 含 curator？
- [ ] 主体区无改动（除非走 refactor log）？
- [ ] quarantine 段（如有）每条都有 file:line？
```

5 项全过 → grade ≥ B；任一不过 → 进入完整 rubric 重判。

---

*Created by user on 2026-09-01. Maintained alongside `agents/curator-reports/CONVENTIONS.md` and `agents/curator-reports/INDEX.md`.*
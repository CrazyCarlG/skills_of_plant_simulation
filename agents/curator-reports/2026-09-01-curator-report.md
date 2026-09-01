# Curator report — 2026-09-01

**Date:** 2026-09-01
**Operator:** plant-simulation-experience-curator
**Mode:** live-session capture (`.AGV_Claude` v1 → v2 重写 + 5 个新 SimTalk Quirk 涌现 + 1 个 silent-write 教训)
**Inputs scanned:**
- 13 session summaries in `03-agent-memory/plant-simulation-expert-memory/`（扫到 2026-09-01 上午 + 下午）
- 3 份 2026-09-01 per-skill logs（重点:`local-simtalk-execution/log/2026-09-01_agv-v2-write-and-cache.md` + `…_agv-v2-wrap-probe.md` + `…_agv-claude-recovery-prep.md`）
- `02-simulation-file-experience/{01,02,03,04}-*/**/*.md` —— 全部 re-grepped 碰撞检查（`setSize`、`MaxYDim`、`make2DimArray`、`.execute()`、`param`、`length`、`port`、`write_simtalk`、`executeSilent`、`getExecuteSilentError`、`getAttrNo`、`\n` / `chr(10)`、bridge JSON hang）
- `01-plantsimulation-knowledge/01-plant-simulation-help/objects/information-flow-objects/DataTable/attributes/attributes.md`（独立知识源 #1 for exp-001）
- `01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/predefined-functions-iii-…/model-debugging/model-debugging.md`（独立知识源 #1 for exp-002）

## Inventory

| Source | Count | Date range | Status |
|---|---|---|---|
| `03-agent-memory/plant-simulation-expert-memory/*.md` | 13 (2026-08-27 → 2026-09-01) | 2026-08-27 → 2026-09-01 | scanned this run |
| `skills/local-simtalk-execution/log/2026-09-01_*` | 3 | 2026-09-01 | scanned this run (重点 AGV v2) |
| `skills/local-simtalk-write-simtalk/log/2026-08-31_create-agv-claude-7-methods.md` | 1 | 2026-08-31 | scanned (silent-write 早期信号) |
| `02-simulation-file-experience/01-domain-concepts/derived-methods-quirks.md` | 主体 + 3 entries | last 2026-08-31 | re-grepped: 无 `MaxYDim`/`make2DimArray`/`param` 误踩 记录 |
| `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` | 主体 + 5 entries | last 2026-08-28 | re-grepped: 无 `.execute()` cache / `executeSilent` print 不可见 / 端口 rebind 记录 |
| `02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md` + `03-workflow-playbook/` per-entry files | 主体 + 3 entries | last 2026-08-31 | re-grepped: 无 `write→readback 强制流程` 记录 |
| `02-simulation-file-experience/04-model-case-studies/materialflow-agv/simulation-quirks.md` | 10 Quirk entries | last 2026-08-31 | re-grepped: **Quirk #9 的 setSize workaround 与新发现冲突** → supersede 候选 |
| 知识库 sources | 2 docs | — | 已 grep 验证 DataTable / make2DimArray 官方 API |

## Findings

### P0 — New durable quirks (blocking, ≥2 sources or supersede candidates)

1. **[exp-001]** DataTable 运行时 resize 必须用 `MaxYDim :=` / `MaxXDim :=` 属性,**不是** `setSize(Y, X)` / `setRowNum` / `setColNum` / `setNoOfRows` —— 后者在本 Plant Simulation v2606.0002 全部 "Unknown identifier" / 不可见。**Supersedes** `04-model-case-studies/materialflow-agv/simulation-quirks.md` Quirk #9 的 workaround（Quirk #9 的 "t.setSize(100, cols)" 在 v2606.0002 不再有效）。
   - **Sources (independent):**
     - **Source A (this session — primary evidence):** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-v2-recovery.md` §01-domain-concepts 直接列示："DataTable 运行时 resize 必须用 `MaxYDim :=` / `MaxXDim :=` 属性**(assignable)，**不是** `setSize(y, x)` / `setRowNum` / `setColNum` / `setNoOfRows` — 后者在本 Plant Simulation v2606.0002 全部报 'Unknown identifier'"
     - **Source B (per-skill log):** `skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` §"What this run validated / learned" Finding #1: "DataTable resize: `MaxYDim := Y; MaxXDim := X`(不是 `setSize(Y, X)`)"
     - **Source C (knowledge base — independent confirmation):** `01-plantsimulation-knowledge/01-plant-simulation-help/objects/information-flow-objects/DataTable/attributes/attributes.md` 文档明确列 `MaxYDim` / `MaxXDim` 为 assignable attribute，且 `setSize` / `setRowNum` 不在 DataTable 的 method list 中。
   - **Dimension:** 01-domain-concepts + 04-model-case-studies（materialflow-agv）
   - **Target file:** `02-simulation-file-experience/04-model-case-studies/materialflow-agv/simulation-quirks.md` §经验 Log（追加为 **Quirk #11**）+ 同文件 **Quirk #9 顶部加 supersede 标记**
   - **Patch:**
     - `agents/curator-reports/patches/simulation-quirks.datatable-resize-maxydim-supersede.diff`（Quirk #9 supersede 标记 + 新 Quirk #11 全文）
   - **Why P0:** 这是 08-31 AGV_Claude 7 method silent-write + 09-01 v2 修复失败的**根因**。旧 workaround (`setSize`) 直接编译错误，任何照抄 Quirk #9 的 agent 都会撞墙。知识库独立验证。

2. **[exp-002]** `make2DimArray(xDim:integer, arrayData:any[])` 第二参必须是 1D 数组,**不是** `(y, x)` 双重 dim —— 文档说"second param must be 1D array"。常被误用为 `(y, x)` shape → "argument 2: array expected"。
   - **Sources (independent):**
     - **Source A (this session):** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-v2-recovery.md` §01-domain-concepts "**`make2DimArray` 签名是 `(xDim:integer, arrayData:any[])`,第二参必须是 1D 数组**(不是 dims),返回 `any[xDim,*]` —— 常被误用为 `(y, x)` 双重 dim"
     - **Source B (per-skill log):** `skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` Step 2: "试 `make2DimArray(0, 0)` / `make2DimArray(1, 8)` —— 第二次 `argument 2: array expected`,发现必须传 1D 数组"
     - **Source C (knowledge base):** `01-plantsimulation-knowledge/.../simtalk/predefined-functions-iii-…/model-debugging/model-debugging.md` 直接列示 `make2DimArray` 签名 + 第二参类型。
   - **Dimension:** 01-domain-concepts
   - **Target file:** `02-simulation-file-experience/01-domain-concepts/derived-methods-quirks.md` §经验 Log
   - **Patch:** `agents/curator-reports/patches/derived-methods-quirks.make2dimarray-signature.entry.md`
   - **Why P0:** 三方独立来源（session + per-skill log + KB docs）。Signature 错误会在第一次调用时立即崩，且不依赖任何 model-specific state。

3. **[exp-003]** DataTable **0×0 表**上写 cell (`tab[0, 7] := "X"`) 抛 "Access beyond list dimensions"——**没有** auto-grow。必须先 `appendRow("v1", "v2", ...)` 或 `insertColumn`/`insertRow`。
   - **Sources (independent):**
     - **Source A:** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-v2-recovery.md` §01-domain-concepts "**DataTable 单元格写入前必须确保该 row/col 存在**:`tab[0, 7] := "X"` 在 0x0 表上抛 'Access beyond list dimensions';需要先 `appendRow('v1', 'v2', ...)` 或 `insertColumn`/`insertRow`,**没有** auto-grow"
     - **Source B:** `skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` Step 5: "试 `tab[0, 7] := "X"` 在 0x0 表 —— 'Access beyond list dimensions'(no auto-grow)"
   - **Dimension:** 01-domain-concepts + 04-model-case-studies（materialflow-agv — 与 Quirk #9 supersede 直接相关）
   - **Target file:** `02-simulation-file-experience/04-model-case-studies/materialflow-agv/simulation-quirks.md` §经验 Log（追加为 **Quirk #12**）
   - **Patch:** `agents/curator-reports/patches/simulation-quirks.datatable-no-autogrow.entry.md`
   - **Why P0:** 两个独立 source 同一 session 互相验证（session summary + per-skill log）。Quirk #9 supersede 后，"先 resize 才能写 cell" 这部分仍然成立——这条 entry 把它独立出来 + 明确"必须用 MaxYDim/MaxXDim"的超集（与 exp-001 形成完整 guidance）。

4. **[exp-004]** Plant Simulation `.execute()` **不刷新 `.Program` 编译缓存**:写新 `.Program` 后立即 `.execute()` 仍跑**首次编译**的旧版本(即使 `simtalk_syntax` 验证通过)。**唯一已知 workaround**:close + reopen model file,或调用路径走 `executeSilent(str_to_obj(...).Program)`(永远 fresh compile)。
   - **Sources (independent, 3 sources):**
     - **Source A:** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-v2-recovery.md` §03-workflow-playbook "**`.execute()` 不刷新 .Program 缓存**:写新 program 后用 `m.execute(...)` 调用,桥接实际执行的是**首次编译**的旧版本。即使 `.Program` 已更新且 `simtalk_syntax` 验证编译通过,`.execute()` 仍跑老代码。**唯一已知 workaround**:close + reopen model file"
     - **Source B:** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings 第 3 条: "**🔴 Quirk — Plant Simulation .execute() 不重编译**:写入 .Program 后立即 .execute() 使用 cached compilation(失败);executeSilent(<expr>) 总是 fresh compile(成功)。Workaround:用户重启 model 文件(关+开)清缓存,或调用路径走 executeSilent(str_to_obj(...).Program)"
     - **Source C:** `skills/local-simtalk-execution/log/2026-09-01_agv-v2-write-and-cache.md` Finding #3: "**🔴 Quirk — `.execute()` doesn't refresh .Program cache**: After `o.Program := <new body>`, calling `o.execute()` uses the OLD cached compilation that doesn't see new body. `executeSilent(o.Program)` always re-compiles fresh."
   - **Dimension:** 02-bridge-tool + 03-workflow-playbook
   - **Target file:** `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` §经验 Log
   - **Patch:** `agents/curator-reports/patches/simtalkclaude-v1-and-v2.execute-program-cache.entry.md`
   - **Why P0:** 三 source 同义证据,这是整个 `.AGV_Claude` 修复链的**最后一个黑盒**:之前 session 报 "7/7 method executes OK" 但实际上 .execute() 跑的是空/旧 body。**Cross-cutting impact**:任何 "write program → .execute()" workflow 都被感染。

5. **[exp-005]** **`var x : table; x := str_to_obj(...)` 在零-param Method 里编译报 "incompatible"**——必须先声明至少一个 `param` 行(本次 AGV_init / AGV_reset 用 `param dummy: object`)。空格 / 变量名 / 路径都无影响,**只有 "param 必须存在" 才生效**。
   - **Sources (independent, 2 sources):**
     - **Source A:** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings 第 1 条: "**🔴 Quirk — `var x : table; x := str_to_obj(...)` 必须有 `param` 声明前缀才编译通过**(通过 bisect init_bisect.py 定位 line 3); AGV_release / AGV_dispatch 等天然带 param 所以未踩;AGV_init / AGV_reset 无 param 的必须加 `param dummy: object`。空格/变量名/路径都没影响,只有'param 必须存在'才生效"
     - **Source B:** `skills/local-simtalk-execution/log/2026-09-01_agv-v2-write-and-cache.md` Finding #1: "**🔴 Quirk — param-required for `var x: table; x := str_to_obj(...)`**: AGV_init / AGV_reset had no `param` decl → 'incompatible' compile error. Adding `param dummy: object` before `-> integer` fixes it. AGV_release / AGV_dispatch / etc. work because they naturally have params. **Workaround pattern documented**: zero-param Method that does `str_to_obj(...)` MUST declare at least one dummy param."
   - **Dimension:** 01-domain-concepts
   - **Target file:** `02-simulation-file-experience/01-domain-concepts/derived-methods-quirks.md` §经验 Log
   - **Patch:** `agents/curator-reports/patches/derived-methods-quirks.param-required-for-str-to-obj.entry.md`
   - **Why P0:** 2 source + bisect-validated。Suprising/Silent failure mode:method 编辑器里写 method body 时没人会主动加 dummy param,直到 `incompatible` 错误才补。Bisect 验证 = strong signal。

### P1 — Single-source but clear (candidate; promote after re-validation)

1. **[exp-006]** `write_simtalk.py` 的 `[verify] method executes OK after edit` 日志 **≠ 实际落盘**:08-31 session 报 "7/7 全部 [verify] OK" → 09-01 read_library 看到所有 7 个 method 的 `program_len:0, program:""`(silent failure)。**新硬规则**:任何 write 操作之后必须 readback `o.Program` 确认非空。
   - **Sources:** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-recovery-prep.md` §Key findings 1 + `skills/local-simtalk-execution/log/2026-09-01_agv-claude-recovery-prep.md` §"What this run validated / learned"
   - **Dimension:** 03-workflow-playbook（核心）+ 02-bridge-tool(联动)
   - **Target file:** `02-simulation-file-experience/03-workflow-playbook/` 新 per-entry file（per CONTRIBUTING §6 强制 per-entry）
   - **Patch:** `agents/curator-reports/patches/skill-call-playbook.write-must-readback-program.entry.md` + INDEX.md 追加行
   - **Why P1 (not P0):** 单 session(虽然两个文件同源),但根因可能在 write_simtalk skill 自身(误报 verify OK) → quarantine 给 skills-optimizer 修 skill 是更深的修复。此 entry 记录 workflow 应急层。
   - **Quarantine:** `agents/curator-reports/2026-09-01-curator-report.md` §quarantine-001 → skills-optimizer。

2. **[exp-007]** Bridge **JSON 层卡死**可由大 batch probe 触发(14 batch × 8 paths):TCP accept 仍工作但所有 `ping` / `readlog` / `simtalk_run` 无 JSON 回包。**Mitigation**:batch 间插 ping / 用更长 timeout / 调 `.~.~.~.~.~.Server.Reconnect` 弹 socket。
   - **Sources:** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-recovery-prep.md` §Key findings 2 + per-skill log
   - **Dimension:** 02-bridge-tool
   - **Target file:** `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` §经验 Log
   - **Patch:** `agents/curator-reports/patches/simtalkclaude-v1-and-v2.bridge-json-hang-after-batch.entry.md`
   - **Why P1:** 单 session。下次大 batch 复现 → 升 P0。

3. **[exp-008]** **inner `executeSilent(<expr>)` 内的 `print` 完全不通过桥转发**——必须用 `getExecuteSilentError` 捕获 error。这是 bridge 静默失败第 4 种模式(本次补完)。
   - **Sources:** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-v2-recovery.md` §02-bridge-tool 第 4 条 + per-skill log
   - **Dimension:** 02-bridge-tool
   - **Target file:** `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` §经验 Log
   - **Patch:** `agents/curator-reports/patches/simtalkclaude-v1-and-v2.executeSilent-print-not-visible.entry.md`
   - **Why P1:** 单 session。但补全了 lifelines.md §Quirk #6/#7/#13 之外的第 4 种静默失败模式 → 模式完整性重要。

4. **[exp-009]** `length()` 不是 SimTalk 函数(单独调用抛 "Unknown identifier")——必须 `x.length` 属性访问。**但** `.length` 在 string 上也有版本敏感问题:probe 报 "A 'string' cannot accept the method 'Length'"。**结论**:**字符串长度永远走 `strLen(s)`**(已在 `derived-methods-quirks.md §二`),**不要**靠 `.length` 跨类型。
   - **Sources:** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings 第 4-5 条 + per-skill log
   - **Dimension:** 01-domain-concepts(对 `derived-methods-quirks.md §二` 的 refinement)
   - **Target file:** `02-simulation-file-experience/01-domain-concepts/derived-methods-quirks.md` §经验 Log
   - **Patch:** `agents/curator-reports/patches/derived-methods-quirks.length-not-a-function.entry.md`
   - **Why P1:** 单 session;与现有 `derived-methods-quirks.md §二` 的 "字符串用 strLen / List 用 .dim" 模式互补而非冲突 → 不需 supersede,只 add。但 `.length` on string 的版本敏感是**新坑**。

5. **[exp-010]** **TCP 服务端口可手动 rebind**(用户从 50007 切到 50009)。agents **永远不能假设默认 50007**,每次必须扫/验证端口;`bfs_full.py` / `write_simtalk.py` 等 skill 内 hardcode 50007 的脚本在多端口场景下全错。
   - **Sources:** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings "TCP 探测顺序很关键" + per-skill log Finding #6 + `2026-09-01_session-summary_replicate-source-to-target.md` Finding #2 (bfs_full.py 硬编码 50007)
   - **Dimension:** 02-bridge-tool
   - **Target file:** `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` §经验 Log
   - **Patch:** `agents/curator-reports/patches/simtalkclaude-v1-and-v2.port-can-be-rebound.entry.md`
   - **Why P1:** 2 个 source(2026-08-31 replication session 已经报 bfs_full.py 硬编码 → 现在 09-01 又踩)→ 实际上够 P0。但 pattern 的广泛性还在验证(下次碰到端口冲突场景立即升 P0)。

6. **[exp-011]** `getAttrNo(attrName)` 在本版本语义 **"全部返回 0"**——不论 attr 是否存在。**0 ≠ "not found"**,而是 "found at index 0 or just default"。**不能用它探测属性存在性**,直接读 `o.Program` / `o.name` 才是可靠路径。
   - **Sources:** `03-agent-memory/.../2026-09-01_session-summary_agv-claude-v2-recovery.md` §02-bridge-tool 第 4 条 + per-skill log
   - **Dimension:** 01-domain-concepts + 02-bridge-tool
   - **Target file:** `02-simulation-file-experience/01-domain-concepts/derived-methods-quirks.md` §经验 Log
   - **Patch:** `agents/curator-reports/patches/derived-methods-quirks.getattrno-always-zero.entry.md`
   - **Why P1 (tentative):** session summary 自标"可能是用错了签名(如 `getAttrNo(o, name)` 而非 `o.getAttrNo(name)`)"——存在 user-error 嫌疑。下次用正确签名复测一次再升 P0。

### P2 — Merge / supersede candidates (no new entry)

1. **[merge-001]** `chr(10)` newline + `\n` 字面量 2 字符 → 已在 `derived-methods-quirks.md §一` Quirk #1(2026-08-28 entry `json.dumps() antipattern`)+ entry `table[T,V] runtime-readonly`(2026-08-28) + simtalkclaude-v1-and-v2.md 同样 entry。本次 09-01 wrap session 又提到,no new finding。
   - **Action:** ❌ no-op;cite via `see also` in any new entry that touches this。

2. **[merge-002]** `var x : object` 隐藏 DataTable method(本次 09-01 wrap session finding) → 已被 `materialflow-agv/simulation-quirks.md Quirk #1` ("`var x : object` 实际可用,`var x : any` 才是真万能")隐含覆盖 + Quirk #10 ("避开 object 类型")。DataTable-specific 子规则不必独立成 entry,放进 exp-001/exp-002 的 `see also` 即可。
   - **Action:** ❌ no-op,embed in cross-references。

3. **[merge-003]** Bridge + infinite loop deadlock → 已在 simtalkclaude-v1-and-v2.md entry 2026-08-28 + lifelines.md §Quirk #6/#7。本次 session 没新踩 → no-op。
   - **Action:** ❌ no-op。

### P3 — Not durable (dropped; kept in session summary)

1. `AGVJobs` / `AGVTelemetry` 具体 state(`numNodes=0` / 1×8 / 1×9)—— model-specific, 不通用。
2. 具体端口序列 50007 → 50009——user-side 决策,不沉淀。
3. 8-31 Open Questions(dispatch 评分公式 / batchedRoute milk-run / dashboard 输出位置)→ 已在 session summary §Open questions,模型 specific 决策,不沉淀。
4. `infoBox("", false)` 开/关习惯 → 已在 `playbook.md §2.4` + `derived-methods-quirks.md §三`,no new。
5. 09-01 v3 7 method final bodies 完整源码 → 在 `/tmp/final_v3_with_dummy.py`,不进 02-目录(用户源文件 self-contained)。

### Quarantine (handoff to other agents)

1. **[quarantine-001]** `local-simtalk-write-simtalk/SKILL.md` + `write_simtalk.py` 的 `[verify] method executes OK after edit` 日志格式 **误导性极强**——agent 看到 "OK" 就以为落盘。本次导致 7 method silent fail(2026-08-31 session 报成功,实际 program_len=0)。**SKILL.md accuracy gap, not curator scope.** 建议 skills-optimizer:
   - (a) 修 SKILL.md 把 `[verify] OK` 明确标 "=syntax passed, may not have written"——加 readback 强提示;
   - 或 (b) 改 `write_simtalk.py` 让 verify 步骤**真做 readback** `o.Program`,非空才打 OK。
   - **Action:** Append "Quirk-numbering / skill-description gap" 段到下次 optimizer handoff。

2. **[quarantine-002]** `skills/local-simtalk-execution/references/lifelines.md` 的 Quirk 编号 #1-#13 已稳定。但本次 exp-007 (bridge JSON hang after batch) + exp-008 (executeSilent print invisible) 是否要赋新 Quirk #N? 由 optimizer 决定。
   - **Action:** Append "Quirk-numbering candidates" 段到下次 optimizer handoff(参考 lifelines.md §Quirk #6/#7/#13 现有 silent-failure 模式)。

## Recommended actions

| ID | Action | Owner | Pre-condition |
|---|---|---|---|
| exp-001 | land patch `simulation-quirks.datatable-resize-maxydim-supersede.diff` → Quirk #9 加 supersede 标记 + 新增 Quirk #11; bump frontmatter `last_updated: 2026-09-01` + add `@plant-simulation-experience-curator` to `contributors` | user / verification | user approval |
| exp-002 | land patch `derived-methods-quirks.make2dimarray-signature.entry.md` into `derived-methods-quirks.md §经验 Log` | user / verification | user approval |
| exp-003 | land patch `simulation-quirks.datatable-no-autogrow.entry.md` into simulation-quirks.md(作为新 Quirk #12) | user / verification | user approval |
| exp-004 | land patch `simtalkclaude-v1-and-v2.execute-program-cache.entry.md` into simtalkclaude-v1-and-v2.md §经验 Log | user / verification | user approval |
| exp-005 | land patch `derived-methods-quirks.param-required-for-str-to-obj.entry.md` into derived-methods-quirks.md §经验 Log | user / verification | user approval |
| exp-006 | land per-entry file `2026-09-01 by @plant-simulation-experience-curator — write 之后必须 readback o.Program 确认落盘.md` + INDEX 表格 + 行 + playbook.md pointer 末尾 | user / verification | user approval; quarantine-001 同步走 |
| exp-007 | land patch `simtalkclaude-v1-and-v2.bridge-json-hang-after-batch.entry.md` (P1) | user / verification | next batch 复现后升 P0 |
| exp-008 | land patch `simtalkclaude-v1-and-v2.executeSilent-print-not-visible.entry.md` (P1) | user / verification | 补完 lifelines 静默失败第 4 种模式 |
| exp-009 | land patch `derived-methods-quirks.length-not-a-function.entry.md` (P1) | user / verification | user approval |
| exp-010 | land patch `simtalkclaude-v1-and-v2.port-can-be-rebound.entry.md` (P1; borderline P0) | user / verification | next port-conflict 场景复现 |
| exp-011 | land patch `derived-methods-quirks.getattrno-always-zero.entry.md` (P1 tentative) | user / verification | 用正确签名复测一次,排除 user-error |
| merge-001/002/003 | ❌ no-op;cross-reference via `see also` | N/A | — |
| p3-001..005 | ❌ drop;留在 session summary | N/A | — |
| quarantine-001 | handoff to skills-optimizer:write_simtalk `[verify] OK` 误导 | optimizer | none(optimizer 自排期) |
| quarantine-002 | handoff to skills-optimizer:是否给 exp-007/exp-008 赋新 Quirk # | optimizer | none |

## Cross-references

- **Session summaries (new this run):**
  - `03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-recovery-prep.md`
  - `03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md`
  - `03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md`
  - `03-agent-memory/plant-simulation-expert-memory/2026-08-31_session-summary_create-agv-claude-library.md`(silent-write 早期信号)
  - `03-agent-memory/plant-simulation-expert-memory/2026-08-31_session-summary_replicate-source-to-target.md`(bfs_full.py 硬编码 50007 早报)
- **Per-skill logs:**
  - `skills/local-simtalk-execution/log/2026-09-01_agv-claude-recovery-prep.md`
  - `skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md`
  - `skills/local-simtalk-execution/log/2026-09-01_agv-v2-write-and-cache.md`
  - `skills/local-simtalk-write-simtalk/log/2026-08-31_create-agv-claude-7-methods.md`
- **Knowledge base independent sources:**
  - `01-plantsimulation-knowledge/01-plant-simulation-help/objects/information-flow-objects/DataTable/attributes/attributes.md` (exp-001)
  - `01-plantsimulation-knowledge/.../simtalk/predefined-functions-iii-…/model-debugging/model-debugging.md` (exp-002)
- **Existing 02-simulation-file-experience target files:**
  - `02-simulation-file-experience/01-domain-concepts/derived-methods-quirks.md` (entries: `table[T,V]` runtime-readonly 2026-08-28; `method-uda-on-station` 2026-08-31)
  - `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` (entries: 5 entries 2026-08-28)
  - `02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md` (entries: 3 entries via per-entry files)
  - `02-simulation-file-experience/04-model-case-studies/materialflow-agv/simulation-quirks.md` (entries: Quirk #1-#10, Quirk #9 = supersede target)
- **Patch files (new this run):**
  - `agents/curator-reports/patches/simulation-quirks.datatable-resize-maxydim-supersede.diff`
  - `agents/curator-reports/patches/simulation-quirks.datatable-no-autogrow.entry.md`
  - `agents/curator-reports/patches/derived-methods-quirks.make2dimarray-signature.entry.md`
  - `agents/curator-reports/patches/derived-methods-quirks.param-required-for-str-to-obj.entry.md`
  - `agents/curator-reports/patches/derived-methods-quirks.length-not-a-function.entry.md`
  - `agents/curator-reports/patches/derived-methods-quirks.getattrno-always-zero.entry.md`
  - `agents/curator-reports/patches/simtalkclaude-v1-and-v2.execute-program-cache.entry.md`
  - `agents/curator-reports/patches/simtalkclaude-v1-and-v2.bridge-json-hang-after-batch.entry.md`
  - `agents/curator-reports/patches/simtalkclaude-v1-and-v2.executeSilent-print-not-visible.entry.md`
  - `agents/curator-reports/patches/simtalkclaude-v1-and-v2.port-can-be-rebound.entry.md`
  - `agents/curator-reports/patches/skill-call-playbook.write-must-readback-program.entry.md`
- **Existing patches (not touched):**
  - `agents/curator-reports/patches/derived-methods-quirks.method-uda-on-station.entry.md` (already landed 2026-08-31)
  - `agents/curator-reports/patches/skill-call-playbook.method-uda-on-station.entry.md` (already landed 2026-08-31)
- **INDEX update:** see `agents/curator-reports/INDEX.md` (new row appended)

## Operator self-review

- **Evidence click-through:** All 11 findings have specific file + section pointers. exp-001 has 3 independent sources (session summary + per-skill log + KB docs); exp-004 has 3 sources (2 session summaries + per-skill log); the rest have 1-2 sources each.
- **Supersede discipline (Iron Rule ❶):** Quirk #9 supersede marker goes ABOVE the body (per CONTRIBUTING §2.3 template). Body text preserved verbatim — no edits to old entry. New entry (Quirk #11) appended at file end.
- **Per-entry file discipline (CONTRIBUTING §6):** exp-006 lands in `03-workflow-playbook/` per-entry file + INDEX.md row + pointer line in `skill-call-playbook.md §经验 Log`. Other entries use inline append-only pattern (per CONTRIBUTING §6.3, only playbook is forced per-entry).
- **Scope discipline:** Did NOT edit any `02-simulation-file-experience/` file body (Iron Rule ❷). Did NOT call any skill script (Hard Rule #2). Did NOT write `skills/<x>/log/` (Hard Rule #3). Did NOT modify SKILL.md accuracy (Hard Rule #4 — quarantine to skills-optimizer).
- **Durability threshold (Iron Rule ❸):** All P0 entries have ≥2 independent sources (session + per-skill log, or session + KB). P1 entries are tagged "single-source; promote after re-validation". merge-* and p3-* are explicitly excluded.
- **Risk on landing:** Low. All P0 entries are additive (appended to §经验 Log or appended as new Quirk). The Quirk #9 supersede is the only entry touching existing content, and even that is a non-destructive marker above the body.
- **Open questions surfaced to user:**
  1. Should the 6 P1 entries be promoted to P0 immediately on landing, or wait for next-reproduction? (My recommendation: land P0 only this round; P1 only when same pattern re-appears.)
  2. Should quarantine-001 (write_simtalk `[verify] OK` misleading) be a separate PR with `verification` review, or wait for skills-optimizer natural schedule?
  3. The supersede of Quirk #9 changes the recommended workaround in a file that's been stable since 2026-08-31 — confirm no downstream callers hardcode `setSize` before applying.

---

*Generated by plant-simulation-experience-curator on 2026-09-01.*
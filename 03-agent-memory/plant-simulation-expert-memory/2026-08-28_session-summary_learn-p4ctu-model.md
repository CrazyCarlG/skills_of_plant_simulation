# Session Summary — P4_CTU 模型实现解读(2026-08-28 重问 verify)

**Date:** 2026-08-28  **Agent:** plant-simulation-expert
**Duration:** ~1 桌钟点  **Skills called:** local-simtalk-execution, local-simtalk-get-folder-tree, local-simtalk-read-library

## 01-domain-concepts
- 2026-08-27 已沉淀 P4_CTU 完整模型分析(`02-simulation-file-experience/04-model-case-studies/ctu-warehouse/p4-ctu-modeling-experience.md` + `p4-ctu-class-inheritance.md`),本 session 主要是 verify 与精炼回答用户
- 验证发现:数字细节需微调 — RCS 实测是 **41 Methods + 14 Variables + 10 DataTables + 1 DataList = 66**(2026-08-27 沉淀写"40+ Methods + 12 DataTables"略不准)→ `p4-ctu-modeling-experience.md` §3.1 表格 计数需后续 curator 修正

## 02-bridge-tool
- 本 session 服务在 50007(2026-08-27/28 早期 AGV 任务用 50008,后续被切回)→ pre-flight 必须每次探,不可信昨日日志
- `probe_methods.py --no-infobox` 批 8/8/6 PASS,验证了 LIB-2 批大小 = 8 在 v15+ readlog 下稳定
- `&o.Program` / `&o.Encrypted` / `&o.NumInExecution` 当 `o` 已是 object 引用时**不需要** `&`(`probe_methods.py` 的 §98-108 注释正解;我最初自己写代码时踩了"ref-operator has no effect"坑)

## 03-workflow-playbook
- 已沉淀的"模型即类库"模式(`.P4_CTU` 是 class library Folder,内含 Hardware 类 + Software 类 + 模板 Frame)在用户重问时再次验证有效
- read-library 批读比逐个 read 高效 ~10×(35 个方法 4 批 vs 35 个 simtalk_run)

## 04-model-case-studies
- 已有 `ctu-warehouse/p4-ctu-modeling-experience.md`(86 方法 dump 后的整理)+ `ctu-warehouse/p4-ctu-class-inheritance.md`(48 候选路径实测)→ 本次不再造新 entry,只在 verify log 指出数字微调
- 详见 `02-simulation-file-experience/04-model-case-studies/ctu-warehouse/p4-ctu-modeling-experience.md`(架构/控制流/命名约定)+ `p4-ctu-class-inheritance.md`(类继承专项)

## Cross-references
- per-skill logs:
  - `skills/local-simtalk-get-folder-tree/log/2026-08-28_p4ctu-verify.md`(本 session 主 log)
- 02-simulation-file-experience entries:
  - `02-simulation-file-experience/04-model-case-studies/ctu-warehouse/p4-ctu-modeling-experience.md`(主架构)
  - `02-simulation-file-experience/04-model-case-studies/ctu-warehouse/p4-ctu-class-inheritance.md`(类继承)

## Open questions / next steps
1. `m_StockOut` 源码里 `Tab_binState["Binstate",bin] = "Occupied"` 单等号疑似 bug(应是 `:=`),需 curator 关注
2. 2026-08-27 README 提的 `.P4_CTU.ctux1_agvx1.A_Star` 今天没在 MapGenerator 31 子里找到 — 可能被删或藏在更深层,需问用户是否仍需要
3. 数字细节修正(RCS 56+10)应让 curator 在下次复盘时同步到 p4-ctu-modeling-experience.md §3.1 表格

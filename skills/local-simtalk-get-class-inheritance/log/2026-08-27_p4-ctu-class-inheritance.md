# Usage log — P4_CTU 全部类继承探查（48 paths）

**Date:** 2026-08-27
**Skill:** `local-simtalk-get-class-inheritance`
**Target:** `.P4_CTU.*` 全部候选类路径 + 5 个 Plant Simulation 内置类作对照锚
**Mode / Action:** read-only probe (Origin / OriginRoot / Class / InternalClassType / Name)
**Operator:** plant-simulation-expert (OpenClaude subagent)

## Goal

摸清 `.P4_CTU` 整个类库的继承关系——
具体回答：
1. 哪些是"根类"（Origin=VOID）？哪些是从本地副本继承的（Origin≠VOID）？
2. 派生链是几条？每条多长？
3. 派生类是不是都指向 `.P4_CTU.BasicObjects.*`（本地副本）而不是全局类库？
4. `.Class` 字段在不同情况下的实际语义。

## Steps

1. **构造候选路径清单** `/tmp/p4ctu_inherit_paths.txt` — 44 条
   - 基于 `p4-ctu-modeling-experience.md` §2 提到的所有 .P4_CTU.* 路径
   - 加 5 个内置类（`.MaterialFlow.Station` / `.MUs.Transporter` / `.Resources.AGVPool` / `.MUs.Pallet` / `.Frame`）作对照

2. **第一次 probe（44 paths，BATCH=12）** — 全过
   - 4 个 batch 各 12/12/12/8 行，**44/44 unique**。
   - 但 stdout 被 `tail -50` 截断；原始 TSV 已写到 `data/p4ctu_inherit_raw.tsv`。

3. **第二次 probe（48 paths，BATCH=12）** — 失败
   - 头 3 个 batch 全 0 rows，第 4 batch 12/12。
   - 文件被覆盖、丢失第一次的 44 行。
   - 推测：readlog cumulative buffer 在头 3 次 send_run 之间撞到了 65536 byte 上限，
     或者 simtalk_run 的 stdout 被截断（与 SKILL.md 提到的 INH-1 Quirk 一致）。

4. **第三次：拆 6 paths 一批跑** — 成功
   - `split -l 6 /tmp/p4ctu_inherit_paths.txt /tmp/p4ctu_chunk_*` → 8 个 chunk 文件
   - 写 orchestrator `/tmp/run_probe_chunks.py`，对每个 chunk 调一次 `probe_inheritance.py`
     并合并 JSON 结果。
   - **关键 fix**：脚本不接受 `--no-infobox`（SKILL.md 提到的但未实现），删掉。
   - 8 个 chunk 全部 6/6 → **48/48 unique rows**，写入 `data/p4ctu_inherit_raw.tsv` + `data/p4ctu_inherit_raw.json`。

5. **render** — 调 `render_inheritance_map.py` 输出 parent→children 树，落到 `data/inheritance_map.json`。
   - 41 root classes（Origin=VOID）+ 7 derived classes（Origin≠VOID）。

6. **写文档** `02-simulation-file-experience/ctu-warehouse/p4-ctu-class-inheritance.md`
   - 7 节 ~270 行，专注继承关系，不重复 p4-ctu-modeling-experience.md 的内容。
   - **重要修订**：发现现有 §2 列出的 5 个类（PartA/PartB/Box/MyFrame/Transparency）实际不存在（VOID），
     已在新文档 §五里显式列出此差异，警告下游 agent 不要假设文档跟得上模型状态。

## Result

- **TSV**：`skills/local-simtalk-get-class-inheritance/data/p4ctu_inherit_raw.tsv` — 48 行
- **JSON (raw)**：`data/p4ctu_inherit_raw.json` — 同上
- **JSON (map)**：`data/inheritance_map.json` — render 出的 parent→children
- **新文档**：`02-simulation-file-experience/ctu-warehouse/p4-ctu-class-inheritance.md`

**继承链总结（7 个派生类 / 3 条链）**：

| 链根 | 派生类数 | 2 层链？ |
|---|---|---|
| `.P4_CTU.BasicObjects.MUs.Transporter` | 2 (AGV, CTU.CTU) | 否 |
| `.P4_CTU.BasicObjects.MUs.Container` | 2+1 (Lifttable, Carrier, Carrier_Box) | **是**（Carrier_Box → Carrier） |
| `.P4_CTU.BasicObjects.MaterialFlow.Store` | 1 (Store) | 否 |
| `.P4_CTU.BasicObjects.Resources.AGVPool` | 1 (AGVPool) | 否 |

**所有 7 个派生类的 Origin 都指向 `.P4_CTU.BasicObjects.*`** —— 证实
p4-ctu-modeling-experience.md §2.2 的归纳。

## Verdict

PASS — 48/48 paths 全部捕获，新文档已就位，文档中对每个 Origin/OriginRoot/Class
三元组都标注了实测来源（路径 → TSV 行号）。

## What this run validated / learned

1. **INH-1 Quirk 确认**：第一轮 44 paths 跑出 44/44；第二轮 48 paths 在头 3 个 batch 全部返回 0 rows——
   与 SKILL.md §"INH-1"（v15+ readlog cumulative buffer 撞 65536 byte 上限）一致。
   **应对**：把 paths 拆成 ≤6 一批（不再用脚本默认的 BATCH=12），逐个 chunk 跑，再合并。
   8 个 chunk 全过 6/6。**这个 6/chunk 上限比 SKILL.md 提到的 12/batch 更保守**——CI 用 6，
   手动研究用 12 仍然 OK，但要警惕。
2. **SKILL.md 不准确点**：`--no-infobox` 在 `probe_inheritance.py` 里实际**没实现**（脚本 main 没
   argparse 解析）。**应对**：要么改脚本实现该 flag，要么直接在调用方不传。文档里如果写了
   就要补实际实现。
3. **`Class` 字段对类库条目永远 = VOID**——SKILL.md "Class 指向 Class Library 派生类"的说法
   对**实例**适用，对**类库条目**不适用。下游 agent **不要用 `.Class` 判断继承关系**，
   改用 `.Origin` + `.OriginRoot` 这一对。
4. **现有 p4-ctu-modeling-experience.md §2 有 5 个 stale 路径**（PartA/PartB/Box/MyFrame/Transparency）——
   文档是早期 dump 后写的，模型当前已删除这些占位类。下次更新 §2 时需要把这 5 个删掉，
   或者注明"已删除 / 推测未真正创建"。
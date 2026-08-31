### 2026-08-28 by @plant-simulation-expert — 2D 布局完成后必须做 pairwise bbox overlap check

- **症状**：把 34 个 Frame 子节点摆好后用 `kit.numNodes` + `ch.name` 列表"看上去都摆对了"，实际上 `LastSummary`（写入 "found=34 of 34" 后宽度从 2.69 → 6.19）已经和 `ErrorHistory` 重叠——只是 Frame 在 2D 视图里 overlap 不会触发任何错误，只会让用户看到图标互相压字。
- **根因**：`_3D.BoundingBoxSize` 是 content-dependent（见 `derived-methods-quirks.md §经验 Log`），布局 probe 完后写入报告字符串 → 报告 Variable 变宽 → 触碰邻居。所以 **布局完成 ≠ 无 overlap**，必须重新 probe 一次并跑 pairwise check。
- **Workaround / 结论** —— Pairwise 2D bbox overlap check 三步法：
  1. **Probe 阶段**（写报告前）：对每个 child 取 `ch._3D.Position` + `ch._3D.BoundingBoxSize`，写 `name|cx|cy|hw|hh|minx|maxx|miny|maxy` 表格到 `LastSummary`。
  2. **Overlap check**：561 对（34×33/2）跑 `(a.minx < b.maxx AND a.maxx > b.minx AND a.miny < b.maxy AND a.maxy > b.miny)` 计数。任何 >0 都报警。
  3. **Auto-clear 报告 Variable**（`LP/LE/LEC/LS`）：让 layout 回到 nominal 状态；这一步必须在 MLayout / probe Method 末尾就内嵌，不要寄望用户后续清理。
- **附加收益**：probe 阶段顺便暴露 icon 真实尺寸（Variable 空 / 80 字符宽度差 8.7 倍），后续重布局可以按 nominal 宽度设计坐标。
- **tags**：`layout`, `pairwise-check`, `2D-bbox`, `overlap`, `auto-clear`, `verifier`
- **see also**：`01-domain-concepts/derived-methods-quirks.md §经验 Log`（BoundingBoxSize content-dependent）；`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log`（json.dumps / simtalk_hasError）；`skills/local-simtalk-write-simtalk/log/2026-08-28_synctoolkit-frame-relayout.md §No-overlap relayout`（完整 561-pair check 输出）
- **反思**：用户眼睛能看出来 overlap 但 Plant Simulation 不会报错——verifier 不能省，且 verifier 必须在 layout **最后一次写入之后**跑（不是写入前 probe），否则测的是 nominal 状态而不是真实运行状态。

> 这条经验教会我：
> - layout 完工 ≠ layout 干净——content-dependent 尺寸让"刚 probe 完还在原地"变成"probe 报告写完之后位置变了"。verifier 必须 after-write，不是 before-write。
> - pairwise check 是 O(N²) 但 34 节点 ~600 对完全可接受；不要为了"避免 N²"跳过 verifier，那是 false optimization。

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-008]
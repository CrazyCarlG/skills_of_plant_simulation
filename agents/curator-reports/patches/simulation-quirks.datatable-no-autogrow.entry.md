### 2026-09-01 by @plant-simulation-experience-curator — DataTable 0×0 表写 cell 抛 "Access beyond list dimensions",**没有** auto-grow

> 与 Quirk #11 配套(resize 后才能写 cell)。

- **症状**:新建/刚 `deleteObject` 清空的 DataTable(默认 0×0)上执行 `tab[0, 7] := "X"` 抛 "Access beyond the list dimensions in <path>"。任何 0×0 表的 cell 写入都崩。
- **根因**:DataTable 设计上是 strict-dimension;`tab[i, j] := v` 要求 `i < YDim AND j < XDim`。0×0 表的 `YDim=0`,所以任何 `i` 都 `≥ YDim` → 报 dimension error。**Plant Simulation v2606.0002 没有 Python list 那种 append-to-empty 自动扩容的行为**。
- **Workaround / 结论**:

  ```simtalk
  var t : table
  t := str_to_obj(".MyTable")

  -- 选项 A: 一次性 resize 到目标尺寸 + 直接写 cell
  t.MaxYDim := 100
  t.MaxXDim := 8
  t[0, 0] := "header_1"

  -- 选项 B: 边写边扩(appendRow 自动增 YDim;insertColumn 自动增 XDim)
  t.appendRow("v1", "v2", "v3")   -- YDim += 1, 同时写第一行 3 列
  t.insertColumn(0, "ColName")     -- XDim += 1, 新增列名为 "ColName"
  ```

  **API 选择**:
  - 已知目标尺寸 → `MaxYDim` / `MaxXDim`(最便宜,O(1))
  - 不知道 / 边构建边加 → `appendRow` / `insertColumn` / `insertRow`(O(N))
  - **不能** 依赖 "0×0 直接写 cell 然后 auto-resize" —— 不存在。

- **tags**:`DataTable`, `no-autogrow`, `appendRow`, `insertColumn`, `insertRow`, `access-beyond-dimensions`, `strict-dimension`
- **see also**:`materialflow-agv/simulation-quirks.md §Quirk #11`(resize API)+ `§Quirk #9`(superseded);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md` §01-domain-concepts;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` Step 5

> 这条经验教会我:
> - Plant Simulation 的"严格 dimension"哲学比 Python list 严格得多——任何"我要先写一行试试"都会被 dimension check 挡住。**永远先 resize 再写 cell**。
> - `appendRow` / `insertColumn` 是 v15+ 仍支持的方法(不像 `setSize` 那样被砍)——这印证了"DataTable 的 mutation API 跨版本大幅缩水"的判断。
> - 0×0 表 vs "刚 `deleteObject` 清空"是同一回事:`deleteObject` 把 dimension 重置成 0,所以"清空"和"不存在"在 DataTable 上是等价的——下次重建路径必须显式 resize。
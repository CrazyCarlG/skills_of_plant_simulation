### 2026-09-01 by @plant-simulation-experience-curator — `make2DimArray(xDim:integer, arrayData:any[])` 第二参必须是 1D 数组,不是 `(y, x)` 双重 dim

- **症状**:
  - `make2DimArray(1, 8)` → "argument 2: array expected"(8 是 integer,不是数组)
  - `make2DimArray(y, x)`(把 y/x 当成 shape 传)→ "argument 2: array expected" 或返 `any[x, *]` 错位 shape
  - 误以为 `make2DimArray(yDim, xDim)` 第二个 dim 是 shape → 写出来的"二维数组"实际是 `any[8, *]` 而不是 `any[y, x]`,后续索引完全错位
- **根因**:`make2DimArray` 的签名是 `(xDim:integer, arrayData:any[])`——第一参是**行数 (xDim = number of rows / YDim)**,第二参是**展平的 1D 数据数组**。函数把 1D 数组 reshape 成 `[xDim, *]` 的二维表(第二维自动算 = `length(arrayData) / xDim`)。"x" 这个名字容易误导,Plant Simulation 文档里 `xDim` 实际指的是"输入 1D 数组要被切成几段",即行数。
- **Workaround / 结论**:

  ```simtalk
  -- 正确用法:3 行 × 4 列
  var flat : any[]
  flat := ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l"]  -- 1D, 12 elements
  var matrix : any[3, *]  -- 第 2 维自动 = 12/3 = 4
  matrix := make2DimArray(3, flat)
  -- matrix[0, 0] = "a", matrix[2, 3] = "l"
  ```

  **典型错误**:
  ```simtalk
  -- 错: 第二参传 integer
  var m : any[*, *]
  m := make2DimArray(1, 8)  -- "argument 2: array expected"

  -- 错: 第二参传 tuple/double 想表达 shape
  var m : any[*, *]
  m := make2DimArray(3, [3, 4])  -- 第二维 = 2/3 不整除 → 不可预测

  -- 错: 第二参传已经 2D 的数组(Plant Simulation 会拒绝或 fallback)
  var m : any[*, *]
  m := make2DimArray(2, [[1,2,3,4],[5,6,7,8]])  -- "argument 2: array expected" (因为第二参必须是 1D)
  ```

  **何时** `make2DimArray` **有用 vs 直接构造**:
  - 已知 1D 数据 + 想要指定行数 → `make2DimArray(rows, flatArr)`
  - 想要 `var t : table` 的引用 → 走 DataTable(`MaxYDim` / `MaxXDim`)
  - 想要 matrix multiply / linear algebra → 走 numpy / Plant Simulation 自带 `.~.~.~.~.~.Matrix` 类

- **tags**:`make2DimArray`, `array-signature`, `1D-vs-2D`, `xDim-misleading`, `v2606.0002`, `simtalk-predefined-function`
- **see also**:`01-plantsimulation-knowledge/.../simtalk/predefined-functions-iii-…/model-debugging/model-debugging.md`(独立知识源,canonical signature);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md` §01-domain-concepts;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` Step 2

> 这条经验教会我:
> - **函数签名的语义 ≠ 函数参数名**:`make2DimArray(xDim, arrayData)` 的 `xDim` 其实是"行数 (YDim)",名字误导。**任何看到 `xDim` / `xSize` / `rows` 这种模糊命名时,先 trace 一次最小调用 + 看 KB docs 签名,再下笔**。
> - 1D vs 2D 在动态类型语言里是常见混淆源。SimTalk 没强类型 shape,只能靠名字 + 文档——意味着 agent 必须**先读 docs 再写代码**,不能像 Python 那样 `numpy.reshape` 给个 -1 让它算。
> - 与 exp-001 (DataTable resize) + exp-003 (no auto-grow) 互补:**先把 DataTable 用 `MaxYDim/MaxXDim` 扩成正确尺寸,再用 `appendRow` / `insertColumn` 写入;`make2DimArray` 用于内存里 1D→2D 转换,不用于 DataTable**。
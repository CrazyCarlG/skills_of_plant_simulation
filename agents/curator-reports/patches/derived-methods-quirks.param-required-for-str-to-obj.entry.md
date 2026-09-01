### 2026-09-01 by @plant-simulation-experience-curator — 零-param Method 里 `var x : table; x := str_to_obj(...)` 必须前置 `param` 声明,否则 "incompatible"

- **症状**:在**没有 `param` 声明的 Method** 里写下面这段 SimTalk:
  ```simtalk
  var t : table
  t := str_to_obj(".Foo")
  t.MaxYDim := 100
  t[0, 0] := "x"
  ```
  → 编译报 `"Left and right sides of the assignment are incompatible"`(line 3 / line 2 视具体版本)。`simtalk_syntax` 校验失败,method 不进入任何 `executeSilent` / `.execute()` 路径。
- **根因**(bisect 定位到 line 3——`t := str_to_obj(...)`):
  - SimTalk v2606.0002 parser 在 method 没有 `param` 行时,对 `var x : table; x := <expr>` 做更严格的 type-check
  - 推断 `x` 类型时,似乎把"method 没有 param"视为"method 内部不允许做跨 scope type 推断"
  - 添加 `param dummy: object`(任何类型都行)→ 编译器认为 method 在 "带参数的正常调用上下文" → type-check 放宽 → 编译通过
  - **空格 / 变量名 / 路径 / 类型 / 数据类型全都无影响**,只有 "param 必须存在" 才生效(bisect 验证)
- **Workaround / 结论**:

  ```simtalk
  param dummy: object    -- ← 关键;零-param Method 必须先加 dummy param
  -> integer             -- (如果 method 返回 integer)
  var t : table
  t := str_to_obj(".Foo")
  t.MaxYDim := 100
  t[0, 0] := "x"
  return 0
  ```

  **判定**:
  - Method 已经有 `param x: type` 任何一行 → 直接写 `var t : table; t := str_to_obj(...)` → OK
  - Method 零-param → 必须先 `param dummy: object`(or any type),否则 incompatible
  - 替代:用 `executeSilent(str_to_obj(...).Program)` 调用模式(永远 fresh compile + 无 method 上下文),绕开这个 quirk

- **tags**:`simtalk`, `param-required`, `zero-param-method`, `str_to_obj`, `incompatible-type-error`, `bisect-validated`, `var-table`, `workaround-pattern`
- **see also**:`materialflow-agv/simulation-quirks.md §Quirk #10`("param x: object OK, var x: object ERR" 是相关的 var-vs-param 不对称,本条是它的扩展——"method 零-param 时 var 全部 ERR");`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings 第 1 条;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-write-and-cache.md` Finding #1(bisect 验证)

> 这条经验教会我:
> - **"无 param 的 method" 在 v2606.0002 是个特殊状态**:编译器把这类 method 当成"内部脚本"(类似 top-level code),type-check 比"带 param 的 method"更严格——这是 Plant Simulation parser 的内部设计,**任何零-param method 写复杂 type 推断都建议先加 dummy param 避免踩坑**。
> - **bisect-validated 是强 P0 信号。本次用 `init_bisect.py` 把一个 method body 二分,定位到 line 3 = `t := str_to_obj(...)` 这一行——说明这是 100% 可复现的 quirk,不是概率性 user-error。**
> - **跨 skill 工作流影响**:AGV_Claude 这种"all-in-one 初始化 Method"(无 param,内部做一堆 `str_to_obj`)是高频模式,以前所有 "7 method 写 OK" 报告里都默认走 `param pool: object` 路径,所以未踩。本次 `AGV_init` / `AGV_reset` 零-param 才发现这个 quirk。**任何 "method 内部需要 str_to_obj + var 推断" 的场景,第一动作就是加 dummy param**。
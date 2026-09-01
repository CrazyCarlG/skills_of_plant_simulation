### 2026-09-01 by @plant-simulation-experience-curator — inner `executeSilent(<expr>)` 内的 `print` 完全不通过桥转发;必须用 `getExecuteSilentError` 捕获 error(bridge 静默失败第 4 种模式)

- **症状**:在 `executeSilent(<some expression>)` 内部用 `print "value is " + str(x)` 想看 `x` 的值——`simtalk_run` 返 `result: "success"`,`readlog` 没拿到这条 "value is ..." 字符串。但 `print` 在 GUI Console 看得到(去 Window ribbon → Console)。
- **根因**:`executeSilent` 是"静默执行"模式——它有独立的 error 缓冲区 + 独立的 print 缓冲区,**不**走 server-side handler 的 "stdout → bridge log" 转发通道。`simtalk_run` 调用 `executeSilent` 时只取 `getExecuteSilentError` 的值;`print` 的输出被 silently dropped。
- **Workaround / 结论**:

  ```simtalk
  -- 错: 想看 print 没意义
  executeSilent("var x := 1 + 2; print x")  -- print 输出 silently dropped
  -- simtalk_run 返 "success"; readlog 看不到 "3"

  -- 对: 改用变量读回
  var result : string := ""
  executeSilent("var x := 1 + 2; result := to_str(x)")  -- 把 x 写到 outer-scope Variable
  print result  -- 现在 print 在 outer scope,会被转发
  ```

  **error capture 模式**(simtalk_run 的 canonical 模式):

  ```simtalk
  executeSilent("<sim_code>")
  var err := getExecuteSilentError
  if err /= ""
      print "runtime error: " + err    -- outer scope print,会被转发
  end
  ```

  **`executeSilent` vs 普通 `simtalk_run`**:
  - **普通 `simtalk_run`**:wrapper method 不带 `executeSilent`,print 输出走桥转发 → 但 wrapper 自己 throw 任何 runtime exception 都会被捕获并以 "code execute failed" 形式返回(Quirk #7)
  - **`simtalk_run` 内 `executeSilent(<expr>)`**:print 不走桥;runtime exception 用 `getExecuteSilentError` 捕获;**只有 error string 转发,print 全 silently dropped**

- **tags**:`executeSilent`, `print-not-forwarded`, `bridge-silent-drop`, `getExecuteSilentError`, `silent-failure-mode-4`, `error-capture-canonical`
- **see also**:`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log entry 2026-08-28 (simtalk_run 无法捕获 Method 返回值)`(相关:都是 "bridge 看不到 method 内部状态");`skills/local-simtalk-execution/references/lifelines.md §Quirk #6/#7/#13`(3 种现有静默失败模式;本条是第 4 种);`02-bridge-tool/simtalkclaude-protocol.md §4.1`(scratch buffer pattern 已用 executeSilent);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md` §02-bridge-tool 第 4 条;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` §"3 bridge 行为 findings" #2

> 这条经验教会我:
> - **executeSilent 是"静默"是有意为之**——它设计目标是 "execute without raising exception, capture error string"——print 不是 error,所以被 silently dropped。**不要试图用 print 调 executeSilent**——这是 anti-pattern。
> - **bridge 静默失败模式已经累计 5 种**:Quirk #6(data 字段空)/ #7(result=success 但 log=code execute failed)/ #13(type 非法挂死) / 本条 #4 (executeSilent print 不转发) / `exec-005`(.execute() 不刷 .Program 缓存)。下次 handoff 给 skills-optimizer 时建议赋新 Quirk #14、#15。
> - **canonical capture 模式**:`executeSilent(<expr>); var err := getExecuteSilentError` 几乎是唯一可靠的"在 bridge 上下文捕获 error"路径——值得在 playbook §3.3 加一行 canonical example。
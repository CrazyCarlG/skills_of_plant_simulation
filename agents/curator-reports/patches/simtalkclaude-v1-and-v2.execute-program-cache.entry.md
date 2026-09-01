### 2026-09-01 by @plant-simulation-experience-curator — Plant Simulation `.execute()` 不刷新 `.Program` 编译缓存;write→execute 路径必须 reopen model 或走 `executeSilent(<expr>)` 模式

- **症状**:用 `m.Program := "<new body>"` 写入新 program 后,调用 `m.execute()` 仍跑**首次编译**的旧版本——即使 `.Program` 已更新、`simtalk_syntax` 验证编译通过、`.execute()` 的 wrapper 是合法的。本次 `.AGV_Claude` 7 method 案例:08-31 写入 → 09-01 readback 发现 7/7 method 全空(其实更早的版本是:即使 `.Program` 写入成功,`.execute()` 仍跑首次 compile 的代码)。
- **根因**:Plant Simulation 对每个 Method object 维护一份"已编译的 bytecode 缓存",挂在 Method object 自身。`.Program` 属性改变时缓存**不**自动失效——`.execute()` 直接调缓存,**绕过 `.Program` 的重新 parse**。`simtalk_syntax` 单独调时是 fresh compile(不读缓存),所以验证通过 ≠ `.execute()` 行为正确。
- **Workaround / 结论**:**两条独立路径**:

  ```simtalk
  -- 路径 A (推荐):不依赖 .execute() 缓存,走 executeSilent(str_to_obj(...).Program) 模式
  -- 永远 fresh compile,无缓存问题
  var m : any
  m := str_to_obj(".MyObj.MyMethod")
  executeSilent(m.Program)
  var err := getExecuteSilentError
  if err /= ""
      print "runtime error: " + err
  end
  ```

  ```text
  -- 路径 B (仅在 path A 不适用时):关闭 + 重新打开 model file
  -- 1. Plant Simulation GUI: File → Close (保存)
  -- 2. File → Open → 选 .psfm
  -- 3. 重启桥 server(.~.~.~.~.Server init → start)
  -- 4. 现在 .execute() 会用新 .Program
  ```

  **路径选择的判定**:
  - Agent 频繁跑 + 改 method body → 路径 A(`executeSilent` 模式)→ 无需 GUI 操作
  - Model 不可频繁重启(用户工作流)→ 路径 A
  - 一次性脚本测试 + 不想写 executeSilent wrapper → 路径 B(关+开 model)
  - **绝对禁忌**:`m.Program := new; m.execute()` —— **永远** 不会跑新 body

  **`.execute()` 的合法使用场景**:
  - Method body 第一次写入时(syntax check 模式)
  - Method body 从未改过(缓存与 .Program 一致)
  - 用户已 close+reopen model 后(缓存被清)
  - Method 是 GUI Methods 编辑器里手写的(缓存与 GUI .Program 一致)

- **tags**:`simtalk`, `method-execute`, `program-cache`, `compile-cache`, `invalidate-cache`, `executeSilent-alternative`, `model-reopen`, `silent-failure-mode-5`
- **see also**:`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log entry 2026-08-28 (Bridge + SimTalk 死循环)`(相关但不同——这是死循环,本条是 stale cache);`skills/local-simtalk-execution/references/lifelines.md §Quirk #6/#7/#13`(现有 3 种静默失败模式;本条是第 5 种);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md` §03-workflow-playbook;`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings 第 3 条;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-write-and-cache.md` Finding #3

> 这条经验教会我:
> - **缓存与属性的非对称失效** 是 Plant Simulation 长期未修的隐式合约。任何 "你写的 .Program 立即生效" 的直觉都是错的——**必须考虑 compile 缓存的生命周期**。这是 08-31 → 09-01 整个 .AGV_Claude 修复链"7 method 全 verify OK 但全空 / 全跑老代码"的**根因**。
> - **`simtalk_syntax` 通过 ≠ `.execute()` 行为正确**——前者 fresh compile,后者用缓存。两个判据不能互相替代。本次 agent 反复被 "syntax check PASS" 误导,以为 method 可用,**实际上 .execute() 跑的是首次 compile 的 body**(可能是空 / 可能是上次版本)。
> - **跨 skill 连锁影响**:任何上层 skill(`write_simtalk.py` / `add_note.py` / `class_management`)如果依赖 "write 后立刻 `.execute()` 验证"——它们的 verify 步骤**全是 silent failure**。需要从根上改 skill 行为(走 `executeSilent` 模式),否则 agent 看到的 "verify OK" 都是幻觉。**本次 quarantine-001 + 本条 entry 是同一个根因的不同层面**——一个修 workflow、一个修 bridge 认识。
### 2026-09-01 by @plant-simulation-experience-curator — `getAttrNo(attrName)` 在本版本语义"全部返回 0",不能用它探测属性存在性(⚠️ tentative:可能是 wrong signature)

- **症状**:`o.getAttrNo("setSize")` / `o.getAttrNo("setRowNum")` / `o.getAttrNo("DummyMethod")` —— 不论存在与否,**全部 0**。
- **根因**(tentative,待复测):
  - 可能 1:Plant Simulation v2606.0002 把 `getAttrNo` 的语义从 "返回 attribute index" 改为 "返回 0 if not found, 0 if found"(永远是 default)—— buggy implementation
  - 可能 2:**签名错了**——可能是 `getAttrNo(o, name)`(把 object 作为第一参)而非 `o.getAttrNo(name)`(method call)。如果用错签名,可能 default 到返回 0 而非 throw——本次 session 自标"可能是用错了签名"
- **Workaround / 结论**:**不要用 `getAttrNo` 探测属性存在性**。直接读 attribute:
  ```simtalk
  var o : any
  o := str_to_obj(".Foo")

  -- 不要用:
  -- if o.getAttrNo("myAttr") = 0  -- 永远 = 0,无意义
  --   ...

  -- 改用:
  if o.getAttribute("myAttr") /= void
      print "exists"
  else
      print "does not exist"
  end

  -- 或探测 program 是否非空:
  if strLen(o.Program) > 0
      print "method has body"
    end
  ```

  **判定**:
  - 探测"attribute 是否存在" → `getAttribute(name) /= void`(类型安全,返 any)
  - 探测"method body 是否非空" → `strLen(o.Program) > 0`(直接读 .Program 长度)
  - 探测"attribute 当前值" → 直接 `o.<attrName>`,让 SimTalk 自己 throw(明确信号)

- **tags**:`getAttrNo`, `attribute-existence`, `tentative`, `getAttribute-vs-getAttrNo`, `v2606.0002`, `wrong-signature-suspected`
- **see also**:`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md` §02-bridge-tool 第 4 条;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-wrap-probe.md` §"3 bridge 行为 findings" #3;`derived-methods-quirks.md §经验 Log entry 2026-08-31`(method-typed-UDA 用 `getAttribute` 是正解,本 entry 是对 `getAttrNo` 反例的补强)

> 这条经验教会我:
> - **`getAttribute` ≠ `getAttrNo`**:前者返 attribute value(类型=any),后者返 attribute index(integer)。语义完全不同。**探测存在性用 `getAttribute(name) /= void`**——这是 typed 模式,任何 Plant Simulation 版本都一致。
> - **本次 session 自身 sanity-check 不够**:session summary 自标 "可能是用错了签名",说明当时没有花 5 分钟 trace 正确签名——下次类似"全部返 0"的发现,**第一步就是查 KB docs 确认签名**再下定论。
> - **保留 tentative 标签**:本 entry 标 ⚠️ tentative,等下次 session 用正确签名复测一次。如果复测后 `getAttrNo(o, name)` 正确返回 index,则本 entry 改为 supersede(`o.getAttrNo(name)` 是 wrong syntax)。如果复测仍返 0,则本 entry 升 P0 永久保留。
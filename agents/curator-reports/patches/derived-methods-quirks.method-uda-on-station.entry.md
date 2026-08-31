### 2026-08-31 by @plant-simulation-experience-curator — 给非 Frame/Folder 对象（Station / Drain / Source / Conveyor / ...）添加自定义 method：canonical 模式是 `createAttr(name, "Method")` + `getAttribute(name) → any`

- **症状**：尝试给 Station（或任何 `InternalClassType ≠ "Frame"` 且 `≠ "Folder"` 的对象，例如 `.UR10.UR10` 是 Station）添加一段自定义 SimTalk 时，三条直觉路径全部失败：
  1. `local-simtalk-create-method-object --frame .UR10.UR10` → `frame_invalid: path .UR10.UR10 is not a Frame (got 'Station')`
  2. `&Method.duplicate(<station>, <name>)` / `<parent_class>.duplicate(<station>, <name>)` → `duplicate_returned_void` 或 `Argument 1 is neither a Frame nor a Folder`
  3. `o.setAttrType(idx, "Method")` → `setAttrType` **不支持** `"Method"` 类型（仅支持 `boolean / integer / real / string / object / table / list / stack / queue / time / money / length / weight / speed / acceleration / date / dateTime / randtime`）。`createAttr(name, "Method")` 成功之后，`o.<methodName>` 点访问返回 `void`（不能用来读/写 `.Program`），让 agent 误以为 "createAttr 失败"。

- **根因**：Method-typed UDA **不是** child Method object —— Plant Simulation 把它当作一种特殊的"属性值"，与 Frame 下的子 Method 对象走完全不同的存储 / 访问路径。`getAttribute` 文档明确说 *"For user-defined attributes of `method` data type, `getAttribute` returns the method itself — not the result of executing it"*；调用 `.execute` 才会真正执行。要拿它的 `Program` 来读写，必须经过 `getAttribute` 而不是点访问。

- **Workaround / 结论**：

  ```simtalk
  -- canonical pattern: createAttr + getAttribute + any-typed var
  var o : object := str_to_obj(".UR10.UR10")  -- any non-Frame object works

  -- 1) create (idempotent: 检查 getAttrNo 是否已存在)
  if o.getAttrNo("myMethod") = 0
      var ok : boolean := o.createAttr("myMethod", "Method")
      -- ok = true on success; false if name is reserved or invalid identifier
  end

  -- 2) access the method (return type 是 `any`，不是 `object`！)
  var m : any
  m := o.getAttribute("myMethod")

  -- 3) write Program (用 chr(10) + chr(34) 安全拼接 multi-line + 嵌入引号)
  m.Program := "-- myMethod -- example body" + chr(10)
             + "self._3D.Poses.moveTo(" + chr(34) + "home" + chr(34) + ")"

  -- alternative 写法（更简洁，不需要 any 变量）
  o.setAttribute("myMethod.Program", "-- myMethod" + chr(10) + "print 1")

  -- 4) read back
  var m2 : any
  m2 := o.getAttribute("myMethod")
  print m2.Program                    -- reads back the source verbatim
  print m2.HasSyntaxError             -- true/false
  ```

  调用方式（client 端）保持不变：`o.myMethod()` 或 `o.myMethod.execute(...)`。

  **关键铁律**：
  - `var m : object := o.getAttribute("myMethod")` → **编译错** *"Left and right sides of the assignment are incompatible"*。必须用 `var m : any`。
  - `var m : object := o.myMethod` → 编译过但运行时 `m = void`。**不要** 用点访问拿 Method 对象。
  - SimTalk 2.0 **不允许** `var m` 不带类型；不允许 `var x;`。
  - `o.<methodName>`（无 `()`）会**执行**方法（空 method 也返回 `void`）；要拿对象引用，必须走 `getAttribute`。

- **tags**：`simtalk`, `createAttr`, `method-typed-UDA`, `getAttribute`, `any-type`, `station`, `non-frame-object`, `setAttribute-attr-path`, `chr(10)-chr(34)-safe-encoding`
- **see also**：`01-plantsimulation-knowledge/.../objects/common-methods/common-methods.md §7 createAttr + §6 getAttribute`（独立来源 #1）；`skills/local-simtalk-create-method-object/SKILL.md` Step "Choosing a target Frame"`（明确拒绝 Station，与本 entry 形成 "skill 限制 vs. 实际可行方案" 的对照）；`02-simulation-file-experience/03-workflow-playbook/skill-call-playbook.md` §经验 Log [pending patch — `method-uda-on-station.entry.md`]（跨 skill 工作流决策表）

> 这条经验教会我：
> - **Method-typed UDA ≠ child Method object**。两者底层存储模型不同：UDA 是 "属性值 = Method 对象"，child Method 是 "Frame 子节点"。读写代码要走完全不同的路径 (`getAttribute` vs `<parent>.<name>`)，不能用同一个 mental model。
> - `getAttribute` 返回 `any` 不是 bug，是设计 —— 因为它要兼容所有 UDA 数据类型（integer / string / list / table / method ...），method 只是其中之一。声明 receiving var 时一定要 `var x: any`，不要想当然 `var x: object`。
> - `createAttr("Method")` vs `setAttrType("Method")` 的不对称容易让人栽跟头：**只有 `createAttr` 接受 "Method"**，`setAttrType` 完全不支持。两条 API 的 type-string 白名单不一样，是 Plant Simulation 历史包袱。
> - 跨 skill 工作流的盲区：`local-simtalk-create-method-object` 只覆盖 Frame-挂-Method 的场景；Station-挂-Method-typed-UDA 这个**同样合法且高频**的 case 没有 skill 包装，只能直接走 `simtalk_run` + `createAttr`。下次任何 agent 接到"给 X 加个 method"的任务，第一步必须先判断 `X.InternalClassType ∈ {"Frame","Folder"}` 还是其他 —— 走哪条路天差地别。

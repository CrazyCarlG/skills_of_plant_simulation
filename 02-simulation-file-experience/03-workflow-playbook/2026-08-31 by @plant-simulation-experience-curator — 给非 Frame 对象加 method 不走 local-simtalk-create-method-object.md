### 2026-08-31 by @plant-simulation-experience-curator — "给非 Frame 对象加 method" 不走 `local-simtalk-create-method-object`；直接 `simtalk_run` + `createAttr` + `getAttribute`

- **症状**：接到 "给 `.UR10.UR10`（一个 Station）添加 4 个 method" 的任务时，按 `local-simtalk-create-method-object` 的 skill description 走 → `validate_frame()` 报错 `path .UR10.UR10 is not a Frame (got 'Station')` → expert 在 Station 上跑 child-Method-object 的 `&Method.duplicate()` 也失败（`Argument 1 is neither a Frame nor a Folder`）。三连失败才意识到：Plant Simulation 的 Method 有两种挂载模型，skill 只覆盖了一种。
- **根因**：`local-simtalk-create-method-object` 的 scope 是 "Frame/Folder 下挂 child Method object"（通过 `&Method.duplicate(frame, name)`）。Station / Drain / Source / Conveyor 等非 Frame 对象的 method 走另一条路：**method-typed user-defined attribute**（通过 `createAttr(name, "Method")` + `getAttribute(name) → any` 访问）。Skill description 没有显式说明这个限制，导致按 description 走的 agent 一定会撞墙。
- **Workaround / 结论**：

  | 任务 | 走的路径 | 用哪个 skill |
  |---|---|---|
  | 给 **Frame / Folder / Models.Model** 加 method | `&Method.duplicate(<frame>, <name>)` 然后 `write_simtalk` | `local-simtalk-create-method-object` + `local-simtalk-write-simtalk` |
  | 给 **Station / Drain / Source / Conveyor / 自定义类实例** 加 method | `o.createAttr(name, "Method")` 然后 `getAttribute(name) → any` + `m.Program := <src>` | **直接 `simtalk_run`**，跳过 `local-simtalk-create-method-object` |

  决策流程：接到 "给 X 加 method" 任务时，第一步检查 `X.InternalClassType`：
  - `Frame` / `Folder` → 走标准 skill 链路
  - 其他（包括 `Station`, `Drain`, `Source`, `Conveyor`, `Transporter`, `Store`, `ParallelStation`, `AssemblyStation`, 自定义类实例等）→ 走 `simtalk_run` + `createAttr` + `getAttribute`，**不要**尝试调 `local-simtalk-create-method-object`

- **tags**：`skill-selection`, `createAttr`, `method-typed-UDA`, `station`, `cross-skill-workflow`, `frame-vs-non-frame`
- **see also**：`02-simulation-file-experience/01-domain-concepts/derived-methods-quirks.md §经验 Log`（`method-uda-on-station` — canonical API pattern + chr(10)/chr(34) 编码）；`skills/local-simtalk-create-method-object/SKILL.md` §"Do NOT use for"（**当前未列出 "non-Frame 对象" 这一条**——这是 skill 描述的 gap，建议 `skills-optimizer` 在下次 handoff 时评估是否补上）；`agents/curator-reports/2026-08-31-curator-report.md` §P2 quarantine-001

> 这条经验教会我：
> - **Skill description 的 "When to use" / "Do NOT use for" 列表必须枚举**。`local-simtalk-create-method-object` 的 description 只说 "Insert a new Method instance into a Plant Simulation Frame"，但 `Frame` 这个词没强调"必须是 Frame"，agent 会按字面理解成"任何对象都可以挂 Method instance" → 撞墙才知道。下次写 skill description 一定要把"什么 *不* 行"显式列出来。
> - 跨 skill 决策表的隐藏价值：单看任一 skill 都能 work（`createAttr` 在 `local-simtalk-execution` 里能调，`write_simtalk` 的任何 path 上都能写），但**组合**起来时 "哪个 skill 处理哪段" 不清晰。playbook 应该补一节 "Frame vs non-Frame object method-attachment" 的决策表。
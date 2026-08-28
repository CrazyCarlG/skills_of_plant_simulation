---
last_updated: 2026-08-27
contributors: [@z004bjuu, @plant-simulation-expert]
scope: P4_CTU 模型 Origin / OriginRoot / Class 三元组类继承专项（与 modeling-experience 互补）
---

# P4_CTU 类继承关系 — 2026-08-27

> **定位**：本文件是 `p4-ctu-modeling-experience.md` 的**类继承专项**——专攻
> `Origin` / `OriginRoot` / `Class` 三元组，不重复模型架构 / 控制流 / 命名约定等
> 已有内容。读完两篇应能完整回答"这个模型里每个类从哪里来"。
>
> **数据来源**：全部基于 `simtalk_run` + `readlog` 实测读回的 `str_to_obj(path).Origin` /
> `OriginRoot` / `Class` / `InternalClassType` / `Name` 五元组，无任何"应该 / 大概"臆测。
>
> **Artifacts**：
> - `skills/local-simtalk-get-class-inheritance/data/p4ctu_inherit_raw.tsv` — 48 行原始 TSV
> - `skills/local-simtalk-get-class-inheritance/data/p4ctu_inherit_raw.json` — 同上 JSON 版
> - `skills/local-simtalk-get-class-inheritance/data/inheritance_map.json` — render 出的 parent→children 树

## 一、捕获概览

48 个候选路径中：

| 类别 | 数量 | 说明 |
|---|---|---|
| **实测总候选路径** | 48 | `data/p4ctu_inherit_raw.tsv` 全部行 |
| **成功解析**（name+type 非空） | 42 | 真实存在的类 / 文件夹 |
| **path 解析为 void**（name 空） | 6 | `.MUs.Pallet` + `.P4_CTU.BasicObjects.InformationFlow.{Attribute,EventController,TableFile}` + `.P4_CTU.BasicObjects.MUs.{Connector,Pallet}` |
| **Origin = VOID**（"根类"） | 41 | 包含 Plant Simulation 内置类 + p4_ctu 内自带的根类定义 |
| **Origin ≠ VOID**（"派生类"） | **7** | 用户从本地副本（`.P4_CTU.BasicObjects.*`）继承的业务类 |

> **重要术语澄清**（与 SKILL.md 略有出入）：
> SKILL.md 原文把 `Origin == VOID` 等同于"Plant Simulation 内置类"。但当模型以 **class library package**
> 形式被导入时（`.P4_CTU` 本身是一个 `Folder`，挂在 class library 根下），里面的所有元素
> 都视为新 class library 的"根条目"，`Origin` 自然 = VOID——这是 model-as-library 的天然结果，
> **与"是不是内置"无关**。判断"业务上是不是从某个内置类派生"的依据是 `.OriginRoot` 在
> 不在全局类库里，以及代码里实际继承了什么 attribute / method。
>
> 实测 `.P4_CTU.BasicObjects.MUs.Transporter`（p4_ctu 自带 Transporter 副本）的 `Origin` = VOID，
> 但**类型就是 `Transporter`**，与全局 `.MUs.Transporter` 完全等价——它是从内置类复制过来的根条目。

## 二、3 条继承链 — 全部 Origin 都指向本地副本

7 个派生类收敛成 3 条以 **本地副本（`.P4_CTU.BasicObjects.*`）** 为根的链：

```
.P4_CTU.BasicObjects.MUs.Transporter          (Transporter, Origin=VOID)
├─ .P4_CTU.AdvancedObject.Hardware.AGV        (Transporter)   ← 业务: 地面 AGV
└─ .P4_CTU.AdvancedObject.Hardware.CTU.CTU    (Transporter)   ← 业务: 堆垛机

.P4_CTU.BasicObjects.MUs.Container            (Container, Origin=VOID)
├─ .P4_CTU.AdvancedObject.Hardware.CTU.Lifttable       (Container)   ← 业务: CTU 提升台
└─ .P4_CTU.AdvancedObject.Hardware.CTU.Carrier         (Container)   ← 业务: 通用 Carrier
   └─ .P4_CTU.AdvancedObject.Hardware.CTU.Carrier_Box  (Container)   ← 业务: 装 Box 的 Carrier（唯一 2 层链）

.P4_CTU.BasicObjects.MaterialFlow.Store       (Store, Origin=VOID)
└─ .P4_CTU.AdvancedObject.Hardware.Store      (Store)         ← 业务: 通用 Store

.P4_CTU.BasicObjects.Resources.AGVPool         (AGVPool, Origin=VOID)
└─ .P4_CTU.AdvancedObject.Hardware.AGVPool    (AGVPool)       ← 业务: AGV 池
```

### 2.1 完整三元组表

| 类路径 | Type | Origin | OriginRoot | Class | 业务角色 |
|---|---|---|---|---|---|
| `.P4_CTU.AdvancedObject.Hardware.AGV` | Transporter | `.P4_CTU.BasicObjects.MUs.Transporter` | `.P4_CTU.BasicObjects.MUs.Transporter` | VOID | 地面 AGV 实例的类定义 |
| `.P4_CTU.AdvancedObject.Hardware.AGVPool` | AGVPool | `.P4_CTU.BasicObjects.Resources.AGVPool` | `.P4_CTU.BasicObjects.Resources.AGVPool` | VOID | AGV 池实例的类定义 |
| `.P4_CTU.AdvancedObject.Hardware.CTU.CTU` | Transporter | `.P4_CTU.BasicObjects.MUs.Transporter` | `.P4_CTU.BasicObjects.MUs.Transporter` | VOID | 堆垛机实例的类定义 |
| `.P4_CTU.AdvancedObject.Hardware.CTU.Carrier` | Container | `.P4_CTU.BasicObjects.MUs.Container` | `.P4_CTU.BasicObjects.MUs.Container` | VOID | 通用 carrier |
| `.P4_CTU.AdvancedObject.Hardware.CTU.Carrier_Box` | Container | `.P4_CTU.AdvancedObject.Hardware.CTU.Carrier` | `.P4_CTU.BasicObjects.MUs.Container` | VOID | 装 box 的 carrier（2 层链） |
| `.P4_CTU.AdvancedObject.Hardware.CTU.Lifttable` | Container | `.P4_CTU.BasicObjects.MUs.Container` | `.P4_CTU.BasicObjects.MUs.Container` | VOID | CTU 提升台 |
| `.P4_CTU.AdvancedObject.Hardware.Store` | Store | `.P4_CTU.BasicObjects.MaterialFlow.Store` | `.P4_CTU.BasicObjects.MaterialFlow.Store` | VOID | 通用 Store |

### 2.2 关键观察

1. **AGV 和 CTU 是兄弟类**：两个都用 `Transporter` 模型，但它们的"业务动作"通过 RCS 的 executer 分别调度。
   —— *作者有意让"AGV"和"堆垛机 CTU"在物理引擎里走同一条 Transporter 路径，差异只在 attribute 和 executer 策略。*

2. **唯一的 2 层链：Carrier_Box → Carrier → Container**：模型里有专门的"装 Box 的 Carrier"变体，
   通过继承 Carrier 而不是 Container 来共享通用逻辑。这是 Plant Simulation 里典型的"业务变体"模式。

3. **`Class` 字段全部 = VOID**：7 个派生类无一例外。原因：它们本身就是 Class Library 顶层条目，
   Plant Simulation 的"Class 字段"指向 class library 上方的根（内置类），而这些**已经是**根。
   详见 §四 Quirk。

## 三、"根类"中真正承载类库副本的部分

41 个 `Origin = VOID` 的条目里，**真正是 Plant Simulation 内置类的只有 9 个**（`.MUs.*` / `.MaterialFlow.*` / `.Resources.*`），其余 32 个是 `.P4_CTU` 类库包自身的根类定义。

### 3.1 内置类（9 个，作为对照锚点）

```
.MUs                              [Folder]    ← 内置类库顶级文件夹
.MUs.Container                    [Container] ← 内置 Container 类
.MUs.Pallet                       [VOID]      ← 注意：内置库本身没 Pallet
.MUs.Transporter                  [Transporter]
.MaterialFlow                      [Folder]
.MaterialFlow.Station              [Station]
.MaterialFlow.Store                [Store]
.Resources                         [Folder]
.Resources.AGVPool                 [AGVPool]
```

> **注意**：`.MUs.Pallet` 是 VOID —— Plant Simulation 内置库**当前没有 Pallet 类**
> （Pallet 在某些 OEM 扩展包才提供）。这与 `.P4_CTU.BasicObjects.MUs.Pallet` 也是 VOID 一致，
> 所以不要尝试引用 `.P4_CTU.*.Pallet`。

### 3.2 .P4_CTU 自带根类（模型作者定义的"业务类基底"）

| 路径 | Type | 业务角色 |
|---|---|---|
| `.P4_CTU.BasicObjects.MaterialFlow.Station` | Station | 内置 Station 的本地副本 |
| `.P4_CTU.BasicObjects.MaterialFlow.Store` | Store | 内置 Store 的本地副本 |
| `.P4_CTU.BasicObjects.MUs.Transporter` | Transporter | 内置 Transporter 的本地副本 |
| `.P4_CTU.BasicObjects.MUs.Container` | Container | 内置 Container 的本地副本 |
| `.P4_CTU.BasicObjects.Resources.AGVPool` | AGVPool | 内置 AGVPool 的本地副本 |
| `.P4_CTU.BasicObjects.InformationFlow.Generator` | Generator | 内置 Generator 的本地副本 |
| `.P4_CTU.AdvancedObject.Hardware.Rack` | Frame | Rack 的 Frame 类定义 |
| `.P4_CTU.AdvancedObject.Hardware.CTU.test` | Frame | CTU 单元测试 Frame 类 |
| `.P4_CTU.AdvancedObject.Software.RCS` | Frame | Rack Control System 的 Frame 类定义 |
| `.P4_CTU.AdvancedObject.Software.MapGenerator.Home` | Frame | Home 占位 Frame 类 |
| `.P4_CTU.AdvancedObject.Software.MapGenerator.ChargingPlace` | Frame | 充电桩 Frame 类 |
| `.P4_CTU.AdvancedObject.Software.MapGenerator.StockInLoader` | Frame | 入库接驳 Frame 类 |
| `.P4_CTU.AdvancedObject.Software.MapGenerator.StockOutLoader` | Frame | 出库接驳 Frame 类 |
| `.P4_CTU.ctux1_agvx1` | Frame | 1×1 仿真模板（1 CTU + 1 AGV） |
| `.P4_CTU.ctux1_agvx2` | Frame | 2×2 仿真模板（2 CTU + 2 AGV） |

### 3.3 Frame 类的"虚根"哲学

注意 `.P4_CTU.AdvancedObject.Hardware.Rack` / `Software.RCS` / `Software.MapGenerator.Home` 等
业务 Frame 类的 `Origin` **全是 VOID**——它们不是从 `.Frame`（内置 Frame 基类）继承的。

实际探查 `.Frame`（内置 Frame 基类）也是 VOID —— 说明 Plant Simulation 的"内置类根"在
`.Frame` 这个 Folder 名上**不显式返回 Object**，而是当作 namespace。

**结论**：

- 在 Plant Simulation 里，**Frame 类无需显式继承 `.Frame`**。新建一个 Frame 元素（即使作为类定义），
  它本身就是 root Frame。
- 一个 Frame 类有没有"父类"，只能通过**自定义 attribute / method 是否被继承**来判断，
  而**不是**通过 `Origin` 是否指向 `.Frame`。
- 同理，Transporter / Container / Store / Station / AGVPool 这些 MUs / MaterialFlow / Resources
  类，**新建时 Origin 就是 VOID**（它们从对应的内置类复制过来，但被当作"新 class library 的根条目"）。

## 四、Quirk：所有派生类 `Class` 字段都 = VOID

7 个派生类的 `Class` 字段全为 VOID。这跟 SKILL.md "Class 指向 Class Library 中派生该实例的类"
的说法**不完全一致**——我先跑了一个对照实验来理解这个字段：

| 实测路径 | Class 字段 |
|---|---|
| `.MaterialFlow.Station`（内置） | VOID |
| `.P4_CTU.BasicObjects.MaterialFlow.Station`（本地副本） | VOID |
| `.P4_CTU.AdvancedObject.Hardware.Store`（从本地副本派生） | VOID |
| `.P4_CTU.AdvancedObject.Hardware.AGV`（从本地副本派生） | VOID |

**观察**：只要这条 path **已经是 Class Library 顶层条目**，`Class` 字段就是 VOID。
所以"Class"字段的语义其实是——"如果这个实例是从**实例**派生的（非类库条目），那 Class 指向它的源类"。
对于**类库条目本身**（无论内置还是用户定义），Class 永远是 VOID。

> **可借鉴度 / Quirk 价值**：⭐⭐⭐⭐。
> **不要**用 `.Class` 来判断派生关系——它对类库条目一律返回 VOID，没有参考价值。
> 判断派生链应该用 `.Origin`（直接父）+ `.OriginRoot`（链根）这一对属性。

## 五、与现有经验文件的差异（修订点）

| 现有文档 §2 的描述 | 实测探查结果 | 修订 |
|---|---|---|
| `.P4_CTU.BasicObjects.PartA` / `PartB` / `Box` / `MyFrame` "用户自定义 MU 类" | 这 4 个 path 实测均返回 VOID（`/tmp/p4ctu_stale_proof.tsv` 第 1-4 行） | 删除或注明"已删除 / 从未真正存在" |
| `.P4_CTU.AdvancedObject.Software.MapGenerator.Transparency` "Frame 类变体" | 实测 VOID（`/tmp/p4ctu_stale_proof.tsv` 第 5 行） | 同上 |
| `.P4_CTU.BasicObjects.InformationFlow.Generator` 隐含未提及 | 存在（Generator 类型） | 补一句"InformationFlow 也带了一份 Generator 副本" |
| `.P4_CTU.BasicObjects.MUs.Container` 未提 | 存在（Container 类型，是 Lifttable / Carrier 的 Origin） | 这是 §2.2 论述的关键支撑，必须显式列出 |

> **stale_path 实测证据**（`probe_inheritance.py` 输出 `name="" type="" origin=VOID originroot=VOID cls=VOID`，即 `str_to_obj` 返回 void）：
>
> ```
> .P4_CTU.BasicObjects.PartA                     <VOID>
> .P4_CTU.BasicObjects.PartB                     <VOID>
> .P4_CTU.BasicObjects.Box                       <VOID>
> .P4_CTU.BasicObjects.MyFrame                   <VOID>
> .P4_CTU.AdvancedObject.Software.MapGenerator.Transparency  <VOID>
> ```
>
> 完整记录在 `/tmp/p4ctu_stale_proof.tsv`（5 行），与主 TSV 分开保存以避免污染 48 行的"全成功探查"基线。

> **可能解释**：原文档基于早期 dump；模型后来被作者**删掉了一部分占位类**（PartA/PartB/Box/MyFrame/
> Transparency），或者这些 class 从一开始就是规划但未真正创建。
>
> **复用规则**：下游 agent 写"我要给 Box 类加方法"之前，**必须先 probe 确认 Box 还在**——
> 不要假设现存的文档描述能跟上模型当前状态。

> **关于"现有文档 §2.2 是否矛盾"**：现有 `p4-ctu-modeling-experience.md` §2.2 原文
> "实测确认：`.P4_CTU.AdvancedObject.Hardware.AGV` 的 `Origin` 是 `.P4_CTU.BasicObjects.MUs.Transporter`
> 而不是 `.MUs.Transporter`"——**与新文档一致**，没有矛盾。两份文档都正确识别了"指向本地副本"模式。

## 六、复用这套继承设计的步骤

要在新模型里照搬 p4_ctu 的"自包含类库副本 + 业务派生"模式：

1. **建类库包**：`<模型名>`（Folder，挂在 class library 根）。
2. **BasicObjects 副本**：从内置类库 duplicate 出要用的类到 `.MyModel.BasicObjects.{MUs, MaterialFlow, Resources, InformationFlow}`。
   - 建议至少带：Transporter, Container, Station, Store, AGVPool, Generator。
   - **不要带 Pallet**（除非有 OEM 扩展）—— 内置类库本身就没 Pallet，会全部返回 VOID。
3. **业务派生**：从本地副本派生业务类，Origin 自然指向本地副本（与全局类库解耦）。
   - 例：`.MyModel.Hardware.MyAGV ← .MyModel.BasicObjects.MUs.Transporter`
4. **Frame 类独立成根**：业务 Frame 类（Rack / RCS / Home / Loader / 模板 Frame）全部 Origin=VOID，
   不需要也无法"继承 .Frame"。
5. **验证**：用 `local-simtalk-get-class-inheritance` probe 整棵继承树，
   确认所有 `Origin` 都指向 `.MyModel.BasicObjects.*` 而不是全局类库。

> **可借鉴度**：⭐⭐⭐⭐⭐。
> 这是**Plant Simulation 模型可移植 / 跨机器部署**的关键模式——
> 任何下游要"把模型发给别人跑"的场景都必须用这套结构。

## 七、还能进一步挖的类继承问题

| 主题 | 价值 | 行动 |
|---|---|---|
| **AGV 和 CTU 内部 `m_executeTransportationOrder` 是方法继承还是各自实现？** | 确认业务类是否真的共享逻辑 | 用 `local-simtalk-read-library` 对比两个 method 的 program 文本 |
| **`BasicObjects.MUs.Transporter` 与全局 `.MUs.Transporter` 在 attribute / method 上的差异** | 看本地副本到底覆盖了哪些内置行为 | probe `obj.numAttributes` / 对比 `getAttrNames` |
| **`.P4_CTU.AdvancedObject.Hardware.CTU.test`（Frame 类型）作为单元测试入口**：包含哪些 test method | 验证作者是否真提供了单元测试 | 用 `local-simtalk-read-library` dump .P4_CTU.AdvancedObject.Hardware.CTU.test |
| **MapGenerator.* Frame 类的 `Origin = VOID` 但彼此同名 / 行为相似**：是否有人为它们做一个共同父类 | 重构机会 | 看是否能新建 `.MyModel.Hardware.Loader` 之类的中间基类 |
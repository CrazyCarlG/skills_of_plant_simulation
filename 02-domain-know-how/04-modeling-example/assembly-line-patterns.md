---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: 自定义装配生产线建模模式(WorkerChart / PalletOptimization / BottleneckAnalyzer / EnergyAnalyzer)
---

# 自定义装配生产线建模模式

本文档基于 assembly-line 模型(Models.Assembly1 + Models.Assembly2)提炼出 **自定义生产线的建模模式**。

## 一、模型架构

```
Basis
├── MaterialFlow / Resources / InformationFlow / UserInterface / MUs / Tools
├── UserObjects                              ← 模块化对象库 pattern
│   ├── Classes                              ← 可复用类定义
│   │   ├── Toolbar Library
│   │   ├── Track CrossTransfer
│   │   ├── Station MS / Station AS
│   │   ├── Worker ×3
│   │   └── PickAndPlace Robot
│   └── Modules                              ← 实例模板(Frames)
│       ├── PreProduction
│       └── Assembly_initialState
├── Models
│   ├── Assembly1                            ← 精简基线
│   │   ├── PreProduction
│   │   ├── WorkerChart
│   │   ├── PalletOptimization
│   │   └── Connectors/Conveyors/Buffer/Source/Drain/Sankey/Events
│   └── Assembly2                            ← 仪器化生产
│       └── Assembly1 + BottleneckAnalyzer + EnergyAnalyzer
│         + BufferOptimization + EnergySavingMeasures + DisplayEnergy
└── SimtalkClaude (v2 TCP bridge)
```

## 二、UserObjects 二级拆分模式

`UserObjects` 分**两类**:

| Folder | 装什么 | 修改频率 |
|---|---|---|
| `UserObjects/Classes/*` | 可复用类定义(Toolbar/Stations/Workers/Robot) | 很少 |
| `UserObjects/Modules/PreProduction` | Frame 模板(Source/Station/Conveyor/Connector/Robot) | 偶尔 |
| `UserObjects/Modules/Assembly_initialState` | "Reset-to-here" 模板,BufferOptimization.restoreParam 使用 | 很少 |

> **值得抄**:`Classes` vs `Modules` 分离让"哪些是定义(不要 instance)vs 哪些是模板(instance + customize)"一目了然。

## 三、WorkerChart — Frame-with-UI 教科书

### 3.1 5 个方法的职责

| Method | 角色 |
|---|---|
| `init` | `GetWorkersFromPool` + `switchRadioButton` + `Refresh` |
| `DragAndDrop` | 接受 `NwWorkerPool`;填表;打开 dialog |
| `Open` | **SimTalk 2.0 语法**(`is`/`do`/`inspect`/`when`);恢复 persisted dialog state |
| `CallBack` | UI 事件路由;`switch item / case`;在 `myStatisticTable` 上合并 2 个 source DataTable |
| `Refresh` | 通过 `Transpose()` 翻转行/列;`MakeString(...)` 每行 + `(s)/numWorkers` 除法 |

### 3.2 Frame-with-UI 标准结构

```
.WorkerChart                              ← Frame 对象
├── Dialog (custom UI)                   ← 拖拽目标、事件源
├── myWorkingTimeStatisticTable           ← DataTable(source 1)
├── myOverallTimeStatisticTable           ← DataTable(source 2)
├── myStatisticTable                      ← DataTable(combined view)
├── myBufferTable                         ← DataTable(transposed for input)
├── myRadioButton                         ← Variable(Working/Overall toggle)
└── Chart (built-in Plant Simulation chart object)
```

生命周期:`init → drag → open → callback → refresh`

### 3.3 关键 idiom:`NwWorkerPool` 类型守卫

```simtalk
-- DragAndDrop
if droppedObject.internalClassName = "NwWorkerPool"
  -- 接受
end
```

## 四、PalletOptimization — 自定义 ExperimentManager

`PalletOptimization` 是比 `.Tools.ExperimentManager` 更丰富的实现——增加了规则引擎 for 实验期适配。

### 4.1 4-state 状态机(`Start`)

```
stopped → wait4stop → running → ready → (循环)
```

状态机存在的原因:Plant Simulation 的内置 `EventController.start` 是 fire-and-forget;这个状态机添加**同步就绪语义**让 agent 能 probe "experiment N done yet?"。

### 4.2 规则引擎(`evalRules` + `performRule`)

规则存在 DataTable 中,列:`priority:int, initRule:boolean, conditionMethod:string, conditionExp:string, actionMethod:string, actionExp:string, validExp:string`。

`evalRules`:

1. 按 priority 降序排序
2. 对每条规则,检查 `initRule` —— 如果是 true,只在 experiment 1 触发
3. 否则,调用 `Rules.validExp(s)` for current experiment
4. 如果 valid,调用 `performRule(rule)`

`performRule(rule)`:

- **复合 condition** = `Rules.TestConditionExp(rule, conditionExp)` AND a method call(`rule.conditionMethod`)
- **复合 action** = `Rules.DoActionExp(rule, actionExp)` AND optionally a method call(`rule.actionMethod`)

> **值得抄**:priority-sorted rule table + 复合 condition/action。让 end-users 在不重新编译的情况下添加实验逻辑。

### 4.3 类型化 dispatch (`storeParam`/`restoreParam`)

```simtalk
-- storeParam
writeValue(AttrStr, AttrVal) per input column

-- restoreParam (type-aware)
"length"  → str_to_length
"time"    → str_to_time
"speed"   → str_to_speed
"acceleration" → str_to_acceleration
"weight"  → str_to_weight

-- WorkerPool inheritance special-case
setCreationTable(void)
inheritAttribute
```

> **Lesson**:Plant Simulation 的 `writeValue` 是**非类型化**的,restore 时务必用 type-specific `str_to_*` 转换器。

## 五、BottleneckAnalyzer — 8-state 利用率分解

8 个 stat 属性 → 8 个利用率因子 per 对象 → 2D bar 层 + 3D-statistics overlay。

### 5.1 8-state 利用率模型

```
statWorkingPortion      -- actively producing
statSetupPortion        -- in setup (changeover)
statWaitingPortion      -- idle, waiting for input
statBlockedPortion      -- blocked by downstream
statPoweringUpDownPortion  -- powering up or down
statFailedPortion       -- in failed state
statStoppedPortion      -- explicitly stopped (NOT fluid objects)
statPausedPortion       -- paused (NOT fluid objects)
```

### 5.2 5-mode sort(`sortStats(criteria)`)

| Code | Sort key |
|---|---|
| 1 | working (descending) |
| 2 | setup |
| 3 | working + fail |
| 4 | working + fail + pause |
| 5 | working + setup + fail + pause |

实现:用 **hidden col 10** 预计算 sort key,再 `resStats.sort(colSort, "down")`。Hidden columns 是 Plant Simulation idiom for "computed sort keys without polluting the visible schema"。

### 5.3 流体特殊化

`isFluid` 触发分支,`statStoppedPortion` 和 `statPausedPortion` **不存在**(continuous-flow 对象不能 "paused" or "stopped")。代码强制 `blocking/fail/powering/pause = 0` for pipes。

> **Lesson**:Plant Simulation 的 stat 模型对 fluid vs discrete 对象**不同**。读 `stat*Portion` 前**始终** check `internalClassName`。

### 5.4 Variable vs DataTable for color map

```simtalk
-- BottleneckAnalyzer(Variable)
colors[1, "Working"] := makeRGBValue(...)
colors[1, "Setup"]   := ...

-- EnergyAnalyzer(DataTable)
Working       → RGB
Setting_up    → RGB
```

> **Lesson**:固定 enum-to-RGB 映射用 **Variable**(更快);user-editable 映射用 **DataTable**。

## 六、EnergyAnalyzer — observer + 可视化

Find energy-active objects → register observer on `PowerInput` → on change,更新 DataTable + roll up custom attrs → visualize via 2D ellipses + 3D cones。

### 6.1 Observer 模式(canonical)

```simtalk
-- prepareObserver(true):为每行注册
o.addObserver("PowerInput",
              absPathOfMethod(~.observeEnergyState))

-- observeEnergyState(valueName, oldValue):runs whenever PowerInput changes
-- 签名 MUST be (valueName: string, oldValue: any)
```

> **Critical**:observer 签名 `(valueName, oldValue)` 是强制的。Plant Simulation 用这两个参数 dispatch observers——搞错签名静默破坏 callback。

### 6.2 Curve-aware 2D/3D 定位

`VisObject` 有两个分支:

1. **曲线对象**(Conveyors, Tracks)——用 `getCurveSegments` + axes math to project arc-length position → pixel position。Right/left-turn handling 是 explicit。
2. **非曲线对象**——使用 bounding-box center。

3D placement 也 curve-aware:`curve-aware offset` on top of `(x, y, z3D_lowerSurface)`。

> **Lesson**:per-object overlays always handle curves differently from non-curves。

### 6.3 递归 name uniqueness

```simtalk
-- isNameUniqueEverywhere
if not frame.isNameUnique(name)
  return false
end
for each child in frame
  if child is Network
    if not isNameUniqueEverywhere(child, name)
      return false
    end
  end
end
return true
```

> **Lesson**:3D / 2D group names 必须 globally unique across all child Networks。Plant Simulation 的 `isNameUnique` 只检查 immediate parent。

## 七、A/B baseline-vs-instrumented 设计 — drift 风险

Assembly1 与 Assembly2 是**两个平行的同一装配线实例**。它们共享拓扑但不共享 analyzers:

| Aspect | Assembly1 | Assembly2 |
|---|---|---|
| Children | 113 | 113 + analyzers |
| PreProduction | embedded | embedded(同实例?—— 未验证) |
| PalletOptimization | ✅ | ❌ |
| BufferOptimization | ❌ | ✅ |
| BottleneckAnalyzer | ❌ | ✅(13 methods) |
| EnergyAnalyzer | ❌ | ✅(17 methods, 12 in source) |

### 7.1 Drift risk:`PalletOptimization` ≡ `BufferOptimization`

failed BFS run 发出**完全相同的方法列表** up to char 11971。这是 `BufferOptimization` 是 `PalletOptimization` **duplicate-and-rename** 的强证据。

**风险**:任一边独立编辑,两边都会 silently diverge。没有 `inheritsFrom` 或 template link。

**Mitigation 选项**(尚未应用):

1. Convert one to inherit from the other(Plant Simulation supports Frame inheritance)
2. Make `BufferOptimization` a Frame with shared base methods via parent class
3. 至少添加 self-check method 在任何编辑后断言两边 byte-identical

## 八、可借鉴模式总结

| 模式 | 出处 | 价值 |
|---|---|---|
| UserObjects 二级拆分 | assembly-line | Classes(可复用)vs Modules(实例模板)清晰分离 |
| Frame-with-UI | WorkerChart | 拖拽式 UI 组件标准结构 |
| 4-state ExperimentManager + 规则引擎 | PalletOptimization | 用户可配置实验流程 |
| 8-state utilization + 5 sort modes | BottleneckAnalyzer | 标准 Plant Simulation "where did the time go" 模式 |
| Observer 模式 | EnergyAnalyzer | 属性变更触发自定义逻辑 |
| Curve-aware 2D/3D 定位 | EnergyAnalyzer.VisObject | 曲线 vs 非曲线的差异化渲染 |
| Hidden col for sort key | BottleneckAnalyzer.sortStats | 不污染 visible schema 的计算列 |

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->
</content>
</invoke>
# Student Note — SevenAxisRobot.OnPull 完整源码 dump(成功)+ Quirk 修正
**Date:** 2026-09-02  **Agent:** plant-simulation-student
**Model:** .Models.SevenAxisRobot.SevenAxisRobot(OnPull method)  **Scenario:** onpull-dump
**Duration:** 21:39 – 21:40  **Skills called:** local-simtalk-execution(simtalk_run + readlog,4 次调用含用户建议的 `robot.&OnPull.Program` 语法)
**Baselines consulted:** 沿 prior `2026-09-02-SevenAxisRobot-onpull-attempt.md`(本 session 校正其结论);`2026-09-02-AGVWithRobot-agv-dispatch-deepdive.md`(对比 OnExit 简化)
**Result:** success — OnPull 60+ 行 SimTalk 源码完整 dump

---

## 🎯 关键:正确的 callback method dump 语法

🆕 **`obj.&MethodName.Program`** 是 dump Station callback-attached methods 的正确语法:

```simtalk
var robot: object := str_to_obj(".Models.SevenAxisRobot.SevenAxisRobot")
print robot.&OnPull.Program    -- ✅ 工作
```

| 写法 | 结果 |
|---|---|
| `print s.OnPull.Program` | ❌ "Unknown identifier 'FwBlockListEntry1'"(编译器尝试按属性访问解析 `OnPull`,失败报内部别名错) |
| `print robot.&OnPull.Program` | ✅ **正确** — ref operator 直接解析 method 引用,返回 Program |
| `print robot.&OnExit.Program` | ❌ "ref-operator cannot find the object 'OnExit'"(本 Station 无 OnExit method) |
| `print robot.&Entry.Program` | ❌ 同上(本 Station 无 Entry) |
| `print s.&OnExit.Program`(AGVWithRobot Station1) | ✅ 工作 — 沿用同样语法 dump 出 OnExit 源码(与 prior session str_to_obj("...OnExit") 路径 dump 一致) |

**规则**:`&MethodName` 是 ref-operator 的 method-name 形式,直接解析为 method 引用;`.Program` 在 ref 上工作。**这与 `&s.PullCtrl` 失败(`PullCtrl` 是 string attr,不是 method name)有本质区别**。

🆕 **Quirk #21/#23/#24 修订**(基于本 session 实测):
- **#21 保留**:PullCtrl 作为 `var m: object := s.PullCtrl` 赋值时变 void(因 PullCtrl 是 string attr 不是 object)
- **#23 修订**:`FwBlockListEntry1` **不是**内部编译别名 — 它是 `s.OnPull` 当作属性访问时编译器尝试解析 forward block list 的失败标记;实际 `?.FwBlockListEntry1` 在 OnPull 方法体内**是合法的 current-MU forward list iterator**(见下面源码 line 3)
- **#24 修订**:`&` operator **不**是 universal 编译错 — `&MethodName` 工作,仅 `&PropertyName` / `&s.PullCtrl` 等不合法组合失败

---

## 01-factory-know-how
### 观察(Observe)— SevenAxisRobot Station OnPull 完整源码

```simtalk
if self.NumInExecution > 1 then return end
-- Check if pull control is already in execution

var Part       = ?.FwBlockListEntry1     -- 第 1 个待处理 MU
var Robot      = ?                         -- 当前 Robot Station 自身
var Poses      = Robot._3D.Poses           -- 3D pose sequencer
var RobotBase  = Robot._3D.getObject(1)    -- 3D 对象层级:base
var RobotBaseZ = RobotBase.getObject(1)    -- base 子对象:z 轴关节

while part /= void
    ?.EnforceProcessing = true            -- 防止 Exit 触发

    var PartLocation = part.~

    var partPosition:length[3] = Robot._3D.getPositionOfObject(part)

    -- Move robot to the pick position
    Robot.state = "DrivingEmpty"
    if partPosition.x < 0
        RobotBase.moveTo(0)
    elseif partPosition.x > Robot.RailLength
        RobotBase.moveTo(Robot.RailLength)
    else
        RobotBase.moveTo(partPosition.x)
    end
    waituntil Poses.EndPoseWasReached

    -- Rotate z-Axis
    Robot.state = "Loading"
    RobotBaseZ.moveToMU(part); waituntil Poses.EndPoseWasReached
    Poses.moveToMU(part); waituntil Poses.EndPoseWasReached

    Robot.state = "Damping"; wait Robot.DampingTime

    Robot.state = "Loading"
    waituntil not self.~.Failed
    part.move(Robot,0)
    waituntil part.RearLocation = Robot

    -- Move to transport pose
    Robot.state = "DrivingFull"
    Poses.moveTo("TransportPose"); waituntil Poses.EndPoseWasReached

    -- Move Robot to Destination
    Poses.moveTo("Init"); waituntil Poses.EndPoseWasReached
    var DestinationObject: Object
    if Robot.cont.Destination = void
        if robot.succ = void
            throwRuntimeError(to_str(self.~)+": No destination for MU defined!")
        else
            DestinationObject = robot.succ(z_uniform(1, robot.NumSucc+1))
        end
    else
        DestinationObject = Robot.cont.getRouteIntermediateDestination
    end

    -- Move to the drop position
    var dropPosition = Poses.getMUAnimationPosition(part, DestinationObject.pe)
    var maxX = Robot.RailLength - 1.08m
    if dropPosition.x > maxX
        RobotBase.moveTo(maxX)
    elseif dropPosition.x < 0
        RobotBase.moveTo(0)
    else
        RobotBase.moveTo(dropPosition.x)
    end
    waituntil Poses.EndPoseWasReached

    -- Rotate z-Axis
    RobotBaseZ.moveToMUAnimationPosition(part, DestinationObject.pe)
    waituntil Poses.EndPoseWasReached

    PartLocation := DestinationObject
    if DestinationObject.full or DestinationObject.failed or DestinationObject.pause
        Robot.state = "Blocked"
        waituntil not Destinationobject.Full and not DestinationObject.failed and not DestinationObject.pause
    end
    Robot.state = "Unloading"
    Poses.moveToMUAnimationPosition(part, DestinationObject.pe)
    waituntil Poses.EndPoseWasReached

    if not part.move(DestinationObject)
        Robot.state = "Blocked"
        waituntil part.location /= Robot
        Robot.state = "Unloading"
    end

    Robot.state = "Damping"; wait ?.DampingTime
    Robot.state = "DrivingEmpty"

    -- Move to transport pose
    Poses.moveTo("TransportPose"); waituntil Poses.EndPoseWasReached

    -- Move to init pose
    Robot._3D.Poses.moveTo("Init"); waituntil Poses.EndPoseWasReached

    ?.EnforceProcessing = false
    part = ?.FwBlockListEntry1    -- 链式处理下一个 MU
end

?.EnforceProcessing = true
Robot.state = "DrivingHome"
Poses.moveTo("HomePosition"); waituntil Poses.EndPoseWasReached
?.EnforceProcessing = false
Robot.state = "Waiting"
```

### 关键设计模式

| 模式 | 实现 | 教学价值 |
|---|---|---|
| **重入保护** | `if self.NumInExecution > 1 then return end` | 防止 Station.PullCtrl 递归触发 |
| **MU 队列迭代** | `var part = ?.FwBlockListEntry1; while part /= void; ...; part = ?.FwBlockListEntry1` | Station 内部 MU forward block list 链式处理 |
| **3D Pose 系统** | `Robot._3D.Poses.moveTo("TransportPose"/"HomePosition"/"Init")` | PS 标准 3D 动画 pose 序列 |
| **3D 位置查询** | `Robot._3D.getPositionOfObject(part)`, `Poses.getMUAnimationPosition(part, DestinationObject.pe)` | MU 在 3D 空间的坐标获取 |
| **3D 关节链** | `Robot._3D.getObject(1)` → `RobotBase`(base); `.getObject(1)` → `RobotBaseZ`(z 轴关节) | 7 轴机器人通过嵌套 3D 对象表示 |
| **状态机字符串** | `Robot.state = "DrivingEmpty"/"Loading"/"DrivingFull"/"Damping"/"Unloading"/"Blocked"/"DrivingHome"/"Waiting"` | 8 个离散状态覆盖所有动作 |
| **阻尼模拟** | `Robot.state = "Damping"; wait Robot.DampingTime` / `wait ?.DampingTime` | 真实机器人拾放后的稳定时间 |
| **分支 routing** | `DestinationObject = robot.succ(z_uniform(1, robot.NumSucc+1))` | 出口路由:succs 随机选(无显式 Destination 时) |
| **阻塞 + 重试** | `if DestinationObject.full; state = "Blocked"; waituntil not ...Full and not ...failed and not ...pause end` | 目标 Station 不可达时阻塞 + 等待 |
| **EnforceProcessing flag** | `?.EnforceProcessing = true/false` | 防止 MU 在 OnPull 处理期间被 Exit 触发 |

### 理论对照(Reference + Judge)
| 观察 | Baseline 出处 | 判定 | Evidence |
|---|---|---|---|
| `?.FwBlockListEntry1` 是 MU forward list iterator | `02-domain-know-how/03-modeling-know-how/02-simtalk/language-quirks-reference.md`(未深读) | ⚠️ diverges — 反转 prior #23 误判 | 实际 `?.FwBlockListEntry1` 是**合法 SimTalk 表达式**,返回当前 Station 第一待处理 MU 引用 |
| 3D Pose 系统 API | `01-plant-simulation-help/objects/material-flow-objects/Station/README.md`(沿 prior,未深读 3D pose) | ✅ matches | PS 标准 3D 动画 API:`_3D.Poses.moveTo(...)`、`moveToMU(...)`、`EndPoseWasReached` |
| `z_uniform(1, robot.NumSucc+1)` 闭区间 +1 off-by-one | `language-quirks-reference.md`(未深读) | ⚠️ confirmed Quirk | 与 prior `2026-09-02-Models-RobotSet-robot-set-overview.md` §02 "Quirk #7 z_uniform off-by-one" 同模式 — 用户代码再次确认此写法 |
| 8 状态字符串(`Robot.state = "DrivingEmpty"` 等) | baseline 未覆盖 | 🆕 Novel | 这是**用户自定义 state attribute 字符串状态机**模式 — PS 标准不是 enum,只是 string 属性 |
| `?.DampingTime` 是 Variable/Attribute | baseline 未明文 | 🆕 Novel | `?` 指当前 MU,`?.DampingTime` 读 MU 上的 DampingTime 属性 — MU 自带动画属性 |
| `throwRuntimeError` | `02-simtalk/control-flow-error-handling/README.md`(沿 prior) | ✅ matches | 标准 PS 错误抛出 API |
| `part.move(DestinationObject)` / `part.move(Robot,0)` | `01-plant-simulation-help/simtalk/predefined-functions-i-os-math-string-datetime/README.md`(沿 prior) | ✅ matches | MU `move` API:1 参=移动到对象;2 参=移动到对象 + 入口 index |

### 候选 finding
- **PS Station OnPull callback 标准模式** → 建议 curator 评估在 `02-domain-know-how/04-modeling-example/seven-axis-robot-anim-controller.md` 新增完整教学案例(baseline:本 session §01 完整源码)
- **`z_uniform(1, NumSucc+1)` off-by-one** → 沿 prior RobotSet finding 扩展,本 session 再次确认
- **Robot.state string 状态机模式** → 建议 curator 评估在 `02-domain-know-how/01-factory-know-how/factory-modeling-architecture.md` 新增"3D 机器人动画状态机约定"小节

---

## 02-simtalkclaude-knowhow
### 观察(Observe)
- 🆕 **Quirk #21/#23/#24 重大修订**(基于本 session):
  - **#21 保留部分**:`var m: object := s.PullCtrl` 赋值为 VOID — 因为 PullCtrl 是 string attr("self.OnPull"),object 类型不匹配
  - **#23 反转**:`FwBlockListEntry1` **不是**PS 内部方法别名 — 它是**合法 SimTalk 表达式**(`?.FwBlockListEntry1` 在 OnPull 方法体内用作 MU 迭代器);之前的 "Unknown identifier 'FwBlockListEntry1'" 错误是 **`s.OnPull` 按属性访问解析失败**的副作用
  - **#24 修订**:`&` ref-operator **不**是 universal 编译错 — `&MethodName` 在 method 存在时干净工作,只在不存在的 method 上报 "ref-operator cannot find the object 'X'"
- 🆕 **新 Quirk #26**:`s.OnPull` 与 `s.&OnPull` **行为不同**:
  - `s.OnPull`(无 `&`)= 属性访问 = 编译器尝试按 `s.@OnPull` 解析 slot,失败报 "Unknown identifier 'FwBlockListEntry1'"
  - `s.&OnPull`(有 `&`)= ref operator = 解析 method 引用,失败时干净报 "cannot find the object"
  - 推测:`FwBlockListEntry1` 错误是 PS 编译器在 `s.OnPull` 属性访问失败时的 fallback 标记**(检查 forward block list entry 1 是否存在)**
- ✅ **修正 prior #20 部分**:`str_to_obj(path)` 对 callback-attached Method **确实**返回 VOID(path 不可寻址),但**正确 dump 语法**是 `obj.&MethodName.Program`

### 理论对照
| 观察 | Baseline 出处 | 判定 |
|---|---|---|
| `&MethodName.Program` 是 callback dump 标准 | `lifelines.md`(未涉及);`local-simtalk-read-library/SKILL.md`(假设 Method 可枚举,未涉及 callback) | 🆕 Novel — student 必须知道这条 SOP 才能 dump Station callback methods |
| Quirk #21/#23/#24 需修订 | `quirks-canonical.md` 暂无相关条目 | ⚠️ 修订申请 |

### 候选 finding
- **dump Station callback method SOP** → 建议 `@skills-optimizer` 评审:① `02-simtalk/language-quirks-reference.md` 新增 "PS 2.0 callback method dump 语法:`obj.&MethodName.Program`";② 修订 Quirk #21/#23/#24;③ read-library SKILL.md Limitations 补"callback-attached methods 用 `obj.&MethodName.Program` 路径 dump,**不**依赖 path 寻址"
- **Quirk #26 `s.OnPull` vs `s.&OnPull` 行为差异** → 候选新 Quirk,进 `language-quirks-reference.md`

---

## 03-modeling-know-how
### 01-objects
- **SevenAxisRobot Station 内部完整结构**(基于 OnPull 源码 + prior onpull-attempt):
  - 属性:`Name` / `~` / `ProcTime=0` / `CycleTime=0` / `SetupTime=0` / `Capacity=1` / `NumMU` / `Setup=false` / `Pause=false` / `MTTR=0` / `ExitCtrl=VOID` / `PullCtrl="self.OnPull"` / **`Robot.state`(string 属性,8 个状态值)**
  - **不可访问属性**:`numNodes` / `NumNodes` / `EntryCtrl` / `OnExit`(Station 上不存在该 method)
  - **存在 method**:`OnPull`(完整 dump 60+ 行)— 通过 `s.&OnPull.Program` 访问

### 02-simtalk
- **OnPull 完整 SimTalk 字面契约**(本 session 全部 dump):
  - `if self.NumInExecution > 1 then return end` — 重入保护
  - `?.FwBlockListEntry1` — 当前 Station 第一待处理 MU
  - `Robot._3D.Poses` / `Robot._3D.getObject(1)` — 3D 对象访问链
  - `Robot.state = "X"` — 字符串状态赋值(非 enum)
  - `part.move(Robot, 0)` / `part.move(DestinationObject)` — MU 移动 API
  - `waituntil Poses.EndPoseWasReached` — 3D 动画完成同步
  - `Robot.cont.Destination` / `Robot.cont.getRouteIntermediateDestination` — MU 自带 Destination 属性
  - `robot.succ(z_uniform(1, robot.NumSucc+1))` — 随机选 succ
  - `throwRuntimeError(...)` — 错误抛出

### 03-software
- 本 session 4 次 simtalk_run + 4 次 readlog(用户建议的 `robot.&OnPull.Program` 1 次成功 + 验证 OnExit/Entry 不存在 + AGVWithRobot Station1 OnExit 复用测试)
- **核心 skill 经验**:
  - **`obj.&MethodName.Program` 是 dump Station callback method 的标准 SOP** — 学生必知
  - **错误信息可区分 method 不存在 vs method 内部错误**:`"ref-operator cannot find the object 'X'"` 是干净错误(说明 method 不存在);`"Unknown identifier 'FwBlockListEntry1'"` 是 fallback 标记(说明按属性语法解析失败)
  - **可移植性**:`robot.&OnPull.Program` 语法对 SevenAxisRobot Station1 与 AGVWithRobot Station1 都工作,应作为通用 SOP

---


> **续见** [part2](./2026-09-02-SevenAxisRobot-onpull-dump-part2.md)

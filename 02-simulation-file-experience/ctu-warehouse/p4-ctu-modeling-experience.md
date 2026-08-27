# P4_CTU 模型经验 — 2026-08-27

> **来源**：从 `P4_CTU`（用户导入的"CTU + AGV 仓库调度"模型）dump 全部 86 个 Method
> 源码后整理。所有方法均通过 `simtalk_run` + `readlog` 实测读回，无推测。
> Artifacts: `/tmp/p4ctu_methods.jsonl`（86 行，每行一个 method 的 path + 完整 program）

## 一、模型是什么

**业务背景**：CTU（Compact Tower Unit，堆垛机/立库提升机）+ AGV（自动导引车）混合调度的
自动化立体仓库。Rack（货架）上每个 bin 可放 1~2 件 MU（Part/Box），

- **入库**：Source → AGV → 接驳点（rack1/rack2 的第一层）→ CTU → 货架 bin
- **出库**：货架 bin → CTU → 接驳点 → AGV → Drain

## 二、目录与架构总览（一图看清）

```
.P4_CTU                                  ← 用户自定义 **类库文件夹**（Origin=VOID, Class=VOID）
├── ctux1_agvx1, ctux1_agvx2             ← **模板 Frame 类**（2 个变体，每个 1 AGV + 1 CTU）
├── BasicObjects/                        ← 类库副本（MaterialFlow/Resources/InformationFlow/MUs/UserObjects）
│   └── PartA, PartB, Box, MyFrame       ← 用户自定义 MU 类
├── AdvancedObject/
│   ├── Hardware/                        ← **硬件类**
│   │   ├── AGV        (Transporter, Origin=.MUs.Transporter)
│   │   ├── AGVPool    (AGVPool)
│   │   ├── Rack       (Frame 类，含 v_x/v_y/bin_l/bin_w/... + m_init + 2 个 Store)
│   │   ├── CTU        (Folder，承包装 CTU 设备的多种类)
│   │   │   ├── CTU        (Transporter)
│   │   │   ├── Lifttable  (Container，CTU 提升台)
│   │   │   ├── Carrier, Carrier_Box
│   │   │   └── test       (Frame，单元测试用 Track)
│   │   └── Store      (Store)
│   └── Software/                        ← **软件 / 控制类**
│       ├── RCS                       (Frame 类 — Rack Control System，控制中枢)
│       ├── MapGenerator              (Frame 类 — 根据 Rack 包围盒动态生成网格 + Marker + Connector)
│       ├── MapGenerator.*           (Frame 类变体：Home / ChargingPlace / StockInLoader / StockOutLoader / Transparency)
│       └── ...
```

### 2.1 这一架构最反直觉的地方 — "模型是放在类库里的"

`.P4_CTU` 这个节点的 `InternalClassType = "Folder"`、Origin=VOID、Class=VOID——
**它不是 Frame 实例，而是 Class Library 里的一个 Folder（用户自定义类库）。**

里面所有东西（Hardware.Rack、Software.RCS、ctux1_agvx1 等）都是 **类定义**。
用户实际跑仿真时，要 `duplicate(.P4_CTU.ctux1_agvx1, .Models.Model)` 把模板拖进运行
视图，才能产生实例。

> **为什么要这么做？** 把"模型"打包成一个可重用的"类库包"——
> 任何新模型只要在 Class Library 里 import `.P4_CTU`，然后从 `.P4_CTU.ctux1_agvx1`
> 派生 / 复制一个 Frame 实例到 `.Models.Model`，就完整复制了整套硬件 + 软件 + 调度逻辑。
>
> **可借鉴度**：⭐⭐⭐⭐⭐。比 "把代码写在 .Models.Model 里" 强 10 倍。

### 2.2 BasicObjects — 让模型"自带类库"

```
.P4_CTU.BasicObjects.MaterialFlow.Station   ← duplicate 自 .MaterialFlow.Station
.P4_CTU.BasicObjects.MUs.Transporter        ← duplicate 自 .MUs.Transporter
.P4_CTU.BasicObjects.Resources.AGVPool      ← duplicate 自 .Resources.AGVPool
```

模型自己带了一份 Plant Simulation 内置类库的副本，**不依赖用户机器上的内置库版本/补丁**。

实测确认：`.P4_CTU.AdvancedObject.Hardware.AGV` 的 `Origin` 是
`.P4_CTU.BasicObjects.MUs.Transporter` 而不是 `.MUs.Transporter`——
**继承链指向本地副本而非全局类库**。这就是"模型可移植"的精髓。

## 三、控制中枢 — RCS（Rack Control System）

> `.P4_CTU.AdvancedObject.Software.RCS` 是一个 Frame 类，挂着 40+ 个 Methods 和 12 个 DataTables。
> 它是整个调度的"大脑"。

### 3.1 RCS 内部数据结构（全部是 DataTable）

| DataTable | 列数 | 作用 |
|---|---|---|
| `tab_taskPool` | ~7 | 全局任务池（In/Out 订单）。State ∈ {`not start`, `created AGV transported task`, `created CTU transported task`} |
| `tab_taskPoolDatabase` | ~8 | 已完成任务归档（包含 TaskCompleteTime） |
| `tab_TransportationTask_AGV` | ~8 | AGV 运输任务队列（MUReady / CurAGV / Start / End） |
| `tab_TransportationTask_CTU` | ~14 | CTU 运输任务队列（含 BinID / RackMarker / CTUMarker / CTU / 起点终点） |
| `Tab_binState` | ~9 | 每个 bin 一行（BinID / Rack_de / Rack_ex / RackRow / RackCol / Content_de / Content_ex / Binstate / NumMU / CTUMarker） |
| `Tab_MU_info` | ~4 | MU → bin 映射（MU / BinID / BinType / State） |
| `Tab_RackMarker` | ~5 | 货架第一层接驳点（Marker / State / rack / row / col） |
| `Tab_HomeState` | ~1 | AGV/CTU home 点位（HomePosition） |
| `Tab_ChargingPlace` | ~1 | 充电桩点位 |
| `tab_agv_state` | ~6 | 每台车一行（Vehicle / State ∈ {`Idle`, `Running`, `Charging`}） |
| `RackList` | (list) | 已注册货架列表 |
| `InitFinished` | (boolean) | "初始化完成"标志，下游用 `waituntil RCS.InitFinished` 同步 |

> **设计要点**：**一切状态都在 DataTable 里**。没有散落在 object attribute 上的可变状态。
> 这让 RCS 完全可以"重启+数据驱动"——清空 DataTable 就等于冷启动。

### 3.2 三级执行器架构

```
              m_StockIn() / m_StockOut()          ← 用户入口
                       ↓ appendrow
                 tab_taskPool
                       ↓ append + triggerpoint
                  m_TaskExcuter                  ← L1: 订单分发（while + sort + 多 case）
                  ├─ In  → m_CreateTransTask_AGV_In + m_CreateTransportationTask_CTU_In
                  └─ Out → m_CreateTransportationTask_CTU_Out + m_CreateTransTask_AGV_Out
                       ↓ append
        tab_TransportationTask_AGV + tab_TransportationTask_CTU
                       ↓ triggerpoint
       m_AGVExcuter              m_CTUExcuter    ← L2: 设备级调度
       ├─ findFreeAGV            ├─ findFreeCTU
       ├─ agvGetTask             ├─ 选最近任务
       └─ executeNewCallChain    └─ executeNewCallChain
                       ↓
        AGV/CTU m_executeTransportationOrder    ← L3: 设备内部执行（move + pick + drop）
```

**关键代码骨架**（`m_TaskExcuter` 摘录）：

```simtalk
while tab_taskPool.ydim > 0
    tab_TransportationTask_AGV.sort("Priority","TaskTime",["down","up"])
    for var i:=1 to tab_taskPool.ydim
        if tab_taskPool["State",i] = "not start"
            ordertype := tab_taskPool["TaskType",i]
            switch ordertype
            case "In"
                bin := m_getFreeBin(tab_taskPool["MU",i])
                if bin = "" then continue end
                tab_taskPool["BinID",i] := bin
                if not m_CreateTransTask_AGV_In(...) then continue end
                if not m_CreateTransportationTask_CTU_In(...) then continue end
            case "Out"
                if not m_CreateTransportationTask_CTU_Out(...) then continue end
                if not m_CreateTransTask_AGV_Out(...) then continue end
            case "Move"
                debug   -- ← TODO 占位
            else
                debug   -- ← TODO 占位
            end
        end
    next
    m_AGVExcuter_triggerpoint
    m_CTUExcuter_triggerpoint
    wait 60    -- 每 60 秒轮询
end
```

**模式总结**：
- **while 死循环 + wait 60**：不靠事件，靠轮询
- **sort + find 优先**：用 DataTable 排序模拟优先级队列
- **state machine by string**：State 字段是字符串字面量（`"not start"` / `"Idle"` / `"Running"`），可读性好但无类型检查
- **`continue` + `exitloop` 守门**：资源不够就跳过本轮，等下次

### 3.3 触发点防重入模式（**重要复用点**）

所有 `_triggerpoint` 方法都用 `xxx_Running` boolean + `executeNewCallChain` 防重入：

```simtalk
-- m_TaskExcuter_triggerpoint
if TaskExcuter_Running then
    m_logger("INFO","Excuter已触发，无需重复触发")
    return
end
TaskExcuter_Running := true
m_logger("INFO","Excuter未触发，触发")
&m_TaskExcuter.executeNewCallChain
```

**为什么用 `executeNewCallChain` 而非直接调用？**
- 直接调用会**阻塞当前方法**直到 executor 跑完（executor 是 while 死循环）
- `executeNewCallChain` 把任务扔到**新的 call chain**上异步执行，当前方法立即返回
- 配合 `_Running` 标志位，确保**全模型只有一个 executor 实例**在跑

> **可借鉴度**：⭐⭐⭐⭐⭐。任何"长跑 worker"（仿真心跳 / 日志写盘 / 状态广播）都用这套三件套。

### 3.4 bin 分配算法（`m_getFreeBin`）

```simtalk
Tab_binState.sort("NumMU","up")       -- 1) 按当前 MU 数升序排
Tab_binState.setcursor(8,1)           -- 2) 定位到 Binstate 列
if tab_binstate.find(0)               -- 3) 找一个空 bin（无 MU）
    bin := Tab_binState["BinID",tab_binstate.cursory]
    Tab_binState["Binstate",tab_binstate.cursory] := "Occupied"
    Tab_MU_info.appendrow(mu,bin,"DE","OnTranportation")
    return bin
else                                  -- 4) 没有空 bin → 找一个只放了 1 个的（DE 已满，看 EX）
    Tab_binState.setcursor(8,1)
    if tab_binstate.find(1)
        bin := Tab_binState["BinID",tab_binstate.cursory]
        Tab_binState["Binstate",tab_binstate.cursory] := "Occupied"
        Tab_MU_info.appendrow(mu,bin,"OnTranportation")   -- 注意：NumMU=1 分支 appendrow 只 3 个参数，没有 "DE"
        return bin
    else
        bin := ""
        return bin
    end
end
```

**模式总结**：
- **两层深度（DE + EX）**：每个 bin 可放 2 件 MU，状态字段用 NumMU（0/1/2）
- **优先填 NumMU=0 的 bin**——减少"半空 bin"
- **找不到 bin 就返回空串**——上游 `m_TaskExcuter` 用 `if bin = "" then continue end` 跳过

### 3.5 完成回调（`m_AGVCompleteTask` / `m_CTUCompleteTask`）

每台 AGV/CTU 完成任务后回 RCS 报到，**RCS 集中释放资源**：

```simtalk
-- m_AGVCompleteTask (param mu:object)
var agv_row := tab_TransportationTask_AGV.getrowno(mu)

-- 1) 更新 AGV 状态
if ?.b_needcharging = false
    tab_agv_state["State",?] := "Idle"
else
    tab_agv_state["State",?] := "Charging"
end

-- 2) In：物料送到接驳点 → 通知 CTU 可以取货
var row := tab_taskPool.getrowno(mu)
if tab_taskPool["TaskType",row] = "In"
    tab_TransportationTask_CTU["MUReady",mu] := true   -- 解锁 CTU 任务
else
    -- Out：归档订单 + 释放接驳点
    tab_taskpool.copyrangeto({0,row}..{*,row}, tab_taskpooldatabase, 0, tab_taskpooldatabase.ydim+1)
    tab_taskpooldatabase["TaskCompleteTime",tab_taskpooldatabase.ydim] := root.eventcontroller.abssimtime
    var rackmarker := tab_TransportationTask_AGV["Start",agv_row]
    Tab_RackMarker["State",rackmarker] := "Available"
    tab_taskpool.CUTROW(ROW)
end

-- 3) 删 AGV 任务 + 触发下一轮
tab_TransportationTask_AGV.cutrow(agv_row)
m_AGVExcuter_triggerpoint
```

**两个 `CUTROW` 的拆解**：
- `tab_taskpool.CUTROW(ROW)` — **Out 分支内**，删除 tab_taskpool 中本订单（前提是已完成数据库归档）
- `tab_TransportationTask_AGV.cutrow(agv_row)` — **if/else 之后**，删除 tab_TransportationTask_AGV 中本 AGV 任务行（两个调用 **target 不同表**，**不冲突**）

**几个关键 trick**：
- `?.b_needcharging`：`?` 是"当前方法所属对象"（这里就是 AGV 实例）
- `tab_TransportationTask_CTU["MUReady",mu] := true`：用 MU 当 key 找到 CTU 任务行
- `tab_taskpool.copyrangeto({0,row}..{*,row}, ...)`：归档完成任务到 database
- 任务完成**不是删自己处理**，而是**叫 RCS 来**——避免每个设备各自维护全局状态

## 四、自动注册 / 生命周期 hook 模式

### 4.1 `OnCreate` / `OnDelete` / `OnMove` 三件套

每个会"出现在场景里"的对象都挂这三个方法：

```simtalk
-- MapGenerator.Home.m_Oncreate
if not (current.~.extendPath("RCS") = void)
    RCS := current.~.extendPath("RCS")
    RCS.m_addHomePosition(current)
else
    messagebox("Please Insert RCS First")
end

-- m_ondelete
if RCS = void then return end
RCS.m_DeleteHomePosition(current)

-- m_OnMove (param old, new : length[3])
if RCS = void then return end
RCS.m_getMinMaxCoordinate
```

**注册/反注册对称**——OnCreate 注册到 RCS、OnDelete 反注册、OnMove 触发包围盒重算。

> **可借鉴度**：⭐⭐⭐⭐⭐。任何"动态往 Frame 里拖对象"的场景都该用这个 hook，
> 不然用户得手动在 init 里 `for child in frame: rcs.add(child)`。

### 4.2 mapbox-style 错误提示

`messagebox("Please Insert RCS First")`——这与 v18+ 的 `infoBox(text, false)` 模态陷阱
**冲突**！会卡死 GUI / socket。

> **❌ 反模式**：在生命周期 hook 里用 `messagebox(...)` 模态弹窗
> **✅ 正确**：用 `print("ERROR ...")` 或 `infoBox(text, false)` 非模态
>
> （注：用户导入的模型用了旧式 messagebox；本地开发时千万别照搬）

## 五、MapGenerator — 动态生成地图

### 5.1 整体流程

```
m_UpdateMap (总入口)
  ├─ m_creategrid         ← 按 RCS.min_x/max_x/y 划分网格
  ├─ m_UpdateRack_Map     ← 在每个 Rack 第一层创建 RackMarker + AGVOnlyMarker
  ├─ m_createCTURack      ← 在合适网格上创建 CTURackMarker
  ├─ m_createSpecPosition ← 在 Home/Charging 位置覆盖 Marker
  ├─ m_UpdateActiveMap    ← 其余空网格填充 ActiveMarker
  └─ m_createConnector    ← 相邻 Marker 间建 Connector
```

### 5.2 网格生成算法（`m_creategrid`）

```simtalk
var cur_x := RCS.min_x
var cur_y := RCS.min_y
var gridid := 1
var frame_rack := RCS.racklist[1]
var rack = frame_rack.rack1
bin_x := rack._3d.dimensions[1] + rack._3d.gap
bin_y := rack._3d.dimensions[2]

while cur_x < RCS.max_x
    while cur_y < RCS.max_y
        Tab_GridLayout[gridindex_x,gridindex_y] := num_to_str(gridid)
        Tab_Grid.appendRow(num_to_str(gridid),cur_x,cur_y)
        gridid += 1
        cur_y += bin_y
        gridindex_y += 1
    end
    cur_y := RCS.min_y
    cur_x += bin_x
    gridindex_y := 1
    gridindex_x += 1
    if gridid > maxgrid  -- 默认 9999，超出说明配置错
        debug   -- 占位
    end
end
```

### 5.3 关键 trick — `obj._3d.boundingboxmax/min/size/position/dimensions`

```simtalk
coordinate := rack._3d.getworldcoordinate            -- 中心世界坐标
max_c := coordinate + rack._3d.boundingboxmax        -- 最大角
min_c := coordinate + rack._3d.boundingboxmin        -- 最小角
rack._3d.position := [...]                           -- 直接挪对象
rack._3d.dimensions                                 -- [width, length, height]
rack._3d.gap                                        -- 3D 间距
rack._3d.FloorThickness
rack._3d.GroundClearance
```

> **可借鉴度**：⭐⭐⭐⭐。任何"按布局自动布局对象"的场景都用得着。
> 但**注意 _3d 是 Plant Simulation 私有 API**，旧版本可能字段名不同。

### 5.4 CTU 接驳点生成算法（`m_createCTURack`）

按邻接网格 void 数判断"是否应该放 CTURackMarker"：
- 4 邻域 void 数 = 2 → 进入判定（挑选"未占"的那一格）
- 4 邻域 void 数 = 0 或 1 → **源码无显式处理**（fall-through 直接 `CTURackMarker.duplicate`，意味着 voidgrid 是循环最后一次赋值的方向）

⚠️ **纠正**：原始总结中"void 数 = 1 → 角落"的归纳是错的，源码里只对 voidcount=2 做了特殊路径选择；其它情况未在源码中显式注释或显式分支。

```simtalk
IF m_r = void THEN voidCount := voidCount + 1; voidgrid := grid_r END
IF m_b = void THEN voidCount := voidCount + 1; voidgrid := grid_b END
IF m_l = void THEN voidCount := voidCount + 1; voidgrid := grid_l END
IF m_t = void THEN voidCount := voidCount + 1; voidgrid := grid_t END

if voidcount = 2
    -- 根据已知的非 void 邻居，把 voidgrid 调整到对面
    if not (m_r = void) then if m_r.origin.name = "ActiveMarker_AGVOnly"
        voidgrid := grid_l
    end end
    ...
end

m := CTURackMarker.duplicate(TargetFrame)
m._3d.position := [Tab_Grid["x",voidgrid],Tab_Grid["y",voidgrid],0] + [bin_x/2, bin_y/2, 0]
Tab_Grid["m",voidgrid] := m
Tab_CTUMarkList.appendrow(m, Tab_Grid["x",voidgrid], Tab_Grid["y",voidgrid])
```

> **可借鉴度**：⭐⭐⭐⭐。"用表存网格拓扑、用 void 数推断点位类型"——比硬编码坐标灵活得多。
> **但 voidcount≠2 的 fallback 行为是不确定的**——下游 agent 复用这段代码时务必实测各种场景。

## 六、变量命名约定（强烈推荐照搬）

| 前缀 | 含义 | 示例 |
|---|---|---|
| `m_` | Method（私有） | `m_init`, `m_logger`, `m_findFreeAGV` |
| `m_Onxxx` | 生命周期 hook（**但模型自身混用大小写——见下）** | `m_Oncreate`, `m_OnMove`, `m_OnDelete` |
| `m_xxx_triggerpoint` | 防重入触发点 | `m_TaskExcuter_triggerpoint` |
| `v_` | Variable | `v_x`, `v_y`, `bin_w`, `RCS` |
| `l_` | length 数值 | `l_groundclearance`, `l_gap` |
| `b_` | boolean | `b_needcharging`, `backhome` |
| `tab_` / `Tab_` | DataTable | `tab_taskPool`, `Tab_binState` |
| `cur*` | 局部临时 | `cur_x`, `curtime`, `curpro` |
| `obj_*` | 通用 object 引用 | `obj_type` |

> Plant Simulation 大小写不敏感但展示是大小写敏感——
> 用 `m_xxx`（私有）、`Tab_xxx`（全局表）这种前缀区分意图，可读性高 10 倍。

⚠️ **纠正**：原总结给出的生命周期 hook 示例看似一致，但模型内部**混用了至少 5 种大小写**（按实测路径）：

| 实际路径中的写法 | 出处 |
|---|---|
| `m_Oncreate`（O 大写） | `MapGenerator.Home` / `MapGenerator.ChargingPlace` / `StockInLoader` / `StockOutLoader` / `MapGenerator`（root） |
| `m_OnDelete`（O+D 都大写） | `MapGenerator`（root） |
| `m_ondelete`（o+d 都小写） | `MapGenerator.Home` / `MapGenerator.ChargingPlace` |
| `m_oncreate`（全小写） | `Software.Transparency` |
| `m_OnMove`（O+M 都大写） | 所有四类 loader/home/charging |
| `m_onChange`（o 小写 C 大写） | `StockInLoader` / `StockOutLoader` |

外加个别方法完全没有 `m_` 前缀：`StockInLoader.Init`、`StockOutLoader.Init`。
同样是 MapGenerator.Home 下还有 `m_ordering`（小写 o）和 `m_StockIn`（大写 S）这种混用。

**结论**：模型自己的命名并不一致（即使作者尽力统一过）——下游 agent 复用时**永远用精确路径 grep**，别靠"看上去一样的命名"匹配。

## 七、可直接复用的模式 ✅

| 模式 | 出处 | 可借鉴度 |
|---|---|---|
| **"模型即类库"打包法**（`.P4_CTU` 作为可重用 class library） | 整体架构 | ⭐⭐⭐⭐⭐ |
| **BasicObjects 携带类库副本**（自包含、跨机可移植） | `.P4_CTU.BasicObjects` | ⭐⭐⭐⭐⭐ |
| **Hardware/Software 分层**（物理 vs 控制） | `AdvancedObject.Hardware/Software` | ⭐⭐⭐⭐⭐ |
| **DataTable 即状态机**（用表代替散落 attribute） | `Tab_binState` / `tab_agv_state` / `tab_taskPool` | ⭐⭐⭐⭐⭐ |
| **`m_xxx_triggerpoint` + `_Running` + `executeNewCallChain`**（防重入 worker 触发） | 3 个 `_triggerpoint` 方法 | ⭐⭐⭐⭐⭐ |
| **`OnCreate/OnDelete/OnMove` 自动注册** | Home/ChargingPlace/Loader 等 | ⭐⭐⭐⭐⭐ |
| **`m_logger(type, msg)` + 时间戳**（统一日志） | `m_logger` 在 RCS/Rack/MapGenerator 都有 | ⭐⭐⭐⭐ |
| **`tab_xxx.copyrangeto + cutrow`**（任务完成归档） | `m_AGVCompleteTask` / `m_CTUCompleteTask` | ⭐⭐⭐⭐ |
| **三层 executer 调度**（任务→设备→执行） | `TaskExcuter` → `AGV/CTUExcuter` → `m_executeTransportationOrder` | ⭐⭐⭐⭐ |
| **DataTable sort + find 模拟优先级队列** | `tab_taskPool.sort("Priority","TaskTime",["down","up"])` | ⭐⭐⭐⭐ |
| **`{0,row}..{*,row}` 范围复制** | `m_AGVCompleteTask` 归档 | ⭐⭐⭐ |
| **`current.~` / `?.` / `?.~` 跨对象引用** | 整个模型 | ⭐⭐⭐⭐ |

## 八、不建议照搬 ❌

| 反模式 | 后果 | 改进建议 |
|---|---|---|
| **`messagebox(...)` 在 OnCreate 里** | 卡死 GUI / socket 阻塞 | 用 `infoBox(text, false)` 或 `print` |
| **`debug` 关键字当 TODO 占位** | `case "Move"` / `else` 都没实现 | 改成显式 `return false` + log |
| **命名大小写混乱**（生命周期 hook 至少 5 种写法并存：`m_Oncreate` / `m_ondelete` / `m_oncreate` / `m_OnDelete` / `m_onChange`）| 难 grep，精确路径才能命中 | 统一一套，详见 §6 纠正表 |
| **错别字方法名**（`m_get_vihicle_class` 应为 `vehicle`） | 一旦被引用就锁死 | rename 时检查所有引用 |
| **`wait 60` / `wait 15` 硬编码** | 调参要改源码 | 提到 `Frame attribute` 可配置 |
| **冗余字段 `backhome`** 在多个 object（AGV/CTU/Homing）上各自维护 | 状态分裂 | RCS 集中维护 |
| **`m_findFreeAGV` / `m_findFreeCTU` 几乎重复代码**（仅 `agv.name = "AGV"` vs `"CTU"` 区别） | 一改两处 | 用 `for v in tab_agv_state if v.State=Idle` 参数化 |
| **Rack 上的 `RCS` 是 `Variable` 而非 typed `object ref`** | 类型不安全 | 用 `object` 类型或 typed Frame attribute |
| **`m_getDistance` 是空方法**（只剩 param 声明） | 死代码 | 删掉或 `print "TODO"` |
| **`m_calculatePro` 里 debug 块直接改 MU 颜色**（侵入 3D 状态） | 影响正常可视化 | 移到独立 debug toggle |
| **`m_AGVCompleteTask` 里被 `/* ... end*/` 整段注释的 `m_backhome` 调用** | 死代码 + 误导（看上去像有效路径） | 直接删，git 历史可查 |

## 九、可继续挖掘的方向

| 主题 | 价值 | 行动 |
|---|---|---|
| **AGV/CTU 内部 `m_executeTransportationOrder`**（不在 `.P4_CTU.*` 路径下，是设备内部方法） | 看设备怎么和 marker 交互 | 用 `local-simtalk-get-class-inheritance` 查 AGV/CTU 类继承 |
| **`tab_ChargingPlace` 已不再被使用**（只在 m_addChargingPosition / m_DeleteChargingPosition / m_getMinMaxCoordinate 三处出现） | 死代码 | 验证后可清 |
| **`m_ifvoidinlist` 在 `m_addRack` 末尾反复清理** void | 有 bug 风险（list 有 void 说明 duplicate 失败） | 看 duplicate 路径 |
| **`m_createCTURack` 邻接判定对边界处理不完整**（角落场景只测了 2 void） | 鲁棒性 | 加单元测试 Frame `test` |
| **`m_calculatePro` 的 `timewindow` 全局变量未声明**（直接除） | 编译时会失败（实测未看到失败因为有运行时分支） | 改成 `current.~.timewindow` 或 Frame attr |

## 十、复用这套设计的步骤（template）

要在你的新模型里"抄作业"：

1. **建类库文件夹**：`.MyModel`（Folder）
2. **BasicObjects 副本**：把需要的 .MaterialFlow.* / .Resources.* / .InformationFlow.* 拖进来
3. **Hardware 类**：在 `.MyModel.Hardware.*` 定义物理设备类（含 `_3d.dimensions` 等几何参数）
4. **Software 类**：在 `.MyModel.Software.*` 定义控制中枢（RCS 风格的 DataTable + executer）
5. **Hook 方法**：每个 Hardware 类挂 `m_Oncreate/m_OnMove/m_OnDelete` 自动注册
6. **模板 Frame**：`.MyModel.template_v1`（Frame 类）把 Hardware + Software + BasicObjects 包起来
7. **用户使用**：新模型只要 `duplicate(.MyModel.template_v1, .Models.Model)` 就有完整功能

> 关键纪律：**一切状态在 DataTable、一切触发走 triggerpoint、一切事件走 OnCreate/OnDelete/OnMove**。
---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: 立体仓库(CTU + AGV)调度的核心模式:RCS 控制中枢 / DataTable 状态机 / 三级执行器 / 触发点防重入
---

# 立体仓库与 CTU 调度模式

本文档基于 P4_CTU 模型(86 个 Method dump 后)提炼出 **立体仓库(CTU + AGV)调度**的可复用模式。

## 一、业务背景

CTU(Compact Tower Unit,堆垛机/立库提升机)+ AGV(自动导引车)混合调度的自动化立体仓库。

```
入库:Source → AGV → 接驳点(rack1/rack2 第一层)→ CTU → 货架 bin
出库:货架 bin → CTU → 接驳点 → AGV → Drain
```

## 二、RCS 控制中枢

### 2.1 一切状态在 DataTable 里

RCS 内部用 11+ 个 DataTable 承担所有可变状态,**没有散落在 object attribute 上的可变状态**。这让 RCS 完全可以"重启+数据驱动"——清空 DataTable 就等于冷启动。

| DataTable | 作用 |
|---|---|
| `tab_taskPool` | 全局任务池(In/Out 订单) |
| `tab_taskPoolDatabase` | 已完成任务归档 |
| `tab_TransportationTask_AGV` | AGV 运输任务队列 |
| `tab_TransportationTask_CTU` | CTU 运输任务队列(含 BinID/RackMarker/CTUMarker) |
| `Tab_binState` | 每个 bin 一行(BinID/Rack/Content/Binstate/NumMU) |
| `Tab_MU_info` | MU → bin 映射 |
| `Tab_RackMarker` | 货架第一层接驳点 |
| `Tab_HomeState` | AGV/CTU home 点位 |
| `Tab_ChargingPlace` | 充电桩点位 |
| `tab_agv_state` | 每台车一行(Vehicle/State ∈ {Idle, Running, Charging}) |
| `InitFinished` | boolean,"初始化完成"标志,下游用 `waituntil RCS.InitFinished` 同步 |

### 2.2 三级执行器架构

```
              m_StockIn() / m_StockOut()           ← 用户入口
                       ↓ appendrow
                 tab_taskPool
                       ↓ append + triggerpoint
                  m_TaskExcuter                     ← L1: 订单分发(while + sort + 多 case)
                  ├─ In  → m_CreateTransTask_AGV_In + m_CreateTransportationTask_CTU_In
                  └─ Out → m_CreateTransportationTask_CTU_Out + m_CreateTransTask_AGV_Out
                       ↓ append
        tab_TransportationTask_AGV + tab_TransportationTask_CTU
                       ↓ triggerpoint
       m_AGVExcuter              m_CTUExcuter       ← L2: 设备级调度
       ├─ findFreeAGV            ├─ findFreeCTU
       ├─ agvGetTask             ├─ 选最近任务
       └─ executeNewCallChain    └─ executeNewCallChain
                       ↓
        AGV/CTU m_executeTransportationOrder      ← L3: 设备内部执行
```

## 三、触发点防重入模式

任何"长跑 worker"(仿真心跳 / 日志写盘 / 状态广播)都用这套三件套。

```simtalk
-- m_TaskExcuter_triggerpoint
if TaskExcuter_Running then
    m_logger("INFO","Excuter已触发,无需重复触发")
    return
end
TaskExcuter_Running := true
m_logger("INFO","Excuter未触发,触发")
&m_TaskExcuter.executeNewCallChain    -- 异步执行,当前方法立即返回
```

### 为什么用 `executeNewCallChain` 而非直接调用?

- 直接调用会**阻塞当前方法**直到 executor 跑完(executor 是 while 死循环)
- `executeNewCallchain` 把任务扔到**新的 call chain**上异步执行,当前方法立即返回
- 配合 `_Running` 标志位,确保**全模型只有一个 executor 实例**在跑

## 四、bin 分配算法

```simtalk
Tab_binState.sort("NumMU","up")       -- 1) 按当前 MU 数升序排
if tab_binstate.find(0)               -- 3) 找一个空 bin
    bin := Tab_binState["BinID",tab_binstate.cursory]
    Tab_binState["Binstate",tab_binstate.cursory] := "Occupied"
    Tab_MU_info.appendrow(mu,bin,"DE","OnTranportation")
    return bin
else                                  -- 4) 没有空 bin → 找一个只放了 1 个的
    if tab_binstate.find(1)
        ...
    else
        return ""                    -- 上游用 continue 跳过
    end
end
```

**模式**:
- 两层深度(DE + EX):每个 bin 可放 2 件 MU,状态字段用 NumMU(0/1/2)
- 优先填 NumMU=0 的 bin——减少"半空 bin"
- 找不到 bin 就返回空串——上游 `if bin = "" then continue end` 跳过

## 五、自动注册 / 生命周期 hook 模式

每个会"出现在场景里"的对象都挂这三个方法:

```simtalk
-- MapGenerator.Home.m_Oncreate
if not (current.~.extendPath("RCS") = void)
    RCS := current.~.extendPath("RCS")
    RCS.m_addHomePosition(current)
else
    print "ERROR: Please Insert RCS First"     -- 不要用 messagebox() 模态!
end

-- m_ondelete
if RCS = void then return end
RCS.m_DeleteHomePosition(current)

-- m_OnMove (param old, new : length[3])
if RCS = void then return end
RCS.m_getMinMaxCoordinate
```

**注册/反注册对称**——OnCreate 注册到 RCS、OnDelete 反注册、OnMove 触发包围盒重算。

⚠️ **反面警示**:模型里有用 `messagebox("...")` 的——会卡死 GUI / socket,**必须改用 `print` 或 `infoBox(text, false)`**。

## 六、变量命名约定(P4_CTU 沉淀)

| 前缀 | 含义 | 示例 |
|---|---|---|
| `m_` | Method(私有) | `m_init`, `m_logger`, `m_findFreeAGV` |
| `m_Onxxx` | 生命周期 hook(但模型自身混用大小写) | `m_Oncreate`, `m_OnMove`, `m_OnDelete` |
| `m_xxx_triggerpoint` | 防重入触发点 | `m_TaskExcuter_triggerpoint` |
| `v_` | Variable | `v_x`, `v_y`, `bin_w`, `RCS` |
| `l_` | length 数值 | `l_groundclearance`, `l_gap` |
| `b_` | boolean | `b_needcharging`, `backhome` |
| `tab_` / `Tab_` | DataTable | `tab_taskPool`, `Tab_binState` |
| `cur*` | 局部临时 | `cur_x`, `curtime` |
| `obj_*` | 通用 object 引用 | `obj_type` |

> Plant Simulation 大小写不敏感但展示是大小写敏感——用前缀区分意图,可读性高 10 倍。
>
> ⚠️ **真实踩坑**:模型内部**混用大小写**(`m_Oncreate` / `m_ondelete` / `m_oncreate` / `m_OnDelete` / `m_onChange` 至少 5 种写法并存)。下游 agent 复用时**永远用精确路径 grep**,别靠"看上去一样的命名"匹配。

## 七、MapGenerator 动态生成地图

```
m_UpdateMap (总入口)
  ├─ m_creategrid             ← 按 RCS.min_x/max_x/y 划分网格
  ├─ m_UpdateRack_Map         ← 在每个 Rack 第一层创建 RackMarker + AGVOnlyMarker
  ├─ m_createCTURack          ← 在合适网格上创建 CTURackMarker
  ├─ m_createSpecPosition     ← 在 Home/Charging 位置覆盖 Marker
  ├─ m_UpdateActiveMap        ← 其余空网格填充 ActiveMarker
  └─ m_createConnector        ← 相邻 Marker 间建 Connector
```

### 7.1 网格生成算法

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
    end
    cur_y := RCS.min_y
    cur_x += bin_x
end
```

### 7.2 关键 trick — `obj._3d.*` API

```simtalk
coordinate := rack._3d.getworldcoordinate            -- 中心世界坐标
max_c := coordinate + rack._3d.boundingboxmax        -- 最大角
min_c := coordinate + rack._3d.boundingboxmin        -- 最小角
rack._3d.position := [...]                           -- 直接挪对象
rack._3d.dimensions                                 -- [width, length, height]
rack._3d.gap                                        -- 3  D 间距
```

> ⚠️ `_3d` 是 Plant Simulation 私有 API,旧版本字段名可能不同。

## 八、不建议照搬的反模式

| 反模式 | 后果 | 改进建议 |
|---|---|---|
| `messagebox(...)` 在 OnCreate 里 | 卡死 GUI / socket 阻塞 | 用 `infoBox(text, false)` 或 `print` |
| `debug` 关键字当 TODO 占位 | case 分支未实现 | 改成显式 `return false` + log |
| 命名大小写混乱 | 难 grep | 统一一套前缀 |
| `wait 60` / `wait 15` 硬编码 | 调参要改源码 | 提到 Frame attribute 可配置 |
| 冗余字段 `backhome` 在多个 object 各自维护 | 状态分裂 | RCS 集中维护 |
| `m_findFreeAGV` / `m_findFreeCTU` 几乎重复代码 | 一改两处 | 用参数化扫描代替 |

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->
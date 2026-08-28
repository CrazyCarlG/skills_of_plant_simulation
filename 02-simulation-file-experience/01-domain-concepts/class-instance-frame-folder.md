---
last_updated: 2026-08-28
contributors: [@z004bjuu]
scope: 写 / 读任何 Plant Simulation 对象前必读；Class vs Instance / Frame vs Folder 三元组判定法（`Origin`/`Class`/`OriginRoot`）
---

# Plant Simulation 概念梳理 — Class vs Instance、Frame vs Folder

> **来源**：2026-08-26 在 `local-simtalk-class-management` 技能调试过程中实际撞坑后整理。
> 与 `02-bridge-tool/simtalkclaude-v1-and-v2.md` 互补 — 那篇是 SimtalkClaude bridge 的内部实现经验，本篇是 Plant Simulation **领域概念**的实测总结。
>
> 所有"实测"数据均由 `simtalk_send.py run + readlog` 探针在 Plant Simulation 2606.0002 服务（`host.docker.internal:50007`）上跑出，可逐条复现。

---

## 一、四个核心对象概念

Plant Simulation 里一切"对象"按用途分四类，理解它们是后续 `derive`/`duplicate`/`create` 等所有操作的前提：

| 概念 | 英文 | 是什么 | 在哪 |
|---|---|---|---|
| **类（类库里的定义）** | Class | 模板 / 图纸 | **Folder**（类库文件夹）里 |
| **实例** | Instance | 真正能跑的对象 | **Frame**（运行视图）里 |
| **类库文件夹** | Folder | 装类定义的容器 | 类库根 `.` 的子节点 |
| **运行框架** | Frame | 装实例 + 跑仿真 | 顶层 `.Models.<ModelName>` |

> **最容易踩的坑**：把 Frame 当成 Folder，或反之。两者都是 "Container" 类型，看着像，实际天差地别。

---

## 二、Class vs Instance

### 2.1 定义

- **Class（类）** — 一份"图纸"。定义了对象有什么属性、能调什么方法。存在类库里供所有模型复用。
  - 例：`.MaterialFlow.Station` —— 这是 **Station 类**，所有 Station 实例的模板。
- **Instance（实例）** — 真正占用内存、能被仿真调度、能接收 MU（物料） 的对象。是从类"实例化"得到的。
  - 例：`.Models.Model.MyStation` —— 这是 **Station 的一个实例**，放在 Frame 里供仿真使用。

### 2.2 怎么判断一个 path 是类还是实例？—— **Origin / Class / OriginRoot 三件套**

这是唯一可靠的方法。`NumChildren`、`InternalClassType`、名字 —— 都不靠谱。

| 属性 | 类（Class） | 实例（Instance） | 根类（built-in） |
|---|---|---|---|
| `Origin` | `VOID` | 源类 | `VOID` |
| `Class` | `VOID` | 源类 | `VOID` |
| `OriginRoot` | 类自己的路径 | 源类的 OriginRoot | 类自己的路径 |

**判读规则**：

```
Origin == VOID  AND  Class == VOID        →  类
Origin != VOID  AND  Class != VOID        →  实例
```

### 2.3 实测证据（Aug 2026）

```text
SOURCE: .MaterialFlow.Station  (built-in root class)
        Origin=VOID, Class=VOID, OriginRoot=.MaterialFlow.Station

METHOD                  DESTINATION        RESULT                          ORIGIN                       CLASS
─────────────────────────────────────────────────────────────────────────────────────────────────────────────
duplicate(.Models, X)   Folder             .Models.X                       VOID                         VOID           ← 类
duplicate(.Models.M, X) Frame              .Models.M.X                     .MaterialFlow.Station        .MaterialFlow.Station   ← 实例
derive(.Models, X)      Folder             .Models.X                       .MaterialFlow.Station        VOID           ← 子类
derive(.Models.M, X)    Frame              .Models.M.X                     .MaterialFlow.Station        .MaterialFlow.Station   ← 实例
```

规律：
- **`duplicate` 到 Folder → 类**（独立副本，无父类）
- **`duplicate` 到 Frame  → 实例**（保留继承）
- **`derive` 到 Folder → 子类**（保留继承，可覆盖父属性）
- **`derive` 到 Frame  → 实例**（与 duplicate 同效；不常见）

---

## 三、Frame vs Folder

### 3.1 定义

- **Folder（类库文件夹）** — 类库（Class Library）里的**容器**。它的孩子是**类定义**。
  - 例：`.MaterialFlow`（Folder）下挂着 `Station`、`Conveyor`、`Source` 等类。
  - `InternalClassType = "Folder"`
- **Frame（运行框架）** — 仿真运行时的**容器**。它的孩子是**实例**（material-flow 对象、Container、Worker 等）。
  - 例：`.Models.Model`（Frame）下挂着仿真里所有的 Station、Source、Drain 实例。
  - `InternalClassType = "Frame"`

### 3.2 视觉/操作差异

| 操作 | Folder | Frame |
|---|---|---|
| 在 GUI 拖入子项 | 从 Class Library 拖入一个**类** | 从 toolbox 拖入一个**对象图标**（创建实例） |
| 子项能做什么 | 不能跑仿真，只能被引用为类 | 能跑仿真、能被 MU 通过、能 `setPosition` |
| `NumChildren` 含义 | 类库子项数 | **结构**子节点数（**不含** 2D 视图里的实例） |

### 3.3 双重身份 —— Frame 也能"装类"

**这是最反直觉的点**：

```text
.Models              ← 是 Folder（顶层类库文件夹）
.Models.Model        ← 是 Frame（仿真模型框架）
```

但当你执行 `.MaterialFlow.Station.duplicate(.Models.Model, "MyStation")` 时，Plant Simulation 把 `.Models.Model` **当作 Folder 用**——因为 `duplicate` 的语义是"在某个类库位置登记一个新类"。

也就是说：

> **同一个对象（这里是 `.Models.Model`），在不同 API 下扮演不同角色：**
> - 作为 Frame（GUI 拖入对象、仿真的根）—— **Frame**
> - 作为 `duplicate` 的目标 —— **当作 Folder 看待**（输出是类）

这就是为什么 `duplicate(.Models.Model, X)` 给出 **Origin=VOID/Class=VOID**（类特征），而不是 **Origin=源/Class=源**（实例特征）。

但 **`.Models.Model.InstStation` 又确实是 Frame 里的实例** —— 这两个结论不矛盾，因为：
- 它在 **类库路径** 上登记成了 `.Models.Model.InstStation`（被 duplicate 当 Folder 处理）
- 它 **同时** 也是 Frame 里可被 `setPosition`、可被 `extendPath` 找到的实例

Plant Simulation 把"类库路径"和"运行时路径"**统一**用点路径表达，二者在多数情况下重合，但 `.Models.Model` 这个特殊节点同时承担两个角色。

### 3.4 怎么判断一个节点是 Frame 还是 Folder？

```simtalk
var p: object := str_to_obj(".Models.Model")
print p.InternalClassType
-- → "Frame"
```

`InternalClassType` 返回 `"Folder"`、`"Frame"`、`"Table"`、`"Station"` 等。这是判断节点类型的**最直接**方法。

但要注意：`InternalClassType` 不区分"类"和"实例"——一个类 `.MaterialFlow.Station` 和一个实例 `.Models.Model.MyStation` 都是 `"Station"`。

---

## 四、Class/Instance 与 Frame/Folder 的关系图

```
┌─────────────────────────────────────────────────────────────┐
│  Class Library                                              │
│  ┌──────────────┐    duplicate →  ┌───────────────────┐    │
│  │ Folder       │ ───────────────→│ Class (新类)       │    │
│  │ .Models      │                 │ Origin=VOID        │    │
│  │              │                 │ Class=VOID         │    │
│  └──────────────┘                 └───────────────────┘    │
│  ┌──────────────┐    duplicate →  ┌───────────────────┐    │
│  │ Folder       │ ───────────────→│ Class (新类)       │    │
│  │ .MaterialFlow│                 │ Origin=源          │    │
│  │              │                 │ Class=VOID         │    │
│  └──────────────┘                 └───────────────────┘    │
│                                                             │
│  ┌──────────────┐    duplicate →  ┌───────────────────┐    │
│  │ Frame        │ ───────────────→│ Instance          │    │
│  │ .Models.Model│                 │ Origin=源          │    │
│  │              │                 │ Class=源           │    │
│  └──────────────┘                 │ 可 setPosition     │    │
│                                   │ 可被 MU 通过       │    │
│                                   └───────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

要点：**`duplicate` 的产物形态由目标节点的角色（Folder 还是 Frame）决定，不是由"目标节点在不在 .Models"决定。**

---

## 五、常见混淆与"应该用哪个 API"

| 想做的事 | 错的方式 | 对的方式 |
|---|---|---|
| 在类库里新增一个 Station 子类 | `duplicate(.Models, "MyStation")` → 得到无父类的独立副本 | `derive(.Models, "MyStation")` → 得到继承自源类的子类 |
| 把 Station 放进 Frame 当实例用 | `cls.create(frame)` → `Unknown identifier 'create'`（Station 不是 MU） | `duplicate(frame, "Inst")` → 得到真正的实例 |
| 判断节点是不是 Frame | `path.NumChildren > 0` | `path.InternalClassType = "Frame"` |
| Frame 里有没有 MyInst 这个实例 | `Frame.NumChildren` 计数 | `Frame.extendPath("MyInst") /= void` |
| 设置实例位置 | `<obj>.setPosition := [100, 100]` → 编译错 | `<obj>.setPosition(100, 100)` → 方法调用 |

---

## 六、Plant Simulation 术语与面向对象的对应

| Plant Simulation | 面向对象类比 | 备注 |
|---|---|---|
| Class Library | 包/命名空间 | 装类的容器 |
| Folder | 包文件夹 | 可嵌套 |
| Frame | 应用/场景 | 装运行时实例 |
| Class | 类 | 模板 |
| Instance | 对象 | 运行时实体 |
| `<class>.duplicate(<folder>, name)` | 定义一个新类（脱离源） | 与 `derive` 区别：切断继承 |
| `<class>.derive(<folder>, name)` | 定义一个子类 | 保留继承 |
| `<class>.duplicate(<frame>, name)` | 实例化一个对象 | 仿真里能跑 |
| `<class>.create(<frame>)` | (MU only) 实例化的另一种形式 | 只对 MU / Worker / DataTable 有效 |

---

## 七、延伸阅读

- `local-simtalk-class-management/log/derive-vs-duplicate.md` — `derive` 与 `duplicate` 的纯 API 参考手册（含决策矩阵、验证矩阵、常见坑清单）。
- `local-simtalk-class-management/log/session-20260826.md` Part E、F — 本次实测的完整 probe 记录（含服务器实际返回）。
- `01-plantsimulation-knowledge/01-plant-simulation-help/objects/common-methods/common-methods.md`
  - line 129: `derive` 定义
  - line 153: `duplicate` 定义
  - line 411: `setPosition` 定义
  - line 415: `setPosition` 正确签名（方法调用）
- `01-plantsimulation-knowledge/01-plant-simulation-help/objects/common-read-only-attributes/`
  — `Origin` / `Class` / `OriginRoot` / `InternalClassType` / `NumChildren` 的权威定义。

---

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾，**不要修改主体**。
> 贡献流程、entry 字段格式、Supersede 模式见 [`CONTRIBUTING.md`](../../CONTRIBUTING.md)。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->
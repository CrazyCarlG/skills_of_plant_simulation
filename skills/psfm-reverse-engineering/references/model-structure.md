# 提取模型结构

分析用户提供的 PSFM 模型文件，输出其【模型结构】，严格按以下五部分返回：

## 一、Frame 层级树

- 用缩进树形图展示整个模型的 Frame 嵌套关系，从根 Frame 到每个子 Frame。
- 每个 Frame 标注：名称、是否带图标/继承（isClass 或 isInstance，若文件中能识别）、包含的对象数量。

## 二、对象清单表

- 用 Markdown 表格列出模型中的每一个对象，列包含：

| 所属Frame | 对象名称 | 对象类型(英文) | 所属大类(MaterialFlow/Resource/InformationFlow/Fluid/UI) | 关键属性(名称=值) |

- 对象类型必须对照知识库 `01-plantsimulation-knowledge/01-plant-simulation-help/objects/` 目录下的标准命名，不要臆造类型。

## 三、类结构与继承关系

- 类继承树（父类 → 子类，标注 isClass / isInstance / isDerivedFrom）。
- 实例对象 → 对应类的映射表。
- 逐类说明继承/引用/属性绑定关系。
- 标准类库来源与自定义类命名约定。
- 详见 `references/class-hierarchy.md` 的详细字段。

## 四、物料流拓扑（物流路径）

- 用有向图描述对象之间的连接关系（Connector 连线、Importer/Exporter 绑定、Source 的后继对象等）。
- 用箭头表示流向，例如：`Source → Buffer → Station → Drain`。
- 对于含循环、回流、并行的路径，请单独注明（如 Cycle 循环、FlowControl 分流/合流）。

## 五、控制与数据流关系

- 列出哪些对象挂载了控制（Entrance/Exit Control、Trigger 的 Interval/Duration Control、Observer/Sensor）。
- 列出哪些 Method 被哪些对象调用（调用方 → 被调 Method）。
- 列出数据表/变量与对象之间的读写关系。

如果某部分在文件中没有信息，请明确写「文件中未体现」，不要编造。

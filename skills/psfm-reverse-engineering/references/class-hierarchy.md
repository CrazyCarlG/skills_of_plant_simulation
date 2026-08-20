# 提取类结构与继承关系

从 PSFM 模型文件中提取【类结构与继承关系】，严格按以下四部分输出：

## 一、类继承树（父类 → 子类）

- 用缩进树形图展示所有自定义类（用户定义的 Frame 类）之间的继承（派生）关系。
- 格式示例：

```text
Model (根Frame)
└── MyMachine (自定义类，isClass=true)
     └── MyDrillingMachine (派生类，Derived from MyMachine)
```

- 每个类标注：类名、是否 isClass、是否 isInstance、是否 isDerivedFrom（若文件可识别）、Derived from 的父类名。

## 二、类与实例（对象）的实例化关系

- 用表格列出「哪个实例对象属于哪个类」：

| 实例对象名 | 所属Frame | 对应类(Class) | 是否继承自父类 | 实例化位置 |

- 区分两种对象：直接从类库拖入的标准对象实例（如 Source、Station）vs. 自定义类的实例。

## 三、类关系（继承/引用/委托/属性绑定）

- 逐类说明它与其它类/对象的关系，分类标注：
  - 继承（Inheritance）：子类继承父类，标注 override 的属性/方法（若文件能体现）。
  - 引用/挂载（Reference/Containment）：类内部包含哪些子对象、Method、变量、表格。
  - 属性继承（Inherit from）：对象的属性是否勾选 Inherit（从类继承）还是被覆盖。
  - 委托/回调：Method 调用其它类的 Method、Exporter/Importer 跨 Frame 连接。

## 四、类库来源与命名约定

- 说明使用了哪些标准类库对象（Basic Objects 的 MaterialFlow/Resource/InformationFlow/Fluid/UI）。
- 说明自定义类的命名前缀/约定（如 `.Models.`、`.MUs.`、`.Tools.`、UserObjects 等路径）。
- 若存在类库文件（如 Toolbox、Class Library 引用）请指出其名称。

约束：父类/子类、isClass/isInstance/isDerivedFrom、Inherit 等术语必须与 Plant Simulation 官方一致。文件中无法判定的关系写「未体现」，不要臆造。

# Plant Simulation Help — Knowledge Base Index

按主题快速定位 `01-plantsimulation-knowledge/
01-plant-simulation-help/` 下的对应文档。本 skill 写代码时随时查。

## 必读（每次写代码前）

| 主题 | 路径 |
|---|---|
| SimTalk 2.0 语法总览 | `objects/simtalk/` |
| Method 对象总览 | `objects/information-flow-objects/Method/general/` |
| Method 程序结构 | `programming-a-method/` |
| 所有对象共有的方法 | `objects/common-methods/common-methods.md` |
| 所有对象共有的属性 | `objects/common-methods/common-attributes.md` |
| 所有对象共有的只读属性 | `objects/common-methods/common-read-only-attributes.md` |

## Method 对象专属

| 主题 | 路径 |
|---|---|
| Method 的方法（`execute` / `executeIn` / `encrypt` / `decrypt` / `load` 等） | `objects/information-flow-objects/Method/methods/` |
| Method 的属性（`Program` / `RandomSeed` / `UsingNewSyntax` / `PythonModule`） | `objects/information-flow-objects/Method/attributes/` |
| Method 的只读属性（`NumInExecution`） | `objects/information-flow-objects/Method/read-only-attributes/` |
| Method 编辑器 | `objects/information-flow-objects/Method/editor/` |
| Method 调试器 | `objects/information-flow-objects/Method/debugger/` |

## 信息流对象（Information Flow）

| 主题 | 路径 |
|---|---|
| Method（方法） | `objects/information-flow-objects/Method/` |
| Variable（变量） | `objects/information-flow-objects/Variable/` |
| Generator / Trigger / DataList / DataStack / DataQueue / DataTable | `objects/information-flow-objects/` |

## 物料流对象（Material Flow）

| 主题 | 路径 |
|---|---|
| Frame / Container / Station / Conveyor / Source / Drain | `objects/material-flow-objects/` |

## 资源管理

| 主题 | 路径 |
|---|---|
| WorkerPool / Broker / ShiftCalendar | `objects/resource-management/` |

## 编程语言

| 主题 | 路径 |
|---|---|
| SimTalk 1.0 vs 2.0 | `programming-a-method/simtalk-syntax-versions.md` |
| SimTalk 字符串 / 数字 / 时间 | `programming-a-method/data-types/` |
| SimTalk 关键字 / 控制流 | `programming-a-method/control-flow/` |
| SimTalk 内置函数 | `programming-a-method/built-in-functions/` |
| PythonModule（Plant Simulation 内嵌 Python） | `objects/information-flow-objects/Method/attributes/python-module.md` |

## 仿真控制

| 主题 | 路径 |
|---|---|
| EventController（事件控制器） | `objects/event-controller/` |
| 控件（Controls）：Entrance / Exit / Draining | `controls/` |
| 触发器（Trigger） | `objects/information-flow-objects/Trigger/` |

## 完整索引

最权威的入口：`01-plantsimulation-knowledge/
01-plant-simulation-help/objects/` 下的目录树。读不清楚时用本地 `find` 或
`grep -r "your_keyword" 01-plantsimulation-knowledge/`。
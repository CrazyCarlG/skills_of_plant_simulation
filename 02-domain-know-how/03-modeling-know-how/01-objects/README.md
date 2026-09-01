---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: Plant Simulation 对象概念(Class / Instance / Frame / Folder)+ 判定方法
---

# 03-modeling-know-how/01-objects — 对象概念

本目录整合 **Plant Simulation 对象概念**:四个核心类型(Class / Instance / Frame / Folder)+ 可靠的判定方法。

## 文件索引

| 文件 | 内容主题 |
|---|---|
| [`object-classification.md`](./object-classification.md) | **四对象概念详解**:Class vs Instance / Frame vs Folder + Origin/Class/OriginRoot 判定矩阵 + Frame 双重身份分析 |

## 何时必须读本目录

- **写 / 读任何 Plant Simulation 对象前必读** —— 后续所有 `derive`/`duplicate`/`create` 等操作的前提
- **判断一个 path 是类还是实例** —— 用 `Origin == VOID AND Class == VOID` 判定
- **判断一个节点是 Frame 还是 Folder** —— `InternalClassType = "Frame"` vs `"Folder"`
- **理解 Frame 的双重身份** —— `.Models.Model` 既是 Frame(运行视图)又是 Folder 角色(duplicate 的目标)

## 核心判定规则速查

```
Origin == VOID  AND  Class == VOID   →  类 (Class)
Origin != VOID  AND  Class != VOID   →  实例 (Instance)

InternalClassType = "Frame"  →  Frame (运行框架)
InternalClassType = "Folder" →  Folder (类库文件夹)
```

## duplicate vs derive 行为矩阵

| 操作 | 目标 | 结果形态 |
|---|---|---|
| `duplicate(<Folder>, X)` | Folder | **类**(Origin=VOID, Class=VOID)|
| `duplicate(<Frame>, X)`  | Frame  | **实例**(Origin=源, Class=源)|
| `derive(<Folder>, X)`    | Folder | **子类**(保留继承,可覆盖)|
| `derive(<Frame>, X)`     | Frame  | **实例**(与 duplicate 同效)|

## 重构元数据

- 重构日期:2026-09-01
- 重构来源:`02-simulation-file-experience/01-domain-concepts/class-instance-frame-folder.md` + `class-instance-frame-folder-concepts.md`
- 重构策略:从两份近似文档(早期版 + 正式版)合成 1 篇统一参考文档,保留所有关键判定规则与实测证据
</content>
</invoke>
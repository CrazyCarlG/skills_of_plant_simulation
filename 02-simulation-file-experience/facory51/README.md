# facory51 — Factory51 + SimtalkClaude 集成经验

> 在 Siemens 官方 **Factory51** 示例模型（`02-offcial-psfm-model/Factory51/Factory51.psfm`）
> 之上导入 **SimtalkClaude**（TCP 远程驱动桥）后的整理与经验沉淀。
> 目录名 `facory51` 沿用用户拼写，**故意不更名**，避免破坏已存在的引用。

| 文件 | 作用 |
|---|---|
| `README.md` | 本索引 |
| `factory51-simtalkclaude-integration.md` | 主报告：Factory51 自身结构 + SimtalkClaude v2 导入后新增/修改的模式 |
| `simtalkclaude-v2-vs-v1.md` | SimtalkClaude v2 相对 v1 的关键差异（鉴权、双协议、状态机） |
| `code_log/` | 与本目录相关的代码备份占位（生产环境用 `local-simtalk-read-library` 重新 dump） |

## 顶层结论

1. **Factory51 自身是干净的标准建模示例**——结构遵循 Plant Simulation
   "Class Library + Models" 二分法（`UserObjects/**` 是类定义，`Models/Factory51/**` 是实例），
   1592 个对象、纯离散事件生产+仓储系统（卡车入库 → HBW 高架库 → P1/P2 双线生产 → 立体库出货）。
2. **SimtalkClaude v2 比 v1（已记录在 `simtalkclaude-best-practices.md`）多了三个真正有价值的模式**：
   - 鉴权握手（`m_sendauth` / `m_authback`）
   - 双协议分帧（`m_str_send` 旧 vs `m_send` 新）
   - 服务端回调路由（`socketcallback` 的 case 分支）
3. **导入路径与隔离策略**清晰：`.SimtalkClaude2` 始终作为独立的 Class Library 挂在根 Frame
   之外，与 Factory51 业务对象（P1/P2/Warehouse/WMS）**零耦合**——只通过 TCP
   与外部 agent 通信，不会污染 Factory51 的运行语义。

## 关键交叉引用

- `02-simulation-file-experience/simtalkclaude-best-practices.md` —— SimtalkClaude v1 的基线经验
- `02-simulation-file-experience/skill-call-playbook.md` —— 9 个 skill 的使用 playbook
- `02-simulation-file-experience/ctu-warehouse/p4-ctu-class-inheritance.md` —— 另一份"反向验证类定义存在性"的实例参考
- `01-plantsimulation-knowledge/02-offcial-psfm-model/Factory51/model-know-how/Factory51-模型结构.md` —— Factory51 模型的结构笔记（已有）

## 重要数据来源

- `skills/local-simtalk-read-library/data/simtalkclaude_dump.json` —— SimtalkClaude v1 的全量 dump
- `skills/local-simtalk-add-note-to-method/code_log/SimtalkClaude2_*_program_original.txt` —— SimtalkClaude v2 的 22 个 method 备份
- `skills/local-simtalk-add-note-to-method/log/2026-08-26_simtalkclaude2_*.md` —— v2 加注释的过程日志
- `01-plantsimulation-knowledge/02-offcial-psfm-model/Factory51/` —— Factory51 模型 bundle

> **环境注记**：本次分析时 Plant Simulation **未运行**（TCP 端口 50001/50007 无监听），
> 故所有发现都基于磁盘上的 `.psfm` bundle + `code_log/` 备份 + 已有文档。
> 后续若需验证 v2 是否仍存在于用户当前加载的模型里，需先启动 Plant Simulation
> 并 `local-simtalk-get-folder-tree . 5` 重新 dump 一次。
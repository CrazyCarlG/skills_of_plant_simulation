# plant-simulation-modeling-architect — Memory Index

本目录存放 **`plant-simulation-modeling-architect` agent** 的会话记录——每个 session 一份"架构推荐方案"文档(`YYYY-MM-DD_architecture-recommendation_<topic>.md`,严格 9 段模板,≤300 行)。

## 索引 / Index

| Date | Topic | Scenario | Target need | Key recommendation |
|---|---|---|---|---|
| _empty — awaiting first session_ | — | — | — | — |

## 何时写新行

每完成一次架构推荐 session → 在上表 **newest at top** append 一行,同时 bump 下方 `last_updated`。详见 `agents/plant-simulation-modeling-architect.md` Step 5 / Step 6。

## 与 peer agent memory 的关系

- **本目录仅由 `plant-simulation-modeling-architect` 写**;
- 本 agent **不**读 `expert-memory/` / `curator-memory/` / `student-memory/` / `synthesizer-memory/` 的会话记录(那些是它们的执行流水账,不是 KB 主源);
- 本 agent **主输入**是 `01-plantsimulation-knowledge/`(官方 KB)+ `02-offcial-psfm-model/`(Factory51 / Small Parts Production 逆向分析)+ `02-domain-know-how/`(已沉淀主题)。

## 文件命名约定

- Session:`YYYY-MM-DD_architecture-recommendation_<topic>.md`
- `<topic>` = kebab-case 短语(如 `factory51-clone-proposal`、`agv-dispatch-architecture`、`pallet-routing-class-design`)
- 单文件 ≤300 行,超出立即拆 `<topic>-part1.md` / `<topic>-part2.md`

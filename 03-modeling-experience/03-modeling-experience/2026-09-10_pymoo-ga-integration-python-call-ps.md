---
last_updated: 2026-09-10
dimension: 03-modeling-experience
source_sessions:
  - 04-agent-memory/student-memory/2026-09-07-Python_GA_Demo-jobsshop-ga-integration.md
models_touched: [Python_GA_Demo]
---

# Python_GA_Demo — Pymoo 多目标 GA 集成 Plant Simulation 范式

## 症状
- 教学模型 `.Models.Example`(含 `.Models.Example.GA` 优化 Frame)是 Siemens 官方 Demo:`Python_GA_Demo.spp`。
- 集成方式 = Python(pymoo)调用 Plant Simulation(headless `PlantSimulationConsole.exe`),**不是** in-process。
- `01-plantsimulation-knowledge/` 无 Python integration baseline — Siemens 官方 demo 但未文档化。

## 根因 / 完整集成模式
**Subprocess 启动**:
```
subprocess.run([PlantSimulationConsole.exe, "/f", model, "/m", frame, "/e", simtalk, "/EnablePrint", "/hideBBL"])
```

**SimHandler 集成流程**(Python 侧):
1. **Parameterize** — Input DataTable 列:buffer 容量范围 / sequence 顺序;RunButton 触发 / DropDownList 选 Solution
2. **Start** — Button.OnClicked 调 `current.Optimizer`(PythonModule);Optimizer 读 Input → 定义 individual → `current.FitnessEvaluator.evaluate()` → 启动子进程 `current.SimHandler.runSim(t_idx)` → `PlantSimulationConsole.exe /e simtalk{t_idx}.txt`
3. **Loop** — 每代:selection / CostumCrossover / CostumMutation → CostumSampling → 新种群
4. **End** — Pareto 前沿写入 HTMLHandler → HtmlReport.Content;Solution 写入 DropDownList.Items;用户从 DDL 选 → SolutionHandler 写回模型

**SimTemplate vs Python `.format`**:
- `current.SimTemplate.Program.replace("---","")` 拼装模板后写入 `simtalk{t_idx}.txt` 再用 `/e` 喂给 console
- `writeSimTalkFile` 用 `template.format_map(ser)` — SimTemplate 是 Python `.format` 模板(`{placeholder}`),不是 SimTalk method

**读结果**:
- `consproc.stdout` → `string_to_dict` → `ast.literal_eval(versionDict['Print']['Throughputs'])` — PlantSimulationConsole 通过 `print` 吐 `key:value` 行

## Workaround / 结论
- **Mask pattern**(heterogeneous decision vars):`mask = ["buffer", "buffer", ..., "sequence", "sequence", ...]`,把 buffer 容量(连续 int)和 sequence 顺序(排列)分别编码成不同算子;`getNextBufferIndex` 递归找下一个 buffer 变量边界。这是 GA 处理 mixed-variable 的标准做法,pymoo 用 `MixedVariableProblem`。
- **Class name typos 沿用**:`CostumCrossover` / `CostumMutation` / `CostumSampling` 三连 typo(`Costum` 应为 `Custom`)。是 user 手误还是约定?待考。
- **Comment2.ReadMe 是"embedded documentation"**:用 RTF 富文本(`\urtf1\ansi...`)承载 model motivation/architecture 说明 — 比 Markdown 更原生(PS Comment 直接渲染),但不可 grep。
- **`current.X.value` / `current.X[row,col]`** — Python 侧访问 PS 对象,使用 Python-side API(`current.HtmlReport.Content` 是 string 属性;`current.X[row,col]` 是 table 索引)— 这是 PS 2606 新增的 Python integration 能力。
- **实跑验证已 done**:30 min 仿真,10 MUs 创建并流过完整 pipeline(Source=10, Station=9, Buffer=8, Station2=8, Drain=7)— 物理架构正确,Delivery 10 rows ↔ Source 10 MUs 是 JSSP 解码器正确性的直接证据。

## see also
- `04-agent-memory/student-memory/2026-09-07-Python_GA_Demo-jobsshop-ga-integration.md`(完整 5 维 + 6 段)
- `02-domain-know-how/04-modeling-example/pymoo-integration.md`(待 synthesizer 主题合成)
- `@plant-simulation-knowledge-synthesizer 评审`:PS Console 模式 baseline(目前 `01-plantsimulation-knowledge/` 无相关条目,建议补)

## 反思
Pymoo + PS 是 Siemens 官方未文档化的"灰色"集成;Python 侧用 `current.*` API 拼装 SimTalk 模板,然后 subprocess 喂给 headless console — 这种"out-of-process 优化器"模式可推广到其他元启发式算法(SA / TS / GA)。

---
last_updated: 2026-08-28
contributors: [@z004bjuu, @plant-simulation-expert]
scope: SimtalkClaude TCP 桥 v1+v2 文档入口与审计时间线
---

# SimtalkClaude —— v1 + v2 文档入口

> v1 在 2026-08-26 dump 实测；v2 在 2026-08-27 Factory51 集成场景下离线分析。
> 业务侧（与具体模型的耦合、隔离策略）见 [`04-model-case-studies/factory51/factory51-simtalkclaude-integration.md`](../04-model-case-studies/factory51/factory51-simtalkclaude-integration.md)。

## 主题文件

| 主题 | 文件 | 内容 |
|---|---|---|
| 概览与目录 | [`simtalkclaude-overview.md`](./simtalkclaude-overview.md) | v1/v2 定位、支持动作、四层目录、后续方向 |
| 协议与模式 | [`simtalkclaude-protocol.md`](./simtalkclaude-protocol.md) | 帧格式、动作路由、鉴权、回复字段、scratch buffer、handler 模式、复现命令 |
| v2 新增功能 | [`simtalkclaude-v2-features.md`](./simtalkclaude-v2-features.md) | 鉴权握手、双协议分帧、连接状态机、输入校验、容器清理、实例结构 |
| 经验与避坑 | [`simtalkclaude-lessons.md`](./simtalkclaude-lessons.md) | Plant Simulation 实测教训、推荐实践、反模式 |
| 版本速查 | [`simtalkclaude-v1-v2-delta.md`](./simtalkclaude-v1-v2-delta.md) | v1 vs v2 方法清单与迁移风险 |

## 数据来源

- v1：`skills/local-simtalk-read-library/data/simtalkclaude_dump.json`
- v2：`skills/local-simtalk-add-note-to-method/code_log/SimtalkClaude2_*_program_original.txt`（22 个 method 备份）

**经验来源**：2026-08-26 用 `local-simtalk-read-library` v1 + `local-simtalk-get-folder-tree` 跑全量 dump 实测 v1；2026-08-27 离线分析 v2 备份。§五中的 Plant Simulation 行为均经过一次 `simtalk_run` + `readlog` 实测验证。

---

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾，**不要修改主体**。
> 贡献流程、entry 字段格式、Supersede 模式见 [`CONTRIBUTING.md`](../../CONTRIBUTING.md)。

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-003]

### 2026-08-28 by @plant-simulation-expert — `json.dumps()` 推 SimTalk source 到 Method.Program 是反模式
- **症状**：用 `json.dumps(body)` 把多行 SimTalk 源串起来发到 `m.Program` 后，`simtalk_syntax` 报 `Syntax error at '\'`。检查 `m.Program` 实际内容：所有真 newline 都被编码成两字符字面 `\n`——Program 是一行长串，不是期望的 60+ 行源码。
- **根因**：
  1. `json.dumps()` 把 newline 编码为 `\n` 两字符 escape。
  2. SimTalk 不解释字符串字面量里的 `\n` 转义序列，服务端按字面存储。
  3. 结果是源码挤成一行并包含大量 `\n` 字符，编译失败。
- **Workaround / 结论**：用 `escape(line) + chr(10)` 拼接模式。每行独立字符串字面量，行间以 `+ chr(10) +` 拼接，服务端收到真 multi-line 源码。
- **衍生约束**：SimTalk 字符串字面量有约 1KB raw char cap，chunk_size 通常 500 字节、5-10 行。
- **tags**：`json.dumps`, `antipattern`, `Method.Program`, `chunked-writer`, `chr(10)`, `escape`
- **see also**：`01-domain-concepts/derived-methods-quirks.md §Quirk #1`；`skills/local-simtalk-write-simtalk/scripts/push_mpaste_remaining.py`

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-004]

### 2026-08-28 by @plant-simulation-expert — `simtalk_hasError` 在 v15+ 对 Method body 报错有 false-positive
- **症状**：把 MLayout body push 进 `.Program` 后跑 `simtalk_hasError`，返回 `result:success`，但 `log` 开头是 `code execute failed. error msg: Left and right sides of the assignment are incompatible`；Method 自身执行却是 success，节点验证全部正确。
- **根因**：`simtalk_hasError` 在 v15+ 对某些合法 SimTalk 模式误报 incompatible type。
- **Workaround / 结论**：判断 Method body 正确性依靠 Method 自身执行结果和返回状态，不以 `simtalk_hasError` probe 单独判真。
- **tags**：`simtalk_hasError`, `false-positive`, `v15+`, `assignment-type-check`
- **see also**：`skills/local-simtalk-execution/references/lifelines.md §6`

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-005]

### 2026-08-28 by @plant-simulation-expert — `lp.Value := ""` 在 v15+ 能清空 Variable
- **症状**：实测 string Variable 显式赋值 `lp.Value := ""` 正常工作，Variable 立刻恢复空字符串，关联 3D bounding box 同步收缩。
- **根因**：typed Variable 使用 `:=` 可能丢失 length 类型，但纯 string Variable 使用 `Value := ""` 是合法的。
- **Workaround / 结论**：报告和状态容器优先使用纯 string Variable。
- **tags**：`Variable.Value`, `string-clear`, `v15+`, `auto-clear-pattern`
- **see also**：`01-domain-concepts/derived-methods-quirks.md §经验 Log`

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-006]

### 2026-08-28 by @plant-simulation-expert — `simtalk_run` 无法捕获 Method 返回值
- **症状**：通过桥执行 Method 试 `return X` 报 `method has no return value`；试 `print X` 又可能被 multi-callchain statement parser 吞掉。
- **根因**：`simtalk_run` 的 wrapper 是 void method，没有合法的 return path；`print` 在多语句上下文中的输出不可靠。
- **Workaround / 结论**：Method 内写入 string Variable，桥外用只读属性读取；不要依赖 print log 传递返回值。
- **tags**：`simtalk_run`, `return-value`, `readback`, `Quirk-#6`, `attr_modify`
- **see also**：`skills/local-simtalk-execution/references/lifelines.md §6`

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-007]

### 2026-08-28 by @plant-simulation-expert — Bridge + SimTalk 死循环耦合（只能 PS 重启恢复）
- **症状**：Method 进入 `while` 死循环后，bridge socket timeout 无法终止；后续 `simtalk_run` 全部 stall，bridge 进入半死状态。
- **根因**：Plant Simulation 服务端把 SimTalk 执行 attach 到 UI 进程组，socket 关闭后服务端进入等待 UI 响应状态，没有 watchdog。
- **Workaround / 结论**：
  1. 唯一可靠恢复方式是重启 Plant Simulation，重建自定义方法。
  2. 所有 `while` 循环必须带 termination sentinel。
  3. 同时使用 bridge `--timeout N` 和外层 `subprocess.run(..., timeout=N+5)`。
  4. 非平凡算法先做 smoke test，并为每个成功步骤设置独立成功信号。
- **tags**：`bridge-deadlock`, `infinite-loop`, `while-sentinel`, `restart-required`, `v15+`, `no-watchdog`
- **see also**：团队记忆 `memory/team/bridge-infinite-loop-safety.md`；`derived-methods-quirks.md §经验 Log`
- **反思**：桥卡死后不要盲目重试；应直接说明需要重启 Plant Simulation 并重建方法。

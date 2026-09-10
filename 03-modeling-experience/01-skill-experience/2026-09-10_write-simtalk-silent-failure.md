---
last_updated: 2026-09-10
dimension: 01-skill-experience
source_sessions:
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-recovery-prep.md
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md
skills_touched: [local-simtalk-write-simtalk]
models_touched: [AGV_Claude, AGV_Claude_v2]
---

# `write_simtalk.py` `[verify] OK` ≠ 实际落盘,必须 readback `.Program` 非空

## 症状
- `write_simtalk.py` 写 7 个 method body,每个 method 都报 `[verify] method executes OK after edit`。
- 次日 read_library 全模型,7 个 method 全部 `program_len: 0, program: ""` — silent failure,实际写没落盘。
- 同次 read_library 中其它已知好 method 返回正常 program 文本 → 排除 read_library 自身 bug,确认 7 method 真的空。
- 后续探活:`simtalk_send.py` 全 TIMEOUT,server JSON 层卡死(big-batch probe 触发的 server lock)。

## 根因
- `write_simtalk.py` 的 `[verify]` 检查的是 `simtalk_run` 内部表达式编译,而不是 `.Program` 属性实际写入。
- write 操作走 `simtalk_run` 含 `str_to_obj(...).Program := ...` → 字符串赋值 + 编译,看起来 `result: success` 但 `.Program` 实际为空。
- 可能与 `.Program` 编译缓存写入协议相关(参见 `2026-09-02_program-cache-stale-execute-uses-old-body.md`)。

## Workaround / 结论
- **write 后强制 readback**:`str_to_obj(path).Program` 打印或 `length > 0` 检查,非空才算落盘成功。
- **三层验证**:
  1. `m.Program` 非空
  2. `executeSilent(m.Program)` → `getExecuteSilentError = []`
  3. functional test `m.execute(args)` → success(注意要 reopen model 清缓存)
- **大 batch probe 后必插 ping / 退避**:server lock 卡死与 big-batch(14 batch × 8 paths)有关。
- **失败后停手 + 回报**:不盲重试,写 usage log + 通知用户重启 server。

## see also
- `04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-recovery-prep.md §Key findings 第 1 条`
- `04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md §03-workflow-playbook`
- `@skills-optimizer 评审`:`write_simtalk.py` 的 `[verify]` 日志应改成"readback `.Program` 非空 + executeSilent []",不是 execute success

## 反思
"silent success"是最危险的失败模式 — log 全绿但结果全空。SKILL.md 的硬规则应强制 write→readback,不允许只靠 skill 内部 verify log。

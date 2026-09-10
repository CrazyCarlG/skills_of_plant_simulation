---
last_updated: 2026-09-10
dimension: 01-skill-experience
source_sessions:
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md
skills_touched: [local-simtalk-execution, local-simtalk-write-simtalk]
models_touched: [AGV_Claude]
---

# `.execute()` 不刷新 `.Program` 编译缓存(写后用 `.execute()` 跑老代码)

## 症状
- 用 `simtalk_run` / `write_simtalk.py` 写入 `m.Program := "<new body>"` 后,`simtalk_syntax --target-path m` 验证 `has no Error`(新代码编译过)。
- 紧接着 `m.execute(args)` 仍跑**首次编译**的旧版本 body。`.execute()` 返回 `execute success`,但实际行为是旧代码。
- 重启 bridge / 重新 `ping` 不解决问题;只有 **close + reopen model file** 才让 `.execute()` 用新 body。

## 根因
- `.execute()` 走的是 Plant Simulation 内部对 `.Program` 的**编译缓存**,不是每次重新 parse。
- 写操作只更新 `.Program` 的字符串值,不触发该 Method 在 PS 内部的编译槽失效。
- `executeSilent(<expr>)` 是唯一 fresh-compile 通路:把字符串作为表达式重新编译并执行。

## Workaround / 结论
- **写后验证流程**(铁律):
  1. `m.Program := "<new>"`
  2. `executeSilent(m.Program)` → `getExecuteSilentError` 检查,空数组=语法过
  3. **不要**靠 `m.execute(args)` 做 readback — 它会用旧 cached compilation
  4. 若必须 `.execute()`,先让用户在 GUI **关闭 + 重新打开 model file**
- 推荐路径:`executeSilent(str_to_obj(path).Program)` 作为统一的 readback 协议(配合 `getExecuteSilentError` 拿 error)
- 用户场景:.AGV_Claude.Pool 7 个 method 全部走 executeSilent 编译验证,跳过 `.execute()` 直到用户 reopen

## see also
- `04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-recovery.md §Key findings 第 3 条`
- `04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md §03-workflow-playbook`
- `@skills-optimizer 评审项`:`local-simtalk-write-simtalk/SKILL.md` 的 `[verify] method executes OK after edit` 日志不可靠,应改成 `[verify] executeSilent + getExecuteSilentError = []`

## 反思
`.execute()` vs `executeSilent(<expr>)` 在 PS 内部走两条不同的编译路径,前者带缓存,后者每次 fresh — 这是 SKILL.md 当前文档未覆盖的语义差。

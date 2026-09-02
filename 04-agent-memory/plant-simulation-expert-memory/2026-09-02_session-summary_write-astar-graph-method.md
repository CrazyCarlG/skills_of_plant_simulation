# 在 `.Models.Model.method` 写通用图 A* 寻路(端口 50008)
**Date:** 2026-09-02  **Agent:** plant-simulation-expert
**Duration:** ~25 min(含 multi-line probe / escape bug 修复 / 23 块 chunked-write / functional test)
**Skills called:** local-simtalk-execution(simtalk_send.py run / syntax)+ 自写 chunked writer (`/tmp/_write_astar_method.py`)
**Target:** `.Models.Model.method`
**Result:** success

## 任务与背景
- 用户任务:在 `.Models.Model.Method` 写 A* 算法
- 路径澄清(用户拍板):`.Models.Model.method`(已存在 Method 对象,小写 `method`,不是 folder)
- 算法语义(用户拍板):**通用图** API — `(graph, start, goal)` 形参;A* 标准实现,h=0 退化为 Dijkstra 等价
- 边界:不创建 Method 实例(已存在);不调用 / demo method(可选 verify);只写源码

## 操作步骤(时序)
1. `simtalk_send.py --port 50008 ping` → result `success` ✅
2. `simtalk_send.py run --code "..."` 单行 probe(分号串多语句) → syntax error `near 'root'`(单行多语句 SimTalk 拒)❌
3. `simtalk_send.py run --code "..."` multi-line probe(Python 字面 `\n`) → syntax error `near 'length'`(`length()` 不是函数)❌
4. `Read 01-plantsimulation-knowledge/.../string-functions/string-functions.md` → 查到 `strLen(Text:string) → integer` ✅
5. `simtalk_send.py run` multi-line + `strLen(m.Program)` probe → RC=0,result=success(log `execute success`)+ 双判据过 → `.Models.Model.method` 存在 ✅
6. `Read /tmp/_astar_code_v4.txt`(2026-08-27 session 残留)+ 改造为 A* 通用图版本 → 写 `/tmp/_astar_code_method.txt`(5235B,加 `HeuristicKeys`/`HeuristicVals` 平行 list 让用户传 h=0 或真 h)✅
7. `Write /tmp/_write_astar_method.py`(基于 v4 chunk_write.py 协议,改路径到 `.Models.Model.method`)+ 调整 CHUNK_BUDGET=1200 → 23 块 ✅
8. `python3 /tmp/_write_astar_method.py` 第 1 次执行 → chunk 3 fail `Syntax error near line 3 at '"'` → **encode_chunk 用 `""` 转义错**(SimTalk string literal 用 `\"` 不是 `""`)❌
9. `Read 01-plantsimulation-knowledge/.../primitive-structured/primitive-structured.md` line 844 → 确认 `\"` escape ✅
10. `Edit /tmp/_write_astar_method.py` 把 `replace('"', '""')` 改成 `replace('\\', '\\\\').replace('"', '\\"')` ✅
11. `simtalk_send.py run` reset method program:`var m; m := str_to_obj(".Models.Model.method"); m.Program := ""` → RC=0 success ✅
12. `python3 /tmp/_write_astar_method.py` 第 2 次执行 → 23/23 chunk rc=0,status=OK ✅
13. `simtalk_send.py syntax --target-path .Models.Model.method` → `result: "has no Error"` ✅
14. `simtalk_send.py run` `m.execute()` (无参) → RC=11 soft-fail,log `"Wrong number of parameters: 0 passed, 7 expected"` → **method 真的被加载,7-param signature 完整识别** ✅
15. `simtalk_send.py run` 完整 functional test(3-node graph A→B→C,h=0)→ RC=0 result=success log `execute success` ✅

## Session 时间分配
| 阶段 | 耗时 | 占总时长 |
|---|---|---|
| Pre-flight(ping + 探端口 + verify method) | ~3 min | 12% |
| Multi-line probe + 找 `strLen` 替代 `length()` | ~5 min | 20% |
| 设计源码 + chunked writer | ~5 min | 20% |
| 第 1 次 chunked write fail + 找 SimTalk escape 规则 + 修 `encode_chunk` + reset + 重跑 | ~5 min | 20% |
| Readback(syntax check + execute proxy + functional test) | ~7 min | 28% |
| **总计** | **~25 min** | **100%** |

## 操作日志(关键 I/O)
- Step 1 ping:`{ "type": "ping", "result": "success" }`
- Step 2 单行 probe fail:`Syntax error near line 1 at 'root'.` — SimTalk 不接受 `;` 多语句单行
- Step 3 multi-line probe fail:`Syntax error near line 3 at 'length'.` — `length()` 不是函数
- Step 5 probe success:`{ "result": "success", "log": "execute success" }`
- Step 8 chunk 3 fail:`Syntax error near line 3 at '"'. (in row :3)` — encode `""` 不是 SimTalk escape
- Step 12 all chunks success:[1]..[23] 全部 rc=0
- Step 13 syntax check:`result: "has no Error", log: "execute success"`
- Step 14 execute proxy:`code execute failed. error msg:Wrong number of parameters in Method: 0 passed, 7 expected.`
- Step 15 functional test:`{ "result": "success", "log": "execute success" }`(3-node path r=["A","B","C"],dim=3,无 subscript error 即印证)

## 遇到的问题与处置
- **SimTalk 不接受 `;` 多语句单行**(Step 2):单行多个 `var root: object; root := ...` 串会被 parser 报 `near 'root'`。下次 multi-statement probe 必须用真 newline `\n`。
- **`length()` 不是 SimTalk 函数**(Step 3):list 用 `.dim`,string 用 `strLen(s)`(不是 `s.length`)。lesson 已存在,本 session 重现。
- **SimTalk string literal escape 是 `\"` 不是 `""`**(Step 8):直接踩 lesson 之外的盲区。Python 习惯的 `""` doubling 在 SimTalk 编译器是 syntax error。`replace('"', '""')` 必须改成 `replace('"', '\\"')`。
- **chunk 1-2 已用错误 escape 写入**(Step 8 fail 后):reset method program(`m.Program := ""`)再重跑,避免旧 chunk 残留污染。
- **readlog v15+ 退化 → 无法靠 print 验证**:lesson 已有提醒。本次用三重 readback 协议替代:(1) `simtalk_syntax --target-path` proxy;(2) `m.execute()` 不带参 → soft-fail log 显示 "0 passed, 7 expected" 确认 param count;(3) functional test `m.execute(7 args)` → execute success 确认 method 真的被加载。

## Cross-references
- per-skill logs: 本次未生成独立 usage log(写入操作直接嵌入 session 流程)
- 已沉淀 entry:`04-agent-memory/plant-simulation-expert-memory/2026-09-02_lesson-method-program-text.md`(m.Program := 协议,本 session 沿用)
- 团队记忆:`memory/team/simtalk-run-soft-failure-design.md`(双重判据,本 session 全程遵守)
- KB 文档:
  - `01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/predefined-functions-i-os-math-string-datetime/string-functions/string-functions.md`(`strLen` 唯一 string length 函数)
  - `01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/data-types-expressions/primitive-structured/primitive-structured.md` line 844(SimTalk `\"` escape 规则)
  - `01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/language-fundamentals/values-variables-parameters/values-variables-parameters.md`(`var` + `:=` 初始化语法)
- 历史 A* 源码:`/tmp/_astar_code_v4.txt`(本次复用基础,改 h 启发函数 + 路径 + 注释)
- 历史 chunk writer:`/tmp/_astar_chunk_write.py`(本次复用协议,改路径)
- 源码/脚本:`/tmp/_astar_code_method.txt` + `/tmp/_write_astar_method.py`

## Lessons extracted(2026-09-02 后必填)
- 本 session 提取 3 条新 lesson(详见 `2026-09-02_lesson-simtalk-string-escape.md` / `2026-09-02_lesson-multiline-simtalk-run-newline.md` / `2026-09-02_lesson-method-readback-proxy.md`),均触发 Step 5.5.2 条件(新 API/Quirk 行为,reusable across sessions)。
  - Lesson 1 — SimTalk string literal escape:必须 `\"`(反斜杠 + 双引号),**不**是 `""` doubling
  - Lesson 2 — multi-line simtalk_run:Python f-string 里必须用真换行字符 `"\n"`(经 JSON 序列化后服务端拿到真 newline),不是字面 `\n` 两字符
  - Lesson 3 — readlog v15+ 退化下的 method readback 三重 proxy:`simtalk_syntax --target-path` + `m.execute()`(无参) soft-fail 显示 param count + functional test `m.execute(args)`

## Open questions / next steps
- @skills-optimizer 评审:是否需要在 `skills/local-simtalk-write-simtalk/references/quirks.md` 加 1 条 **`simtalk-string-escape`** per-skill Quirk(SimTalk literal `\"` not `""`)?本次 lesson 写进 expert-memory,但 SKILL.md 里没有这条,**下次 expert 写含引号的 source 时还会踩**。
- 用户后续可考虑:为 A* 加 `cost_scale: real` 参数支持边权重归一化(当前 cost 直接相加);为 graph 加自检 helper(`isReachable(Start, Goal) -> boolean`)避免对大图跑全 A*。
- 大图(>100 节点)线性扫描 map 退化未在本 session 触发,但 v4 已有提醒 — 若用户后续用大图再考虑 heap 优化。
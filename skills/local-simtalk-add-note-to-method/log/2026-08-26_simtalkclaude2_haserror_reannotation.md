# 2026-08-26 — 按新规则重注 `.SimtalkClaude2.src.SimtalkAction.simtalk_hasError`

## 目标

按用户给出的新规则（**"注释前请先大致了解下 Plant Simulation，并使用
`local-simtalk-read-library` 了解下模型的框架"**），把上一轮给
`.SimtalkClaude2.src.SimtalkAction.simtalk_hasError` 加的 51 行 NOTE 头**升级**成
113 行 NOTE，把 `simtalk_hasError` 在整个 SimtalkAction 里的真实调用关系、副作用
消费者、和占位 Method 的作用全部讲清楚，不再只写"接受一段代码 → 检查 → 返回"这种
签名级摘要。

新规则已保存到 feedback memory：
`memory/simtalk-annotation-prelude-rule.md`。

## 新规则触发的工作流（以后每条 NOTE 都按这个跑）

| 步骤 | 工具 | 产出 |
| --- | --- | --- |
| 1 | `01-plantsimulation-knowledge/01-plant-simulation-help/` | 读 SimTalk 注释语法 / Method 对象属性 / `obj.execute` 生命周期 |
| 2 | `local-simtalk-read-library/scripts/read_library.py --no-infobox --tree-depth 5` | 整个模型的 Method inventory + 源 |
| 3 | `grep` 当前方法名跨库查 caller | 拿到所有 `executenewcallchain` / 直接调用的入口 |
| 4 | 读 `data/library_dump.json` 里 target 的 `program` | 拿到原始 body 用于字节级对比 |
| 5 | 写新 NOTE — 包含实际 caller 链、字面返回值契约、副作用消费者 | — |
| 6 | **分块写** `obj.program`（每块 ≤ 2 KB），校验 `simtalk_hasError(obj.program) == "has no Error"` | — |

## 本轮实际执行

### 步骤 1 — 读 Plant Simulation 知识库

只读了关键几条：
- `simtalk/language-fundamentals/values-variables-parameters` —— 确认 `--`/`//`/`/* */`
  的合法位置
- `simtalk/control-flow-error-handling/return` —— 确认 `return` 在 `if/else` 之外的写法
- `objects/information-flow-objects/Method/methods/methods.md` —— 确认 `hasSyntaxError`
  的官方签名 "Returns whether the source code of the Method designated by `&` has
  syntax errors"，**必须有 `&Method` 引用**，不能对临时字符串做语法检查

最后这条直接解释了为什么 `simtalk_hasError` 要把 code 挂到 `&simtalkcode.program`
再检查 —— 不是失误，是 `hasSyntaxError` 的硬约束。

### 步骤 2 — 跑 `read_library.py` 抓 `.SimtalkClaude2` inventory

```bash
python3 skills/local-simtalk-read-library/scripts/read_library.py \
    --no-infobox --tree-depth 5 --out /tmp/simtalkclaude2_prelude.json
```

抓到了 40 个 `.SimtalkClaude2.*` Method（包括 `.SimtalkClaude2.main.*` 和
`.SimtalkClaude2.src.*` 两套 —— `.main` 是 `.src` 的实例层副本，不是新定义，
`local-simtalk-add-note-to-method` 的继承探测脚本要跳过 `.main`）。

**踩坑**：`read_library.py` 用批量 probe，受 v15+ readlog 截断（累积 buffer > 50 KB
就截断）影响，**所有 40 个 `.SimtalkClaude2` 方法的 `program` 字段在最终 JSON 里
都是空字符串**（输出 dump 里 `"program": ""`、`"program_len": 0`），但 metadata
字段（path/name/type）都填对了。

绕路：用单方法 readlog 探针模式手抓 `simtalk_hasError` 的当前 program，得到了
51 行 NOTE + 14 行 body 的完整原文。

### 步骤 3 — 跑 `grep` 抓 caller

从已有 `data/simtalkclaude_dump.json`（旧库的 dump，仍是 `.src` 的真源）里 grep
`simtalk_hasError`：

```
.SimtalkClaude.src.SimtalkAction.Run_Simutalk
    action_result["log"] := simtalk_hasError(simtalk)
    var syntax_result := action_result["result"]
    if syntax_result = "success" then ...

.SimtalkClaude.src.SimtalkAction.get_simtalk_hasError
    var code_synax := simtalk_hasError(simtalk)
    action_result["result"] := code_synax
```

`m_callback`（`simtalk_syntax` / `simtalk_run` 的入口）通过
`executenewcallchain(j)` 调到这两个 wrapper，wrapper 再调 `simtalk_hasError`。

### 步骤 4 — 读 `simtalkcode` 占位 Method

`simtalkcode` 在 `.SimtalkClaude.src.SimtalkAction.simtalkcode` 层级声明，body 只
有一行 `var obj:=.createfodler`，故意留空。它是给 `hasSyntaxError` 提供 `&Method`
引用目标的占位对象 —— 因为 Plant Simulation 的 `hasSyntaxError` 不接受临时字符串。

### 步骤 5 — 写新 NOTE（113 行）

旧 NOTE 51 行只覆盖了：
- Purpose
- Parameters
- Algorithm
- Return value
- Side effects
- Notes

新 NOTE 在此基础上新增 2 节：
- **Direct callers**：明确点名两个直接 caller（`Run_Simutalk` 读 `action_result.result`
  槽位，`get_simtalk_hasError` 读本方法的返回值回写槽位 —— **两条读取路径不同**，
  这是双写的关键）
- **Dispatch entry**：解释 `m_callback` 通过 `executenewcallchain(j)` 把 socket JSON
  分发到 wrapper 方法

每节都把字面契约写死（前导半角空格 + 全角冒号、success/failed 的小写），
让未来读 NOTE 的人不会"好心 ASCII 化"破坏远程解析。

## 本轮踩到的新坑（这次新发现的，Run_Simutalk / ReadLogFile 那两轮没暴露）

### 坑 1：单 payload > ~2 KB 必失败

**特征**：尝试一次写完整 113 行 NOTE（payload 7542 chars） → 5 次 retry 全是
`Error in JSON data: Error in line 1: Unexpected end of string`。

读 ReadLogFile usage log 时我以为这是偶发 transient，retry 5 次能解。**实际不是**。
本次的 NOTE 比 ReadLogFile 大一倍，跑完 5 次 retry 没一次成功；而且错误信息附带
`Syntax error near line 1 at 'hr(10) + "--'` —— 意味着 payload 在 server 端 buffer
里就被截了，根本没等到 retry 时机。

**根因**：server 端 JSON parser 的 recv buffer 约 ~6 KB，超过这个长度的 payload
在某些时序下会被截断。Run_Simutalk (4711 字符) 偶尔成功偶尔失败 (ReadLogFile
3909 字符也 fail 过 2 次) 的"非确定阈值"就是 ~6 KB。

**修复**：分块写，每块 ≤ 2 KB。

### 坑 2：分块写有 2 种语义

我先用两阶段方案（Phase 1 写 NOTE 全部，Phase 2 append body）—— 第一阶段 6938
字符 payload 又 fail，因为 NOTE 本身就超 2 KB。**正确的分块**：

```simtalk
# chunk 1: obj.program := chunk_1_RHS        # 替换
# chunk 2: obj.program := obj.program + chr(10) + chunk_2_RHS  # append
# chunk 3: 同上
# body:    obj.program := obj.program + chr(10) + body_RHS   # append
```

每块 payload 控制在 1.5–2 KB 范围内，30 行 NOTE / 块，14 行 body 单独一块。
**所有 4 次 chunk + 1 次 body 全部第一次尝试就成功**（rc=0, attempts=1）。

### 坑 3：readlog 截断导致 `read_library.py` 输出空 program

这是 `local-simtalk-read-library` 的已知问题（v15+ readlog 累积 buffer > 50 KB
截断，详见 LIB-2 quirk）。本轮的影响：

- `read_library.py` 批量 probe 整个模型 → 累积 log 超阈值 → 后续 probe 的 program
  输出被截
- 结果：JSON dump 里 `.SimtalkClaude2.*` 全部 `program: ""`
- 绕路：单方法 readlog 探针，每次探一个方法、立即 readlog 抓、`print obj.Program`
  + `###PRG_START###` / `###PRG_END###` 标记模式

未来如果要做全库 dump，应该按 LIB-2 的建议：每批 ≤ 8 个 method + 立即 readlog
+ 标记模式。当前这次只关心 `simtalk_hasError` 1 个 method，用单探针就够了。

## 最终状态

| 维度 | 结果 |
| --- | --- |
| NOTE 行数 | 113 行（之前 51 行 → 现在 113 行，新增 Direct callers + Dispatch entry 两节） |
| NOTE 写入 | ✅ 4 块 chunk 全部 rc=0，每块 attempts=1 |
| 原 body 字节保留 | ✅ append 阶段读 backup + 原样 quote + chr(10) 拼接 |
| `simtalk_hasError(obj.program)` | ✅ `has no Error`（readlog 抓到） |
| `obj.internalclasstype` | ✅ `Method` |
| 备份可用 | ✅ `log/SimtalkClaude2_src_SimtalkAction_simtalk_hasError_program_original.txt` |
| 新规则可复用 | ✅ 已保存到 `memory/simtalk-annotation-prelude-rule.md` |

## 教训（下次别再踩）

1. **单 payload ≤ 2 KB 是硬约束**。超过这个长度 5 次 retry 也不一定能救 —— 必须
   分块写。判断逻辑：NOTE 行数 × 平均行长 ≈ 50 字节 / 行，**超过 ~30 行 NOTE 就
   应该按 25-30 行 / 块分块**。

2. **分块写 ≠ 一次写 NOTE+body**。两阶段（先 NOTE 后 body）也不行，因为 NOTE
   本身就 > 2 KB。正确做法：把 NOTE 也按 25-30 行切块，第一块用 `obj.program :=`
   替换，后续每块用 `obj.program := obj.program + chr(10) + ...` 追加。

3. **`read_library.py` 在 `.SimtalkClaude2` 这种已经加过 NOTE 的库上会全空**。
   v15+ readlog 累积 buffer 已经被之前几次操作填满，再跑批量 probe 会让
   `print obj.Program` 输出被截。要么 clearLogFile 重置，要么用单方法 readlog
   探针模式 + 立即 readlog 抓标记区间（参见 LIB-2）。

4. **`hasSyntaxError` 必须挂在 `&Method` 上**，不能对临时字符串检查。这一条
   解释了为什么 `simtalk_hasError` 一定要先 `&simtalkcode.program := code` 再
   `&simtalkcode.hasSyntaxError(...)` —— 不是冗余，是 Plant Simulation 的硬约束。
   `simtalkcode` 这个占位 Method (body `var obj:=.createfodler`) 就是为这个需求
   设计的。

5. **新规则要落地到 feedback memory 而不是 usage log**。usage log 是事件记录，
   feedback memory 是跨会话生效的工作流规则。这次的新规则（注释前必须 read-library）
   已经保存到 `memory/simtalk-annotation-prelude-rule.md`，下次会话第一轮就会被
   LLM context 加载，不会重复踩"没查 caller 就硬写 NOTE"的坑。

6. **NOTE 必须讲字面契约**。`action_result.result` 是 `success` 还是 `Success`、
   返回串前导是 `"hasError"` 还是 `" hasError "`（有前导空格）、冒号是半角 `:` 还
   全角 `：` —— 这些都是**调用方按字面比较**的契约，NOTE 必须写死。下次改 NOTE
   想"顺手清理空格"前先 grep 一下所有 caller 是不是有同样的字面值。

## 关联文件

- 备份（未动）：`skills/local-simtalk-add-note-to-method/log/SimtalkClaude2_src_SimtalkAction_simtalk_hasError_program_original.txt`
- 写入脚本（一次性，已完成任务）：
  - `/tmp/reannotate_haserror.py` —— 单 chunk 7542 字符 → 失败
  - `/tmp/reannotate_haserror_v2.py` —— 2 阶段（NOTE then body）→ NOTE 阶段 6938
    字符仍超 2 KB → 失败
  - `/tmp/reannotate_haserror_v3.py` —— 4 块 chunk + 1 块 body → ✅
- 新规则 feedback memory：`memory/simtalk-annotation-prelude-rule.md`
- 关联 usage log：
  - `usage_log/2026-08-26_simtalkclaude2_runsimutalk_annotation.md`（上一轮单 chunk
    4711 字符的"成功"其实是侥幸过线）
  - `usage_log/2026-08-26_simtalkclaude2_readlogfile_annotation.md`（3909 字符 3 次
    retry 才过——已经是当时的边界征兆）
  - 反馈 memory：`memory/simtalk-note-block-comment-trap.md`（`/* ... */` 的来源）
  - 参考 memory：`memory/simtalk-comment-docs.md`（`--` / `//` / `/* */` 的权威出处）
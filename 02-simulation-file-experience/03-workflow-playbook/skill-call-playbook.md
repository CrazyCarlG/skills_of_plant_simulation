---
last_updated: 2026-08-28
contributors: [@z004bjuu, @plant-simulation-expert]
scope: 9 个 `local-simtalk-*` 技能调用决策矩阵 + 写操作 5 步硬流程 + Top 10 高频坑
---

# Plant Simulation 技能调用实战手册 — 2026-08-26/27 总结

> **来源**：扫读了 9 个 skill 的 `log/` 与 `usage_log/`（共 130+ 条 session 文件，时间跨度 2026-08-24 ~ 2026-08-26），按主题提炼跨 skill 共有的模式、坑、决策矩阵。
>
> 与既有两份文档互补：
> - `01-domain-concepts/class-instance-frame-folder.md` — 讲 **Plant Simulation 领域概念**（Class/Instance/Frame/Folder）
> - `02-bridge-tool/simtalkclaude-v1-and-v2.md` — 讲 **.SimtalkClaude bridge 内部**（协议、scratch buffer、ErrorHandler）
> - 本篇 — 讲 **agent 调用 9 个 skill 时的工作流、坑、决策**（跨 skill 通用）
>
> 所有 "Quirk #N" 编号沿用 `local-simtalk-execution/references/lifelines.md` 的统一编号。

---

## 一、9 个 skill 的依赖关系（一张图）

```
                          plant-simulation-expert (大脑)
                                       │
                                       │ Agent tool, subagent_type
                                       ▼
            ┌─────────────────────────────────────────────────┐
            │           local-simtalk-execution                │  ← 唯一的传输层
            │   scripts/socket_client.py / simtalk_send.py    │
            │   WSL2→host.docker.internal:50007, ||END|| 帧   │
            └────────────────────────┬────────────────────────┘
                                     │ 所有其它 skill 都在它的基础上
        ┌──────────────┬────────────┼────────────┬──────────────┐
        ▼              ▼            ▼            ▼              ▼
   os-functions  get-folder-tree get-class-  read-library  modify-attribute
                              inheritance
        ▲              ▲            ▲            ▲              ▲
        │              │            │            │              │
        │   ┌──────────┴────────────┴────────────┴──────┐       │
        │   │                                            │       │
        ▼   ▼                                            ▼       ▼
   add-note-to-method  write-simtalk                class-management
        └──────────────┬─────────────┘
                       │
                  add-note  ←  write-simtalk 的底层
```

**关键观察**：

1. **`local-simtalk-execution` 是唯一触达 Plant Simulation 进程的 skill**——其它 8 个都是它的"领域封装"。所以所有传输层 Quirk（v15 readlog 回归 / Quirk #6 / #7 / #13 / 模态陷阱）会 100% 渗透到上层 skill。
2. **当上层 skill 撞上未覆盖的边界，正确的 fallback 是"掉到 `local-simtalk-execution` 直接跑原始 SimTalk"**，不要硬在 skill 内部绕。
3. **`local-simtalk-read-library` 的产物（`data/library_dump.json`）会被多个下游 skill 引用**——它是后续 add-note / write-simtalk / class-management 的"前置语义地图"。

---

## 二、按操作类型分组的坑与最佳实践

### 2.1 读操作 / Read

| Skill | 核心坑 | 解决方案 | 出处 |
|---|---|---|---|
| `get-folder-tree` | 默认 depth 4 = 45 round-trips；depth 大了 server 端慢但 client 不会挂 | `--no-infobox` 模式批量跑 | `test-session-20260825-v3.md` |
| `get-class-inheritance` | batch > 8 paths 触发 readlog 截断，3/8 batches 返 0 行 | 收紧到 ≤ 8 paths/batch 或加 inter-batch sleep 2 | `test-run-20260826-v2.md` Finding #6 |
| `read-library` | BATCH=8 在小方法上够用；对内嵌多行字符串的方法会丢内容 | 单方法一次 + sleep(1.2) + readlog；或 marker 模式 `###PRG_START###` / `###PRG_END###` 抓 print 输出 | `02-bridge-tool/simtalkclaude-v1-and-v2.md` §五.2 + `lifelines.md` §5 |
| `modify-attribute` | `--read-only` 在 shell 循环里连发偶发 transient syntax-error | sleep 1 重试一次 | `modify-attribute/log/SUMMARY.md` Round 1 Quirks |

### 2.2 写操作 / Write

**所有写操作的 5 步硬流程**：

```text
1. type-check        → str_to_obj(path) + print obj.internalclasstype  // 确认是 Method/Variable/...
2. backup            → print obj.program / obj.<attr> 写到 *.original.txt
3. compose           → quote(line) + chr(10) 串成 RHS  // 切勿用字面 "\n"
4. single-shot write → obj.program := <完整 RHS>
                       // 绝不"先写 NOTE 再 readback 再 append body" —— v15 readlog 已废
5. verify            → simtalk_hasError(obj.program) + obj.execute(smoke_payload)
```

| Skill | 写操作专属坑 | 最佳实践 | 出处 |
|---|---|---|---|
| `add-note-to-method` | payload > ~2KB → 服务端 JSON parser 截断 → "Unexpected end of string" | 分块写（NOTE 每块 ≤ 30 行 / ≤ 2 KB） | `2026-08-26_simtalkclaude2_haserror_reannotation.md` 坑 1 |
| `add-note-to-method` | NOTE 文本里含 `\` → quote() 转义后 server 看到字面 `\\"` → 提前闭合字符串 | NOTE 里完全避免 `\` 字符；要"双引号"语义直接写中文或单引号 | `2026-08-26_simtalkclaude2_runsimutalk_annotation.md` 坑 3 |
| `add-note-to-method` | NOTE 行 `--` 与裸 `===` 行混排 → SimTalk lexer 把 `==` 当 token 报 syntax error | 整段 NOTE 包在 `/* ... */` 块注释里（Quirk #9） | `simtalk-note-block-comment-trap` memory |
| `add-note-to-method` | `print obj.program` 多行输出有"每行时间戳前缀" → readback 字节校验失效 | 不要做"读回 + 字节比较"中间步骤；改用 `simtalk_hasError + obj.execute` 验证 | `m_paramRack_annotation.md` What this run did NOT use |
| `write-simtalk` | `add_note.py --note A --note B --note C` argparse `nargs="+"` 不带 `action="append"` → args.note 被覆盖成 `['C']` | 改用 `--note A B C D`（单 `--note` 多位置参数） | `session-20260826.md` Bug 1 |
| `write-simtalk` | `method`（小写）是 SimTalk 保留字（data type），新建 Method 实例报 "Invalid identifier" | 改用 `Method`（大写 M，Frame 自带） | `session-20260826.md` Bug 2 |
| `write-simtalk` | `var p: object := str_to_obj(...); p.create(...)` → "Unknown identifier 'create'"（Method/Variable 不是 MU） | 走 `class_ops.py duplicate .InformationFlow.Method .Models.Model myMethod`（即 `<Class>.duplicate(frame, name)`） | `session-20260826.md` Step 5 |
| `modify-attribute` | `--batch` 模式 restore snippet 复用一个 `var o_: object := ...` 在同一作用域重声明 → `'o_' is already defined` | 后缀索引 `o_0`/`o_1`/`o_2` | `modify-attribute/log/SUMMARY.md` Bug #2 |
| `modify-attribute` | restore 正则用 `re.match` 锚定 `Capacity:` → SimTalk log 有时间戳前缀 `2026-08-26 13:13:39: Capacity: 8 -> 12` → match 失败 → before 值丢失 → restore 不跑 | 改用 `re.search` | `modify-attribute/log/SUMMARY.md` Bug #1 |
| `class-management` | `derive vs duplicate vs create` 三种语义混淆 | 见下方"决策矩阵 §3" | `class-management/log/session-20260826.md` Part F |

### 2.3 探针 / Probe

**所有"我要看看 X 的 Y 属性"的操作统一套路**：

```bash
python3 local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object := str_to_obj("<path>");
   print "###MARKER_START###";
   print <expression>;
   print "###MARKER_END###"'
```

- `###MARKER_*###` 是**唯一可靠**的"分隔 print 输出与 readlog 噪音"的手段（因为 readlog 截断会丢前文 → 取最后 `###END###` 与 `###START###` 之间的内容是稳定的）。
- 不依赖 readlog 全量日志、不依赖 `data` 字段（Quirk #6：永远空）。
- 想拿实际值 → 去 Plant Simulation GUI Console（Window ribbon → Console）肉眼读 print。

### 2.4 通知与 UI / Notification

按用户约定（v18+ 落地）：

| 操作 | SimTalk 写法 | 是否安全 | 出处 |
|---|---|---|---|
| 开始时通知 | `infoBox("<text>", false)` | ✅ 非模态 | `test-session-20260825-v18.md` §3 |
| 收尾关闭 | `infoBox("", false)` | ✅ 幂等 no-op | 同上 |
| 防御性二次关闭 | `infoBox("", false)` ×2 | ✅ | 同上 |
| 模态通知（禁忌） | `infoBox("<text>")` / `infoBox("<text>", true)` / `prompt(...)` / `promptList*(...)` | ❌ 永久阻塞服务端 | `lifelines.md` §4 |

> **为什么 `infoBox("", false)` 重要**：GUI 端的消息框不会被 socket 关闭；如果不主动关，下次跑测试时 GUI 上挂着前一轮的 msgBox 会让用户困惑。

---

## 三、决策矩阵 / Decision Matrices

### 3.1 选哪个 skill？

| 用户意图 | 首选 skill | 兜底 skill（直接跑 SimTalk） |
|---|---|---|
| 检查这段 SimTalk 语法 | `local-simtalk-execution` (`syntax`) | — |
| 跑一段 SimTalk 拿结果 | `local-simtalk-execution` (`run`) | — |
| 想知道某对象的属性 | `local-simtalk-modify-attribute` (`--read-only`) | `local-simtalk-execution` + `str_to_obj` |
| 想改某个对象的非 program 属性 | `local-simtalk-modify-attribute` | `local-simtalk-execution` |
| 想给某个 Method 加注释 | `local-simtalk-add-note-to-method` | `local-simtalk-write-simtalk` |
| 想完全重写一个 Method | `local-simtalk-write-simtalk` | `local-simtalk-execution` + `obj.program :=` |
| 想列出模型结构（Frame / Folder / 类） | `local-simtalk-get-folder-tree` | — |
| 想看某个对象的继承链 | `local-simtalk-get-class-inheritance` | `local-simtalk-execution` + str_to_obj + print Origin/Class/OriginRoot |
| 想 dump 所有 Method 源码 | `local-simtalk-read-library` | `local-simtalk-execution` 单方法探针 |
| 想新建类 / 派生类 | `local-simtalk-class-management` (`derive`/`duplicate`) | `local-simtalk-execution` |
| 想新建 Method / Variable 实例 | `local-simtalk-class-management` (`duplicate` 到 Frame) | `local-simtalk-execution` + `<Class>.duplicate(frame, name)` |
| 想用 OS 函数（文件/注册表/进程/环境变量） | `local-simtalk-os-functions` | `local-simtalk-execution` |

### 3.2 `derive` vs `duplicate` vs `create`

| 想做的事 | 错的方式 | 对的方式 |
|---|---|---|
| 在 Class Library 加 Station 子类 | `duplicate(.Models, "MyStation")` → 得到**无父类独立副本** | `derive(.Models, "MyStation")` → 保留继承 |
| 把 Station 放进 Frame 当实例 | `cls.create(frame)` → "Unknown identifier 'create'"（Station 不是 MU） | `duplicate(.Models.Model, "Inst")` → 真正的实例 |
| 想同时派生 + 放进 Frame | `create(frame)` → 仍失败 | `derive(.Models.Model, "Inst")` 或 `duplicate(.Models.Model, "Inst")`（二者等价） |
| 想新建 Method 实例 | `p.create(frame)` → "Unknown identifier 'create'" | `local-simtalk-class-management duplicate .InformationFlow.Method .Models.Model myMethod` |
| 判断节点是不是类 vs 实例 | `NumChildren > 0` / `InternalClassType` | **`Origin == VOID AND Class == VOID` → 类；否则实例** |
| 设置实例 2D 位置 | `<obj>.setPosition := [100, 100]` → 编译错 | `<obj>.setPosition(100, 100)` → 方法调用 |

完整 Origin/Class/OriginRoot 矩阵见 `01-domain-concepts/class-instance-frame-folder.md` §2.3。

### 3.3 怎么判断"成功 vs 失败"？

| 请求类型 | 成功判据 | 失败判据 |
|---|---|---|
| `ping` | `result == "success"` | `result == "failed"` 或 socket timeout |
| `simtalk_syntax` | `"hasError" not in result`（即 `"has no Error"` 在 result 里） | result 含 `"hasError"` → 退出码 12 |
| `simtalk_run` 语法错 | `result == "failed"` + log 含 `Syntax error near line N` | **这是真失败**，不是软失败 |
| `simtalk_run` 运行时异常 | **仍然 `result == "success"`** + log 以 `code execute failed. error msg:...` 开头 | 这是 **Quirk #7 软失败** —— 必须 parse log |
| `simtalk_run` 真正成功 | `result == "success"` AND `not log.startswith("code execute failed")` | — |
| `readlog` v15+ | `result == "success"` 但 ⚠️ 内容不可信（可能反馈循环 / 截断） | 退出码 20 标 warning |

> **致命陷阱**：永远只看 `result == "success"` 就以为成功——这会漏掉 100% 的运行时异常（Quirk #7）。

### 3.4 退出码 / Exit Codes

| 退出码 | 含义 | 出处 |
|---|---|---|
| `0` | 语义成功 | `socket_client.py` + `simtalk_send.py` |
| `1` | `TIMEOUT`（在 `--timeout` 内未收到完整回复） | `socket_client.py` |
| `2` | `ERR: cannot connect` / 参数错误 | `socket_client.py` |
| `3` | `ERR: connection closed before reply` / 回包不是合法 JSON | `socket_client.py` |
| `10` | `simtalk_run` 编译错 / `result != "success"`（硬失败） | `simtalk_send.py` |
| `11` | `simtalk_run` Quirk #7 软失败（runtime exception） | `simtalk_send.py` |
| `12` | `simtalk_syntax` 语法失败 / 服务端回裸字符串 | `simtalk_send.py` |
| `20` | `readlog` 收到 result=success 但 ⚠️ v15+ 不可信 | `simtalk_send.py` |

---

## 四、跨 skill 反复出现的"高频坑 Top 10"

按踩坑频率 + 影响范围排序：

| 排名 | 坑 | 触发场景 | 修复 | 引用 skill |
|---|---|---|---|---|
| **1** | Quirk #7：`simtalk_run` runtime 异常返回 `result=success` | 所有跑代码的地方 | **必须 parse `log` 字段**，判据 `result=success AND not log.startswith("code execute failed")` | 所有 |
| **2** | Quirk #6：`simtalk_run` 的 `data` 字段永远空 | 想要返回值时 | 走 GUI Console 肉眼读 print；或 marker 模式从 readlog 抓 print 输出 | 所有 |
| **3** | v15 readlog 回归：readlog 不捕获 print + 65536 字节截断 + 反馈循环 | 任何依赖 readlog 取值的操作 | 用 marker 模式 + 单方法探针 + sleep | `read-library` / `get-class-inheritance` / `add-note-to-method` |
| **4** | Quirk #13：`type` 字段非白名单值让服务端静默挂死 | 自构造 JSON 时 | 用 `simtalk_send.py` argparse 子命令（强制白名单）或手工校验 | `local-simtalk-execution` |
| **5** | 模态陷阱：`prompt` / `infoBox(text, true)` / `promptList*` 永久阻塞 | 想"通知"或"取用户输入"时 | 用 `infoBox(text, false)` / 改 print / 改走 GUI 手工 | `local-simtalk-execution` |
| **6** | payload > 2KB 触发服务端 JSON parser 截断 | 写大 NOTE / 一次性 `obj.program :=` 大段 | 分块写（每块 ≤ 30 行 NOTE / ≤ 2 KB），用 `simtalk_send.py` 而非裸 `socket_client.py` | `add-note-to-method` / `write-simtalk` |
| **7** | NOTE 文本里的 `\` 被 quote() 双重转义后错位 | 注释里想写带引号的代码示例 | NOTE 里完全避免 `\`；要"双引号"语义直接写中文或单引号 | `add-note-to-method` |
| **8** | List API：`l.length` 不存在、`l := [1,2,3]` 不可赋 | 想拿 list 长度 / 构造 list | 用 `l.dim`；list 只能走 list-returning 函数（`getFilesOfFolder` / `makeList`） | `os-functions` / 所有用 list 的地方 |
| **9** | `Frame.NumChildren` **不数** placed-in-Frame 实例 | 想检查 Frame 是否放了对象 | 用 `Frame.extendPath(name) /= void` | `class-management` |
| **10** | argparse `nargs="+"` 不带 `action="append"` 覆盖 | 传多 `--note A --note B --note C` | 改用单 `--note A B C` | `add-note-to-method` / `write-simtalk` |

---

## 五、Plant Simulation 语言层的"小字面契约"

这些是反复被字面比较、踩坑、改错的"硬字面值"，**改任何一处都会破坏远程调用**：

| 字面契约 | 出处 | 踩坑案例 |
|---|---|---|
| `action_result["result"]` 的取值是小写 `"success"` / `"failed"` | `simtalk_hasError` 返回值契约 | `add-note` 多次写错成 `"Success"` → 远端拿不到 |
| log 前缀 `"code execute failed. error msg:..."`（注意开头无空格、句点+空格） | Quirk #7 检测字符串 | 改了大小写/标点会漏判 |
| 语法失败前缀 `" hasError "`（**有前导空格 + 全角冒号**） | `simtalk_syntax` 返回值契约 | "顺手 ASCII 化"破坏远程解析 |
| `hasSyntaxError` 必须挂在 `&Method` 上，不能对临时字符串检查 | Plant Simulation 文档 | `simtalk_hasError` 必须先把代码写到 `&simtalkcode.program` |
| `chr(10)` 是 newline，SimTalk **不**解释 `\n` 转义序列 | Quirk #1 | 写了字面 `\n` 当 newline → 服务端收到 `\` + `n` 两个字符 |
| `infoBox(text, false)` 第二参数是 `Modal` 标志 | Plant Simulation 文档 | 漏掉 `false` → 服务端挂死 |

---

## 六、跨 skill 工作流模板

### 6.1 标准"我要看 X 是什么"工作流

```bash
# 1. ping 探活
python3 skills/local-simtalk-execution/scripts/simtalk_send.py ping

# 2. (可选) 打开 infoBox 通知用户（按 v18 惯例）
python3 skills/local-simtalk-execution/scripts/simtalk_send.py --timeout 30 run \
  'infoBox("正在探查 <X>", false)'

# 3. 探针
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object := str_to_obj("<path>");
   print "###START###";
   print "PATH:" + obj_to_str(obj);
   print "NAME:" + obj.Name;
   print "TYPE:" + obj.InternalClassType;
   print "ORIGIN:" + obj_to_str(obj.Origin);
   print "CLASS:" + obj_to_str(obj.Class);
   print "NUMATTR:" + to_str(obj.NumAttr);
   print "NUMCHILD:" + to_str(obj.NumChildren);
   print "###END###"'

# 4. 收尾：infoBox 关闭 + ping 复测
python3 skills/local-simtalk-execution/scripts/simtalk_send.py --timeout 30 run \
  'infoBox("", false)'
python3 skills/local-simtalk-execution/scripts/simtalk_send.py ping
```

### 6.2 标准"我要写一段 SimTalk 到 Method"工作流

```bash
# 1. 备份原 program
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object := str_to_obj("<path>");
   print "###BACKUP_START###"; print obj.program; print "###BACKUP_END###"' \
  > backup.txt
# ↑ 把 readlog 输出里 ###BACKUP_START### 与 ###BACKUP_END### 之间的内容存盘

# 2. 构造新 program（NOTE + body），通过 quote() + chr(10) 拼接
# ↑ 必须保证每个 NOTE 行不含 \ 字符、整段包在 /* ... */ 里

# 3. 单次写（payload > 2KB 则分块）
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object := str_to_obj("<path>");
   obj.program := <拼接 RHS>;
   print "###WRITE_OK###"'

# 4. 验证（不依赖 readback 字节比较 —— v15 已废）
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object := str_to_obj("<path>");
   print simtalk_hasError(obj.program)'
# ↑ 期望输出 "has no Error"

# 5. 烟雾测试
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  '<obj>.execute(<legal smoke input>)'
```

### 6.3 标准"我想 dump 整个模型"工作流

```bash
# 1. 先抓 folder tree
python3 skills/local-simtalk-get-folder-tree/scripts/bfs_full.py \
  --no-infobox . <depth> /tmp/tree.json

# 2. 过滤目标路径（Method / Frame / Class 等）写到 paths.txt
python3 -c "
import json
t = json.load(open('/tmp/tree.json'))
out = []
def walk(n):
    if n.get('type') == 'Method': out.append(n['path'])
    for c in n.get('children', []): walk(c)
walk(t)
open('/tmp/paths.txt', 'w').write('\n'.join(sorted(set(out))) + '\n')
"

# 3. 批量 probe —— 注意 v15 readlog 截断：batch ≤ 8 + sleep 1.2 between batches
python3 skills/local-simtalk-read-library/scripts/probe_methods.py \
  --batch-size 8 --sleep 1.2 /tmp/paths.txt /tmp/methods.tsv

# 4. 渲染
python3 skills/local-simtalk-read-library/scripts/render_library.py \
  /tmp/methods.tsv /tmp/library_dump.json
```

---

## 七、Skill 调用的"哲学层"经验

不是文档抄来的，是 9 个 skill × 130+ session 的**反复实证**：

### 7.1 当上层 skill 失败时，先问"我是哪种失败"

```
症状                              → 真正原因
─────────────────────────────────────────────────────
exit=1 timeout                     → Quirk #13 (type 非法) 或 payload > 2KB
exit=2 connection refused          → host:port 错（WSL2 必须 host.docker.internal:50007）
exit=10 result=failed              → 真编译错（log 含 "Syntax error near line N"）
exit=11 result=success + log prefix "code execute failed" → Quirk #7 软失败（runtime 异常）
exit=12 hasError in result         → 真语法错（simtalk_syntax 路径）
exit=20 result=success             → readlog 收到但 v15+ 内容不可信
```

### 7.2 不要相信"自动化成功"

- **readlog v15 不可信**——别拿它当任何正式通道。
- **`simtalk_run` 返回 success 不等于代码执行成功**——必须双重判据。
- **argparse 默认 `nargs="+"` 不带 `action="append"`** 会静默丢行——必须看 `args.note` 实际值。
- **NOTE 写完别急着收尾**——`simtalk_hasError` 才是真正的语法通行证。

### 7.3 三层 fallback

1. **首选**：上层 skill（如 `add-note-to-method`、`write-simtalk`）。
2. **兜底**：`local-simtalk-execution` 直接跑原始 SimTalk + `obj.program :=` / `obj.attr :=`。
3. **最后**：去 Plant Simulation GUI 手工操作（drag-drop Frame 实例、Methods 编辑器、Console 读 print 值）。

### 7.4 当所有 skill 都说"这是用户干预"——就把它当用户干预

`simtalk_run` 的软失败设计是 SimtalkClaude 团队**有意为之**的：让 `result` 字段反映"代码编译并进入执行"，让 `log` 字段承担"运行时错误"。如果你看到 `result=success + log 前缀 "code execute failed"`，**不要怀疑协议**——按 Quirk #7 处理即可。详见 `memory/team/simtalk-run-soft-failure-design.md`。

---

## 八、可继续挖掘的方向（来自各 session 的"待补"清单合并）

| 主题 | 来源 session | 待办 |
|---|---|---|
| `sleep` 在 Method 上下文里的行为 | `os-functions/log/README.md` | 在真正 Method `m()` 里跑 `sleep(3.5, false)` + print |
| 3 个模态函数的 GUI 手动验证 | `os-functions/log/README.md` | GUI 端手动调 `browseForFolder` / `selectFileForOpen` / `selectFileForSave` 记录返回值 |
| `getRegistry` string / integer 分支 | `os-functions/log/README.md` | 测 `HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProductName` |
| `class_ops.py` 加 `classify` 子命令 | `class-management/log/session-20260826.md` Part E.3 | 打印 Origin/Class/OriginRoot/NumChildren + 标 class/instance |
| `class_ops.py duplicate` subcommand 文档化 | `class-management/log/session-20260826.md` Part E.5 | 把 Folder/Frame 两种 destination 行为写进 SKILL.md |
| `add_note.py` multi-line program 的 readback 修复 | `add-note-to-method/log/2026-08-26_m_paramRack_annotation.md` | 修复 `extract_between()` 的时间戳前缀 bug |
| `simtalk_send.py` 加 `--json-output` / `--quiet` / `batch` 子命令 | `local-simtalk-execution/log/test-session-20260825-v17.md` §11 | 三项非阻塞增强 |

---

## 九、本仓库 9 个 skill 的全景索引

| Skill | 主要 log/usage_log 文件 | 核心 session |
|---|---|---|
| `local-simtalk-execution` | `log/test-session-20260824-v1.md` ~ `log/test-session-20260825-v19.md`（19 个版本迭代） | v17（重构）+ v18/v19（业务函数族验证） |
| `local-simtalk-os-functions` | `log/README.md` + `log/test-session-20260825-v14~v17.md` | v14（20 函数实测）+ v17（list API 发现） |
| `local-simtalk-get-folder-tree` | `log/test-session-20260825-v1/v2/v3.md` | v3（45 round-trips + diff 基准） |
| `local-simtalk-get-class-inheritance` | `log/test-run-20260826-v1/v2.md` | v2（94 paths / 60 unique / 18 root / 42 derived） |
| `local-simtalk-read-library` | `log/test-session-20260826-v1.md` + `data/library_dump.json` | v1（27 methods dump） |
| `local-simtalk-class-management` | `log/session-20260826.md` + `log/derive-vs-duplicate.md` | session-20260826（4 bugs fixed + derive vs duplicate matrix） |
| `local-simtalk-add-note-to-method` | `log/2026-08-26_*.md`（5 个 annotation sessions） | simtalkclaude2_haserror_reannotation（2 KB chunked write + 113 行 NOTE） |
| `local-simtalk-write-simtalk` | `log/session-20260826.md` + `usage_log/` | session-20260826（2 bugs fixed + class_ops duplicate Frame 发现） |
| `local-simtalk-modify-object-attribute` | `log/01_*.log` ~ `log/80_*.log`（80 个细分 session）+ `log/SUMMARY.md` | SUMMARY.md Round 1+2（MaterialFlow 全覆盖 + Resources/InformationFlow） |

---

**总结**：9 个 skill、130+ session 反复验证同一件事——**Plant Simulation 的远程控制 80% 是传输层 Quirk、15% 是 SimTalk 字面契约、5% 才是领域知识**。先把传输层 Quirk 吃透（lifelines.md / Quirk #1-#13 / v15 readlog 回归），剩下 20% 的领域问题才值得花时间精雕。

---

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾，**不要修改主体**。
> 贡献流程、entry 字段格式、Supersede 模式见 [`CONTRIBUTING.md`](../../CONTRIBUTING.md)。

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-008]

### 2026-08-28 by @plant-simulation-expert — 2D 布局完成后必须做 pairwise bbox overlap check
- **症状**：把 34 个 Frame 子节点摆好后用 `kit.numNodes` + `ch.name` 列表"看上去都摆对了"，实际上 `LastSummary`（写入 "found=34 of 34" 后宽度从 2.69 → 6.19）已经和 `ErrorHistory` 重叠——只是 Frame 在 2D 视图里 overlap 不会触发任何错误，只会让用户看到图标互相压字。
- **根因**：`_3D.BoundingBoxSize` 是 content-dependent（见 `derived-methods-quirks.md §经验 Log`），布局 probe 完后写入报告字符串 → 报告 Variable 变宽 → 触碰邻居。所以 **布局完成 ≠ 无 overlap**，必须重新 probe 一次并跑 pairwise check。
- **Workaround / 结论** —— Pairwise 2D bbox overlap check 三步法：
  1. **Probe 阶段**（写报告前）：对每个 child 取 `ch._3D.Position` + `ch._3D.BoundingBoxSize`，写 `name|cx|cy|hw|hh|minx|maxx|miny|maxy` 表格到 `LastSummary`。
  2. **Overlap check**：561 对（34×33/2）跑 `(a.minx < b.maxx AND a.maxx > b.minx AND a.miny < b.maxy AND a.maxy > b.miny)` 计数。任何 >0 都报警。
  3. **Auto-clear 报告 Variable**（`LP/LE/LEC/LS`）：让 layout 回到 nominal 状态；这一步必须在 MLayout / probe Method 末尾就内嵌，不要寄望用户后续清理。
- **附加收益**：probe 阶段顺便暴露 icon 真实尺寸（Variable 空 / 80 字符宽度差 8.7 倍），后续重布局可以按 nominal 宽度设计坐标。
- **tags**：`layout`, `pairwise-check`, `2D-bbox`, `overlap`, `auto-clear`, `verifier`
- **see also**：`01-domain-concepts/derived-methods-quirks.md §经验 Log`（BoundingBoxSize content-dependent）；`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log`（json.dumps / simtalk_hasError）；`skills/local-simtalk-write-simtalk/log/2026-08-28_synctoolkit-frame-relayout.md §No-overlap relayout`（完整 561-pair check 输出）
- **反思**：用户眼睛能看出来 overlap 但 Plant Simulation 不会报错——verifier 不能省，且 verifier 必须在 layout **最后一次写入之后**跑（不是写入前 probe），否则测的是 nominal 状态而不是真实运行状态。

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-009]

### 2026-08-28 by @plant-simulation-expert — probe pipeline 在大模型上 3 个隐性 quirk
- **症状 1 (`render_library.py` RENDER-1)**:library dump JSON 里 `program` 字段只剩**首行注释**,但 `program_len` 是正确的完整长度 → 后续分析全错位。
- **症状 2 (`bfs_one_level.py` 大 Frame 截断)**:对 >~130 子节点的 Frame(如 Factory51 142 children),stdout JSON 在 ~12 KB 处被截断 → 缺失的 child 没人发现。
- **症状 3 (readlog v15+ batch degradation)**:连续发 `probe_methods.py` batch-8 时,前 17/25 抓干净,后 8 个 EnergyAnalyzer 方法 metadata 全空(META_TYPE=Method 但其他字段空白)→ 方法全空视图。
- **根因**:
  1. `probe_methods.py` 写 program body 用**真 newline**;`render_library.py` 用 `for ln in f: ln.split("\t")` 把每行当新 row → multi-line program 拆碎,只保留首注释。
  2. `bfs_one_level.py` 单 round-trip 用 `simtalk_run`(inline code),命中 v15+ readlog buffer ceiling(本文件 §四 Top 10)。
  3. v15+ readlog buffer 是按 statement 切片的;长 batch 的后段 metadata 在 buffer 重新分配时丢失。
- **Workaround / 结论**:
  1. **RENDER-1**:自定义 TSV re-parser(`/tmp/learning_library_full.json`),recognize header line(path + tab + name + tab + type + tab + ≥6 more tabs),accumulate body until next header。**Upstream 修法待提**:`probe_methods.py` 用 sentinel (`\x1e`) 替换 `\n` 后再写 TSV,renderer 还原;或整体改 quoted-CSV。
  2. **`bfs_one_level.py`**:改用 `bfs_full.py <path> 1 <out>.json`(depth-by-depth,每 round-trip ≤1 帧)避开 readlog ceiling。
  3. **readlog degradation**:batch 限制 ≤7 个方法;超出后改逐个 re-probe via `simtalk_send.py run` + readlog 提取(`/tmp/probe_with_log_capture.py`)。
  4. **re-parser 副作用**:`parse_analyzer_tsv.py` 会把空 row 附加到前一个 method → 修法:detect path-pattern 行(如 `.Models.`)即停积累。
- **tags**:`render_library`, `RENDER-1`, `bfs_one_level`, `readlog-v15-degradation`, `probe-pipeline`, `large-frame`, `multi-line-program`
- **see also**:本文件 §四 Top 10(readlog buffer ceiling);`skills/local-simtalk-get-folder-tree/log/2026-08-27_basis-depth4-full-and-factory51-types.md`(Factory51 142 children 截断案例);`skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-bottleneckAnalyzer-energyAnalyzer.md`(re-probe 工作流)
- **反思**:probe pipeline 是**默认信任链路**,但实际有 3 处会让 dump 看起来"成功"而内容破碎——**任何 library dump 后必须做完整性校验**(method count vs inventory、`program_len > 0` 占比、path 格式)。可考虑加 `library_dump_validator.py` 自动跑。
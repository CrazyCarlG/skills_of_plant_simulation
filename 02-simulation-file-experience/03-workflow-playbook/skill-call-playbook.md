---
last_updated: 2026-09-01
contributors: [@z004bjuu, @plant-simulation-expert, @plant-simulation-experience-curator]
scope: 9 个 `local-simtalk-*` 技能调用决策矩阵 + 写操作 5 步硬流程 + Top 10 高频坑 + 持久化硬规则 #9
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

> 完整 bash workflow 见 §6.1 "我要看 X 是什么"——marker 模式 `###START###` / `###END###` + readlog 提取是唯一可靠的"分隔 print 输出与 readlog 噪音"的手段（v15 readlog 截断会丢前文 → 必须 rsplit 取最后 marker 块）。

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

> **canonical home**：[`01-domain-concepts/derived-methods-quirks.md §一`](../01-domain-concepts/derived-methods-quirks.md) 集中维护所有 SimTalk 字面契约（含 `chr(10)` newline / `infoBox(text, false)` 模态标志 / `code execute failed` 前缀 / `hasError` 前导空格 等）。本节不再重复表格——改动请改那一份。

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

## 七、Skill 全景与"三步 fallback"

**三层 fallback**（所有 skill 撞墙时的统一应对）：

1. **首选**：上层 skill（如 `add-note-to-method`、`write-simtalk`、`modify-attribute`）。
2. **兜底**：`local-simtalk-execution` 直接跑原始 SimTalk + `obj.program :=` / `obj.attr :=`。
3. **最后**：去 Plant Simulation GUI 手工操作（drag-drop Frame 实例、Methods 编辑器、Console 读 print 值）。

> **9 个 skill 的全景索引**（log 路径 / 核心 session）见 [`02-bridge-tool/simtalkclaude-overview.md §支持动作`](../02-bridge-tool/simtalkclaude-overview.md)；本仓库 9 个 skill 的依赖关系图见 §一。

---

**总结**：9 个 skill、130+ session 反复验证同一件事——**Plant Simulation 的远程控制 80% 是传输层 Quirk、15% 是 SimTalk 字面契约、5% 才是领域知识**。先把传输层 Quirk 吃透（lifelines.md / Quirk #1-#13 / v15 readlog 回归），剩下 20% 的领域问题才值得花时间精雕。

---

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾，**不要修改主体**。
> 贡献流程、entry 字段格式、Supersede 模式见 [`CONTRIBUTING.md`](../../CONTRIBUTING.md)。

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-008]

### 2026-08-28 by @plant-simulation-expert — 2D 布局完成后必须做 pairwise bbox overlap check
→ 详见 [2026-08-28 by @plant-simulation-expert — 2D 布局完成后必须做 pairwise bbox overlap check.md](./2026-08-28%20by%20%40plant-simulation-expert%20%E2%80%94%202D%20%E5%B8%83%E5%B1%80%E5%AE%8C%E6%88%90%E5%90%8E%E5%BF%85%E9%A1%BB%E5%81%9A%20pairwise%20bbox%20overlap%20check.md)（tags: `layout`, `pairwise-check`, `2D-bbox`, `overlap`, `auto-clear`, `verifier`）

> [curator-audited 2026-08-28 by @plant-simulation-experience-curator — pre-curator entry; see `agents/curator-reports/2026-08-28-curator-report.md` audit-009]

### 2026-08-28 by @plant-simulation-expert — probe pipeline 在大模型上 3 个隐性 quirk
→ 详见 [2026-08-28 by @plant-simulation-expert — probe pipeline 在大模型上 3 个隐性 quirk.md](./2026-08-28%20by%20%40plant-simulation-expert%20%E2%80%94%20probe%20pipeline%20%E5%9C%A8%E5%A4%A7%E6%A8%A1%E5%9E%8B%E4%B8%8A%203%20%E4%B8%AA%E9%9A%90%E6%80%A7%20quirk.md)（tags: `render_library`, `RENDER-1`, `bfs_one_level`, `readlog-v15-degradation`, `probe-pipeline`, `large-frame`, `multi-line-program`）

### 2026-08-31 by @plant-simulation-experience-curator — "给非 Frame 对象加 method" 不走 `local-simtalk-create-method-object`；直接 `simtalk_run` + `createAttr` + `getAttribute`

→ 详见 [2026-08-31 by @plant-simulation-experience-curator — 给非 Frame 对象加 method 不走 local-simtalk-create-method-object.md](./2026-08-31%20by%20%40plant-simulation-experience-curator%20%E2%80%94%20%E7%BB%99%E9%9D%9E%20Frame%20%E5%AF%B9%E8%B1%A1%E5%8A%A0%20method%20%E4%B8%8D%E8%B5%B0%20local-simtalk-create-method-object.md)（tags: `skill-selection`, `createAttr`, `method-typed-UDA`, `station`, `cross-skill-workflow`, `frame-vs-non-frame`）

### 2026-09-01 by @plant-simulation-experience-curator — write 之后必须 readback `o.Program` 确认落盘(硬规则 #8 强化)

→ 详见 [2026-09-01 by @plant-simulation-experience-curator — write 之后必须 readback o.Program 确认落盘.md](./2026-09-01%20by%20%40plant-simulation-experience-curator%20%E2%80%94%20write%20%E4%B9%8B%E5%90%8E%E5%BF%85%E9%A1%BB%20readback%20o.Program%20%E7%A1%AE%E8%AE%A4%E8%90%BD%E7%9B%98.md)（tags: `write-verify`, `silent-failure`, `readback-Program`, `must-verify`, `write-simtalk-skill-bug`, `hard-rule-8`, `executeSilent-fresh-compile`）

### 2026-09-01 by @plant-simulation-experience-curator — `m.Program :=` 写入的方法 / 属性 **不持久化**:Plant Simulation 重启即丢,必须用户 GUI 导出 `.psfm`(硬规则 #9)

→ 详见 [2026-09-01 by @plant-simulation-experience-curator — m.Program 不持久化，PS 重启即丢必须 export .psfm.md](./2026-09-01%20by%20%40plant-simulation-experience-curator%20%E2%80%94%20m.Program%20%E4%B8%8D%E6%8C%81%E4%B9%85%E5%8C%96%EF%BC%8CPS%20%E9%87%8D%E5%90%AF%E5%8D%B3%E4%B8%A2%E5%BF%85%E9%A1%BB%20export%20.psfm.md)（tags: `persistence`, `m.Program-not-persistent`, `in-memory-vs-disk`, `psfm-export-required`, `bridge-no-save-action`, `restart-data-loss`, `workflow-mandatory-save`）
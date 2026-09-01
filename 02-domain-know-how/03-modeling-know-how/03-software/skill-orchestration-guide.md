---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: 9 个 local-simtalk-* skill 的依赖图 + 决策矩阵 + 写操作 5 步硬流程 + Top 10 高频坑
---

# Skill 编排与工作流指南

agent 调用 Plant Simulation 工具时的工作流、坑、决策矩阵。

## 一、9 个 skill 的依赖关系

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

**关键观察**:

1. **`local-simtalk-execution` 是唯一触达 Plant Simulation 进程的 skill**——其它 8 个都是它的"领域封装"。所以所有传输层 Quirk(v15 readlog 回归 / Quirk #6 / #7 / #13 / 模态陷阱)会 100% 渗透到上层 skill。
2. **当上层 skill 撞上未覆盖的边界,正确的 fallback 是"掉到 `local-simtalk-execution` 直接跑原始 SimTalk"**,不要硬在 skill 内部绕。
3. **`local-simtalk-read-library` 的产物(`data/library_dump.json`)会被多个下游 skill 引用**——它是后续 add-note / write-simtalk / class-management 的"前置语义地图"。

## 二、按操作类型分组的最佳实践

### 2.1 读操作 / Read

| Skill | 核心坑 | 解决方案 |
|---|---|---|
| `get-folder-tree` | 默认 depth 4 = 45 round-trips;depth 大了 server 端慢但 client 不会挂 | `--no-infobox` 模式批量跑 |
| `get-class-inheritance` | batch > 8 paths 触发 readlog 截断,3/8 batches 返 0 行 | 收紧到 ≤ 8 paths/batch 或加 inter-batch sleep 2 |
| `read-library` | BATCH=8 在小方法上够用;对内嵌多行字符串的方法会丢内容 | 单方法一次 + sleep(1.2) + readlog;或 marker 模式 `###PRG_START###` / `###PRG_END###` 抓 print 输出 |
| `modify-attribute` | `--read-only` 在 shell 循环里连发偶发 transient syntax-error | sleep 1 重试一次 |

### 2.2 写操作 / Write —— 5 步硬流程

```text
1. type-check        → str to obj(path) + print obj.internalclasstype  // 确认是 Method/Variable/...
2. backup            → print obj.program / obj.<attr> 写到 *.original.txt
3. compose           → quote(line) + chr(10) 串成 RHS  // 切勿用字面 "\n"
4. single-shot write → obj.program := <完整 RHS>
                       // 绝不"先写 NOTE 再 readback 再 append body" —— v15 readlog 已废
5. verify            → simtalk_hasError(obj.program) + obj.execute(smoke_payload)
   ⭐ step 5.5: readback `o.Program` 确认非空(硬规则 #8)
   ⭐ step 5.6: 用户 File → Save 持久化到 .psfm(硬规则 #9)
```

| Skill | 写操作专属坑 | 最佳实践 |
|---|---|---|
| `add-note-to-method` | payload > ~2KB → 服务端 JSON parser 截断 → "Unexpected end of string" | 分块写(NOTE 每块 ≤ 30 行 / ≤ 2 KB) |
| `add-note-to-method` | NOTE 文本里含 `\` → quote() 转义后 server 看到字面 `\\"` → 提前闭合字符串 | NOTE 里完全避免 `\` 字符;要"双引号"语义直接写中文或单引号 |
| `add-note-to-method` | NOTE 行 `--` 与裸 `===` 行混排 → SimTalk lexer 把 `==` 当 token 报 syntax error | 整段 NOTE 包在 `/* ... */` 块注释里 |
| `write-simtalk` | `add_note.py --note A --note B --note C` argparse `nargs="+"` 不带 `action="append"` → args.note 被覆盖 | 改用 `--note A B C D`(单 `--note` 多位置参数) |
| `write-simtalk` | `method`(小写)是 SimTalk 保留字,新建 Method 实例报 "Invalid identifier" | 改用 `Method`(大写 M,Frame 自带) |
| `write-simtalk` | `var p: object := str_to_obj(...); p.create(...)` → "Unknown identifier 'create'" | 走 `class_ops.py duplicate .InformationFlow.Method .Models.Model myMethod` |
| `modify-attribute` | `--batch` 模式 restore snippet 复用一个 `var o_: object := ...` 在同一作用域重声明 → `'o_' is already defined` | 后缀索引 `o_0`/`o_1`/`o_2` |
| `class-management` | `derive vs duplicate vs create` 三种语义混淆 | 见 §三.2 决策矩阵 |

### 2.3 通知与 UI / Notification

| 操作 | SimTalk 写法 | 是否安全 |
|---|---|---|
| 开始时通知 | `infoBox("<text>", false)` | ✅ 非模态 |
| 收尾关闭 | `infoBox("", false)` | ✅ 幂等 no-op |
| 防御性二次关闭 | `infoBox("", false)` ×2 | ✅ |
| 模态通知(禁忌) | `infoBox("<text>")` / `infoBox("<text>", true)` / `prompt(...)` / `promptList*(...)` | ❌ 永久阻塞服务端 |

## 三、决策矩阵

### 3.1 选哪个 skill?

| 用户意图 | 首选 skill | 兜底 skill(直接跑 SimTalk) |
|---|---|---|
| 检查这段 SimTalk 语法 | `local-simtalk-execution` (`syntax`) | — |
| 跑一段 SimTalk 拿结果 | `local-simtalk-execution` (`run`) | — |
| 想知道某对象的属性 | `local-simtalk-modify-attribute` (`--read-only`) | `local-simtalk-execution` + `str_to_obj` |
| 想改某个对象的非 program 属性 | `local-simtalk-modify-attribute` | `local-simtalk-execution` |
| 想给某个 Method 加注释 | `local-simtalk-add-note-to-method` | `local-simtalk-write-simtalk` |
| 想完全重写一个 Method | `local-simtalk-write-simtalk` | `local-simtalk-execution` + `obj.program :=` |
| 想列出模型结构(Frame / Folder / 类) | `local-simtalk-get-folder-tree` | — |
| 想看某个对象的继承链 | `local-simtalk-get-class-inheritance` | `local-simtalk-execution` + str_to_obj + print Origin/Class/OriginRoot |
| 想 dump 所有 Method 源码 | `local-simtalk-read-library` | `local-simtalk-execution` 单方法探针 |
| 想新建类 / 派生类 | `local-simtalk-class-management` (`derive`/`duplicate`) | `local-simtalk-execution` |
| 想新建 Method / Variable 实例 | `local-simtalk-class-management` (`duplicate` 到 Frame) | `local-simtalk-execution` + `<Class>.duplicate(frame, name)` |
| 想用 OS 函数(文件/注册表/进程/环境变量) | `local-simtalk-os-functions` | `local-simtalk-execution` |

### 3.2 `derive` vs `duplicate` vs `create`

| 想做的事 | 错的方式 | 对的方式 |
|---|---|---|
| 在 Class Library 加 Station 子类 | `duplicate(.Models, "MyStation")` → 得到**无父类独立副本** | `derive(.Models, "MyStation")` → 保留继承 |
| 把 Station 放进 Frame 当实例 | `cls.create(frame)` → "Unknown identifier 'create'"(Station 不是 MU) | `duplicate(.Models.Model, "Inst")` → 真正的实例 |
| 想同时派生 + 放进 Frame | `create(frame)` → 仍失败 | `derive(.Models.Model, "Inst")` 或 `duplicate(.Models.Model, "Inst")`(二者等价) |
| 想新建 Method 实例 | `p.create(frame)` → "Unknown identifier 'create'" | `local-simtalk-class-management duplicate .InformationFlow.Method .Models.Model myMethod` |
| 判断节点是不是类 vs 实例 | `NumChildren > 0` / `InternalClassType` | **`Origin == VOID AND Class == VOID` → 类;否则实例** |
| 设置实例 2D 位置 | `<obj>.setPosition := [100, 100]` → 编译错 | `<obj>.setPosition(100, 100)` → 方法调用 |

### 3.3 怎么判断"成功 vs 失败"?

| 请求类型 | 成功判据 | 失败判据 |
|---|---|---|
| `ping` | `result == "success"` | `result == "failed"` 或 socket timeout |
| `simtalk_syntax` | `"hasError" not in result`(即 `"has no Error"` 在 result 里) | result 含 `"hasError"` → 退出码 12 |
| `simtalk_run` 语法错 | `result == "failed"` + log 含 `Syntax error near line N` | **这是真失败**,不是软失败 |
| `simtalk_run` 运行时异常 | **仍然 `result == "success"`** + log 以 `code execute failed. error msg:...` 开头 | 这是 **Quirk #7 软失败** —— 必须 parse log |
| `simtalk_run` 真正成功 | `result == "success"` AND `not log.startswith("code execute failed")` | — |
| `readlog` v15+ | `result == "success"` 但 ⚠️ 内容不可信(可能反馈循环 / 截断) | 退出码 20 标 warning |

> **致命陷阱**:永远只看 `result == "success"` 就以为成功——这会漏掉 100% 的运行时异常(Quirk #7)。

### 3.4 退出码 / Exit Codes

| 退出码 | 含义 |
|---|---|
| `0` | 语义成功 |
| `1` | `TIMEOUT`(在大括号 timeout 内未收到完整回复) |
| `2` | `ERR: cannot connect` / 参数错误 |
| `3` | `ERR: connection closed before reply` / 回包不是合法 JSON |
| `10` | `simtalk_run` 编译错 / `result != "success"`(硬失败) |
| `11` | `simtalk_run` Quirk #7 软失败(runtime exception) |
| `12` | `simtalk_syntax` 语法失败 / 服务端回裸字符串 |
| `20` | `readlog` 收到 result=success 但 ⚠️ v15+ 不可信 |

## 四、跨 skill 反复出现的"高频坑 Top 10"

按踩坑频率 + 影响范围排序:

| 排名 | 坑 | 触发场景 | 修复 |
|---|---|---|---|
| **1** | Quirk #7:`simtalk_run` runtime 异常返回 `result=success` | 所有跑代码的地方 | **必须 parse `log` 字段**,判据 `result=success AND not log.startswith("code execute failed")` |
| **2** | Quirk #6:`simtalk_run` 的 `data` 字段永远空 | 想要返回值时 | 走 GUI Console 肉眼读 print;或 marker 模式从 readlog 抓 print 输出 |
| **3** | v15 readlog 回归:readlog 不捕获 print + 65536 字节截断 + 反馈循环 | 任何依赖 readlog 取值的操作 | 用 marker 模式 + 单方法探针 + sleep |
| **4** | Quirk #13:`type` 字段非白名单值让服务端静默挂死 | 自构造 JSON 时 | 用 `simtalk_send.py` argparse 子命令(强制白名单)或手工校验 |
| **5** | 模态陷阱:`prompt` / `infoBox(text, true)` / `promptList*` 永久阻塞 | 想"通知"或"取用户输入"时 | 用 `infoBox(text, false)` / 改 print / 改走 GUI 手工 |
| **6** | payload > 2KB 触发服务端 JSON parser 截断 | 写大 NOTE / 一次性 `obj.program :=` 大段 | 分块写(每块 ≤ 30 行 NOTE / ≤ 2 KB) |
| **7** | NOTE 文本里的 `\` 被 quote() 双重转义后错位 | 注释里想写带引号的代码示例 | NOTE 里完全避免 `\`;要"双引号"语义直接写中文或单引号 |
| **8** | List API:`l.length` 不存在、`l := [1,2,3]` 不可赋 | 想拿 list 长度 / 构造 list | 用 `l.dim`;list 只能走 list-returning 函数 |
| **9** | `Frame.NumChildren` **不数** placed-in-Frame 实例 | 想检查 Frame 是否放了对象 | 用 `Frame.extendPath(name) /= void` |
| **10** | argparse `nargs="+"` 不带 `action="append"` 覆盖 | 传多 `--note A --note B --note C` | 改用单 `--note A B C` |

## 五、跨 skill 工作流模板

### 5.1 标准"我要看 X 是什么"工作流

```bash
# 1. ping 探活
python3 skills/local-simtalk-execution/scripts/simtalk_send.py ping

# 2. (可选) 打开 infoBox 通知用户(按 v18 惯例)
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

# 4. 收尾:infoBox 关闭 + ping 复测
python3 skills/local-simtalk-execution/scripts/simtalk_send.py --timeout 30 run \
  'infoBox("", false)'
python3 skills/local-simtalk-execution/scripts/simtalk_send.py ping
```

### 5.2 标准"我要写一段 SimTalk 到 Method"工作流

```bash
# 1. 备份原 program
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object := str_to_obj("<path>");
   print "###BACKUP_START###"; print obj.program; print "###BACKUP_END###"' \
  > backup.txt

# 2. 构造新 program(NOTE + body),通过 quote() + chr(10) 拼接

# 3. 单次写(payload > 2KB 则分块)
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object := str_to_obj("<path>");
   obj.program := <拼接 RHS>;
   print "###WRITE_OK###"'

# 4. 验证(不依赖 readback 字节比较 —— v15 已废)
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  'var obj: object := str_to_obj("<path>");
   print simtalk_hasError(obj.program)'

# 5. ⭐ READBACK (硬规则 #8):print obj.program 确认非空源码

# 6. 烟雾测试
python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
  '<obj>.execute(<legal smoke input>)'

# 7. ⭐ 用户 GUI: File → Save 持久化到 .psfm (硬规则 #9)
```

## 六、Skill 全景与"三步 fallback"

**三层 fallback**(所有 skill 撞墙时的统一应对):

1. **首选**:上层 skill(如 `add-note-to-method`、`write-simtalk`、`modify-attribute`)
2. **兜底**:`local-simtalk-execution` 直接跑原始 SimTalk + `obj.program :=` / `obj.attr :=`
3. **最后**:去 Plant Simulation GUI 手工操作(drag-drop Frame 实例、Methods 编辑器、Console 读 print 值)

> **总结**:9 个 skill、130+ session 反复验证同一件事——**Plant Simulation 的远程控制 80% 是传输层 Quirk、15% 是 SimTalk 字面契约、5% 才是领域知识**。先把传输层 Quirk 吃透(Quirk #1-#13 / v15 readlog 回归),剩下 20% 的领域问题才值得花时间精雕。

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->
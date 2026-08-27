# Session Summary — `.ModelAssistants` 最佳实践学习

**Date:** 2026-08-27
**Agent:** plant-simulation-expert
**Duration:** ~30 min（接续 2026-08-27_session-summary_learn-modelassistants.md）
**Skills called:** `local-simtalk-read-library`（probe_methods.py 批量抓元数据 → 手动 42 次
sequential socket_client 抓全文，绕过 LIB-2 readlog buffer overflow）+ `local-simtalk-execution`
（infoBox 控制 / 链接探测）

## Goals

用户上一轮要求「请学习下 ModelAssistants」后定位并结构枚举了 `.ModelAssistants`。
本轮继续追问 **「请学习下这个模型的优秀经验」**——需要**读源码**，抽模式，写经验沉淀。

## What was done

1. **路径枚举完成**——67 个 method path 落盘至 `/tmp/modelassistants_method_paths.txt`。
2. **批量 probe 抓元数据**——用 `probe_methods.py` 一次跑 8 个，捕获 `methodName` /
   `objectClass` / `programLen` / `encrypted`。结果：41 个 "OK" + 26 个空 stub。
3. **LIB-2 readlog buffer overflow 绕过**——批量 probe 把 40/41 非空 method 的 program
   截到 60 char（只有 AIBot.M_Response 完整 1164 B 幸存）。改用 42 次 sequential
   socket_client 调用，每次只 probe 一个 method。**关键 fix**：`o.Program` 而不是
   `&o.Program`（后者触发「ref-operator has no effect in this context」运行期错误）。
4. **42 份完整源码落盘**至 `/tmp/modelassistants_sources/ModelAssistants_<Frame>_<Method>.simtalk`。
5. **逐 method 阅读**——重点看了 `Internal.autoexec/autoexecLoadObj/onCloseModel`、
   `AIBot.M_SetPyEnv/M_SendRequest/M_Response`、`ModelSyncCopy.M_ApplyFrame`（11 KB）、
   `M_SetObjectAttribute`、`Assistants.M_AddUserMenu/M_CallInternalMethod/M_CreateIcon`、
   `AutoSave.AutoSaveModel/MSaveModel`、`ClassAssistant.AutoSorter/AddNewModel`、
   `QuickArrayTool.ArrayObjects`（3.3 KB 三轴阵列生成）、`FrameEncrypt.EncryptFrame`、
   `FrameReplacer.replaceObject` 等。
6. **三份经验文档落盘**到 `02-simulation-file-experience/modelassistants/`：
   - `README.md`（索引 + 一句话总结）
   - `architecture-overview.md`（架构总览 + 11 Frame 职责表 + lifecycle triple）
   - `best-practices.md`（**核心：12 条可复用 SimTalk 模式**）
   - `mscf-v2-protocol.md`（MSCF v2 私有协议完整规范）
7. **本 session summary** 写入（per 🔴 铁律❸）。

## Key findings / decisions

### 12 条 Siemens SimTalk 风格（best-practices.md）

1. **防御式参数校验**——method 开头 3 行 if（来自 `M_AddUserMenu` 等）
2. **9 字段 doc header**——Function/Parameter/Return/Called/Call/Date/Programmer
3. **Tab ↔ List 互转**——`copyFromTableColumn` 是 O(n) 内部优化
4. **`param := default`**——API 友好
5. **显式 type switch**——`setAttribute` 重载需要 switch 分发
6. **三态 sentinel switch**——`-1` = ignore, `else` = debug
7. **`current.LastSummary` scratch variable**——借 Variable 中转 string 给 silent program
8. **Dialog 回调触发副作用**——`Dialog.callback("Apply")` 走对话框事件链
9. **Clipboard 图标三步走**——`putIconToClipboard` + `existsIcon` 检查 + `setCurrIconFromClipboard`
10. **`while + sleep(sec, False)`**——后台守护；`True` 是同步陷阱
11. **`isComputerAccessPermitted` 守门**——任何写盘 / 启进程 method 必须先查
12. **`incl(prefix, str, pos)`**——就地插入函数，比字符串拼接快且可读

### MSCF v2 协议（mscf-v2-protocol.md）

- **5-pass scan 重建 Frame 子树**：F → S/O → A/P → G/W → C（顺序严格，pass 4 需要 pass 2 完成）
- **9 种 record 类型** + `classScope` (`R`/abs) + `refScope` (`S`/`R`/abs) + `isUser` (`"1"`/`"0"`)
- **pathMap** 是 sourceRel → destPath 的运行时映射，pass 1 创建，pass 2-5 共用
- **OnCollision 三策略**：`"skip"` / `"rename"`（`_N` 后缀） / default（`deleteObject` 覆盖）
  → **默认覆盖是最大破坏性隐患**
- **M_Encode / M_Decode** 字符串转义（用户字段里的 chr(1)/chr(2) 必须先转义）
- **MSCF v2 ≠ SimtalkClaude 协议**——前者是「建模工具传输层」，后者是「agent RPC 层」

### 架构核心模式

- **Lifecycle triple**：`autoexec` + `autoexecLoadObj` + `onCloseModel` 是 Siemens Frame bundle
  标准结构；agent 实现 Frame bundle 自动接入就照抄这三个 hook
- **工具 vs 数据二分**：method 应该是纯函数（输入参数 + current + 数据 Variable）；对象
  应该挂在 Frame 上当持久数据
- **Templates 空 method**——9 字段 doc header 充当 copy-paste 模板（建模师新建 method
  时把头拷过去填）
- **Commented-code preservation**——`/*...end*/` 注释旧代码保留作为历史演进痕迹
- **「空 stub 但 encrypted=false」**——33 个 method 是 `program_len=0` 但未加密，意味
  着原厂预留了接口位置但没有实现（agent 可作为扩展点）
- **IsContiuned typo**——原厂变量名拼错了（应是 IsContinued），沿用别改

### 库/用法陷阱（agent 启示）

- **跳过 readlog v15+ 批量 probe**——`local-simtalk-read-library` 的 LIB-2 quirk 让
  `readlog` 在一次性累积多 method 后只保留最后几条；逐 method sequential socket_client
  调用才能拿到完整 program
- **`&o.Program` 是 false friend**——SKILL.md 文档说能用，实际触发 ref-operator 错误；
  `o.Program` 才正确
- **使用 `str_to_obj(...).deleteObject` 前必须确认路径存在**——`existsObject(path)`
  是真守卫；但 `existsObject(to_str(...))` 当 path 含 void 时会返回 true（陷阱）
- **`bfs_one_level.py --no-infobox`** 不自动开/关 infoBox——agent 需要手动 wrap
  `simtalk_send run 'infoBox(...)'`

## Cross-references

- `02-simulation-file-experience/modelassistants/README.md` —— 索引
- `02-simulation-file-experience/modelassistants/architecture-overview.md` —— 架构总览
- `02-simulation-file-experience/modelassistants/best-practices.md` —— **核心：12 条模式**
- `02-simulation-file-experience/modelassistants/mscf-v2-protocol.md` —— MSCF v2 规范
- `02-simulation-file-experience/simtalkclaude-best-practices.md` —— 平行对比（agent RPC）
- `02-simulation-file-experience/facory51/simtalkclaude-v2-vs-v1.md` —— SimtalkClaude v1/v2 差异
- `03-agent-memory/plant-simulation-expert-memory/2026-08-27_session-summary_learn-modelassistants.md`
  —— 上一轮结构枚举总结（定位 + BFS）
- `skills/local-simtalk-get-folder-tree/log/2026-08-27_bfs-modelassistants-live.md` —— BFS 原始数据
- `/tmp/modelassistants_sources/` —— 42 份 Siemens method 完整源码（agent 可 grep）
- `/tmp/modelassistants_method_paths.txt` —— 67 个 method 路径清单
- `/tmp/modelassistants_library_dump.json` —— 批量 probe 元数据 dump

## Open questions / next steps

1. **8 个未深读 Frame**——`ClassAttrDepulicator`, `Calculator3D`, `FrameEncrypt`
   的其他 method, `Namer.exchangeTabRow` 的细节还没看。下一轮如需要可以补全。
2. **MSCF v2 在 SimtalkClaude 上能否桥接**？理论可以——把 SimtalkClaude 的 JSON-line
   payload 改写成 MSCF v2 即可驱动 ModelSyncCopy。但这是双层封装，**不推荐**——直接走
   SimtalkClaude 自己的 SimTalk 执行更简单。
3. **`AIBot` 是否预连接某个 LLM provider**？`PythonDLLPath` 是空 Variable，需要用户
   自己配置；Siemens 没硬编码任何 provider URL。这是**好消息**——agent 可以塞自己的
   API key 到 `PythonDLLPath` 旁的 Variable 复用 AIBot 框架。
4. **`Templates` Method 是否还有其他用途**？目前看是空 doc header。可能是原厂留给建模
   师 copy-paste 的占位符——确认需不需要在 Plant Simulation 启动时打印「copy-paste 提示」。
5. **`ClassAttrDepulicator.M_DuplicateObjectAttributes`** 命名是 `M_*` 前缀但又是
   transform method——和 `M_Response` / `M_SendRequest` 的命名约定（命令动词）不同，
   **疑似老旧 method 没改名**。可作为命名一致性的改进建议。
6. **`Internal.Socket`** 仍然未解——为什么 utility bundle 里挂个 Socket 对象？是 PS 内部
   IPC 还是某个被遗忘的功能？
7. **是否要把这 4 份经验文档同步到 `/root/knowledge_of_plant_simulation/`**？
   目前只在本仓库落盘（per 🔴 铁律❺）。
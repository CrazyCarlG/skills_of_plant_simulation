---
name: simtalk-os-functions
description: Plant Simulation SimTalk 预定义操作系统函数的参考与测试助手，覆盖 20 个 OS 相关函数（availableMemory / copyFile / SHGetKnownFolderPath / startExtProc / system / sleep 等）。当用户想了解某个 OS 函数怎么用、签名是什么、实际返回值类型，或者想在本地 Plant Simulation 进程上验证某个 OS 函数的真实行为时使用。触发场景包括："getFilesOfFolder 怎么用"、"SHGetKnownFolderPath 的 CLSID 怎么填"、"system() 返回什么"、"如何拿到 PID"、"read 注册表"、"复制到剪贴板"、"sleep 在 SimTalk 里怎么写"。本技能只覆盖 OS 相关函数；其它 SimTalk 预定义函数不在此列。
---

# simtalk-os-functions

Plant Simulation SimTalk 提供 20 个**预定义操作系统函数**，用于在控制逻辑里访问 Windows 系统的能力（内存 / 进程 / 目录 / 环境变量 / 注册表 / 文件 / 剪贴板 / 外部进程 / 系统命令 / 运行控制）。本技能把官方文档 `01-plant-simulation-knowledge/.../operating-system/operating-system.md` 整理成可查询的参考，并提供经过本地 Plant Simulation 实测验证的**真实返回值**（v14 测试）。

> 本技能**不**直接执行 SimTalk——它依赖 `local-simtalk-execution` 把代码送到本机/局域网的 Plant Simulation 进程并拿回真实执行结果。

## 工作前提 / Prerequisites

- 已安装 `local-simtalk-execution` skill（提供 `socket_client.py` / `simtalk_syntax` / `simtalk_run` / `readlog`）。
- 已有一台本机/局域网可达的 Plant Simulation 进程，TCP 50007 端口可连接。
- `scripts/` 目录下的辅助脚本可执行。

## 何时使用 / When to Use

- 用户问"SimTalk 里怎么读注册表 / 拿 PID / 复制文件到剪贴板"
- 用户问"这个 OS 函数的签名 / 返回类型 / 参数怎么填"
- 用户想**实测**某个 OS 函数在自己 Plant Simulation 上的行为（拿到真实返回值，不只是 doc string）
- 用户在 SimTalk 代码里调用了某个 OS 函数，遇到奇怪行为想确认"它真的返回这个吗"

不要使用：

- 用户问的是 SimTalk 语言语法 / 面向对象 / 流程控制 —— 这是 SimTalk 通用问题，不属于 OS 函数范畴
- 用户问的是 Plant Simulation GUI 操作 —— 这是 GUI 工具范畴
- 用户只是想在本地 Plant Simulation 上跑任意 SimTalk —— 用 `local-simtalk-execution` 即可，不需要本技能

## 任务流程 / Workflow

1. **查 reference**——在 `references/functions.md` 找到目标函数：
   - 函数签名（`→` 后是返回类型）
   - 参数列表（含可选参数）
   - v14 实测返回的真实值
   - 使用注意事项（受 "Allow access to the computer" 约束 / 模态 / Method-only 等）

2. **判断能否在 socket 端验证**：
   - 非模态、无 Method-only 限制 —— ✅ 可以直接 `simtalk_run` 实测
   - 模态（`browseForFolder` / `selectFileForOpen` / `selectFileForSave`） —— ❌ 跳到 step 3（看文档即可）
   - Method-only（`sleep`） —— ❌ 跳过，参见 `references/quirks.md` Quirk #7

3. **用 `local-simtalk-execution` 跑一遍**——按 `references/test-cookbook.md` 的模板构造 `simtalk_run` 请求，把目标函数放到 `simtalk_code` 里：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host host.docker.internal --port 50007 \
     --data '{"type":"simtalk_run","action_id":"<id>","simtalk_code":"print getFilesOfFolder(\"C:\\\\Windows\\\\*.exe\")[1]"}||END||' \
     --resp-mode delimiter --resp-delimiter '||END||'
   ```

4. **拉 readlog 拿 print 实际值**（v13+）——socket 端**第一次**能拿到 `print(...)` 表达式求值后的真实字符串：
   ```bash
   python3 skills/local-simtalk-execution/scripts/socket_client.py \
     --host host.docker.internal --port 50007 \
     --data '{"type":"readlog","action_id":"<id>"}||END||' \
     --resp-mode delimiter --resp-delimiter '||END||'
   ```
   回包 `log` 字段里 `YYYY-MM-DD HH:MM:SS: <text>` 格式的行就是 print 输出。详见 `references/test-cookbook.md` 的"取 print 实际值的标准流程"。

5. **解读**——把 readlog 的 print 输出对照 v14 实测表（在 `references/functions.md` 每个函数条目下），确认行为是否一致。

## 关键文件 / Key Files

- `references/functions.md`：20 个函数的合并参考——签名 / 参数 / 返回类型 / v14 实测值 / 使用注意
- `references/test-cookbook.md`：用 `local-simtalk-execution` 实测每个函数的 recipe + 取 print 实际值的标准流程
- `references/v14-findings.md`：v14 测试发现的 6 条新发现（`print <list>` 行为、SHGetKnownFolderPath CLSID 格式、getRegistry VOID 字面量、setCodePage 返回前值、startExtProc PID、system 退出码）
- `references/quirks.md`：与 OS 函数相关的服务端 quirks（Quirk #6 `data` 字段恒空、Quirk #7 sleep Method-only、Quirk #8 模态陷阱、Quirk #11/#12 readlog 修复历史）
- `references/safety-and-prerequisites.md`：哪些函数需要"Allow access to the computer"模型设置才能跑
- `log/README.md`：测试日志存放位置 + 已完成的测试 session 索引

## Logging / 日志

每次调用本技能 **必须** 在 `log/` 下新建一个日志文件,禁止追加到已有日志,每次调用一个新文件。文件名格式:

```
<YYYY-MM-DD>-<agent>-<topic>.md
```

- `<agent>` 是调用方 agent 的 kebab-case 形式,默认为 `plant-simulation-expert`。
- `<topic>` 是 kebab-case slug(≤ 5 个英文词),描述这次调用做了什么。本技能的示例: `verify-getfilesoffolder-on-c-windows`。
- 同一天多次调用:在 `.md` 前加 `-2`、`-3` 等后缀。
- 不要重命名或移动已存在的日志文件(老的 `YYYY-MM-DD_<topic-slug>.md` 是历史记录)。

完整的 schema(frontmatter 字段、必填段落、verdict 规则):见 `log/CONTRIBUTING.md`。

## 知识库路径 / Knowledge Paths

本技能整合自：

- 官方文档：`01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/predefined-functions-i-os-math-string-datetime/operating-system/operating-system.md`（与 `operating-system.txtx` 内容一致）
- 实测日志：`skills/local-simtalk-execution/log/test-session-20260825-v14.md`（20 个函数的本地 Plant Simulation 实测，2026-08-25）
- 协议基础：`skills/local-simtalk-execution/references/message-schema.md`、`code-templates.md`、`workflow.md`
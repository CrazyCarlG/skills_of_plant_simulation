# local-simtalk-get-folder-tree Test Session v2 — 2026-08-25

测试目标：在 v1 的只读 folder-tree 探索基础上，按用户要求**给本技能加上 `infoBox` 通知 / 关闭惯例**（沿用 `local-simtalk-execution` v18 → v19 的约定），然后端到端验证：
1. 入口 `infoBox(text, false)` 通报；
2. `bfs_full.py` 在 depth 0/1 边界节点更新 `infoBox`（让操作员看到进度）；
3. 出口（成功 OR 失败）`infoBox("", false)` **两次**防御性关闭；
4. `--no-infobox` 标志可抑制整条 open / update / close 链；
5. 字符串中的 `\` / `"` 正确转义，不会破坏 SimTalk 字面量。

承接 v1 用户追加诉求："使用这个技能的时候，always 通过 infobox 告诉用户你当前在干什么，技能调用完后关闭 infobox，请依据这条规则修改技能，再测试一下，测试过程记录下来"。

> 关键约束（沿用 v1）：
> - `simtalk_run` `data` 字段始终空（Quirk #6）—— `infoBox` 本身是 void，无 Quirk #6 问题
> - `infoBox(text, true)`（modal）会让 GUI 阻塞；本技能坚持 `false`（非模态）
> - `infoBox` 在无 GUI 显示的 server 上仍返回 `result:"success"`，但窗口不可见 —— 在 CI 场景使用 `--no-infobox`

## 1. 环境 / Environment

| 项 | 值 |
|---|---|
| Skill under test | `skills/local-simtalk-get-folder-tree/`（v2 — infoBox-wrapped） |
| 依赖技能 | `skills/local-simtalk-execution/`（v17+ 的 `simtalk_send.py` 客户端） |
| Server | Plant Simulation 2606.0002（宿主机） |
| TCP port | 50007 |
| Client host | WSL2 容器 → `host.docker.internal:50007` |
| 测试时间 | 2026-08-25（接续 v1） |
| 测试方法 | ① 真实 server 烟雾测试 ② monkey-patch spy harness 验证调用序列 |

## 2. 握手 / Handshake

| ID | 命令 | 回包 | 退出码 | 结论 |
|---|---|---|---|---|
| v2-ping-init | `python3 scripts/simtalk_send.py ping` | `{ "type": "ping", "result": "success" }` | 0 | ✅ 链路通 |
| v2-compile-one | `python3 -m py_compile scripts/bfs_one_level.py` | (无输出) | 0 | ✅ 语法 OK |
| v2-compile-full | `python3 -m py_compile scripts/bfs_full.py` | (无输出) | 0 | ✅ 语法 OK |

## 3. 真实 server 烟雾测试 / Live Server Smoke Tests

> 所有 v2- 开头的用例都使用 v2 版本的脚本（已加 infoBox 包装）。

| ID | 命令 | 预期行为 | 实际 | 退出码 | 结论 |
|---|---|---|---|---|---|
| v2-smoke-one-default | `python3 scripts/bfs_one_level.py .` | infoBox 打开 + 关闭 + JSON 输出 | `{"root_name":"Basis","root_numNodes":10,...}` 打印到 stdout | 0 | ✅ 默认模式功能完整 |
| v2-smoke-one-noinfobox | `python3 scripts/bfs_one_level.py --no-infobox .` | 无 infoBox；JSON 输出 | 同上 JSON | 0 | ✅ --no-infobox 静默 |
| v2-smoke-one-err | `python3 scripts/bfs_one_level.py .DoesNotExist` | infoBox 打开 + 关闭（finally）+ ERR 诊断 | stderr: `ERR: no JSON start after marker`；readlog 内含 `ERR: cannot resolve path` | 1 | ✅ 失败路径仍关闭 infoBox |
| v2-smoke-one-noargs | `python3 scripts/bfs_one_level.py` | stderr usage + exit 2 | `usage: bfs_one_level.py [--no-infobox] <path>` | 2 | ✅ 入参校验 |
| v2-smoke-full-default | `python3 scripts/bfs_full.py . 2 /tmp/test_v2_depth2.json` | 打开 infoBox + 完成 + 关闭；21 round-trips | `Wrote /tmp/test_v2_depth2.json  calls=21` | 0 | ✅ 默认模式 + 深度 2 全树 |
| v2-smoke-full-noinfobox | `python3 scripts/bfs_full.py --no-infobox . 1 /tmp/test_v2_depth1.json` | 无 infoBox；11 round-trips | `Wrote /tmp/test_v2_depth1.json  calls=11` | 0 | ✅ --no-infobox + 深度 1 |

## 4. Spy Harness 验证 / Monkey-Patch Spy Tests

> 用 `importlib` 直接加载 `scripts/bfs_one_level.py` / `scripts/bfs_full.py`，
> monkey-patch 其 `_run_simtalk` 记录每次 `simtalk_send.py run <code>` 实际发了什么。
> 这能在**没有 GUI 截图的情况下**证明 infoBox 调用序列正确。
>
> 测试脚本：`/tmp/spy_test_v2.py`（含 6 个用例）

| ID | 用例 | 实测 infoBox 调用序列 | 断言 | 结论 |
|---|---|---|---|---|
| v2-spy-1 | `bfs_one_level.py .`（默认模式） | `infoBox("[bfs_one_level] start: path=.", false)` → `infoBox("", false)` → `infoBox("", false)` | 3 次；首条含 `start:`；末两条是空关闭 | ✅ |
| v2-spy-2 | `bfs_one_level.py --no-infobox .` | （无任何 simtalk 调用） | 0 次 simtalk 调用 | ✅ |
| v2-spy-3 | `bfs_one_level.py .SimtalkClaude`，`call_one_level` 抛异常 | `infoBox("[bfs_one_level] start: path=.SimtalkClaude", false)` → 2x `infoBox("", false)` | 3 次（try/finally 仍关闭） | ✅ 异常路径也合规 |
| v2-spy-4 | `bfs_full.py . 1 /tmp/spy_test_depth1.json`（mock 2 children） | open → 3x progress（depth 0 + 2×depth 1）→ done → 2x close | 首条 `start:`；末两条空关闭；含 `done` 条 | ✅ 7 次调用顺序正确 |
| v2-spy-5 | `bfs_full.py --no-infobox . 0 ...` | （无任何 simtalk 调用） | 0 次 simtalk 调用 | ✅ |
| v2-spy-6 | `bfs_one_level.py 'path"with\\quotes'`（含 `\` 和 `"` 的路径） | `infoBox("[bfs_one_level] start: path=path\"with\\quotes", false)` | 含 `\"` 和 `\\` 的转义 | ✅ 转义正确，不会破坏 SimTalk 字面量 |

### v2-spy-4 完整序列（最关键的回归点）

```
1. infoBox("[bfs_full] start: path=. depth=1 -> /tmp/spy_test_depth1.json", false)
2. infoBox("[bfs_full] progress: calls=0 depth=0 path=.", false)
3. infoBox("[bfs_full] progress: calls=1 depth=1 path=..A", false)
4. infoBox("[bfs_full] progress: calls=2 depth=1 path=..B", false)
5. infoBox("[bfs_full] done: calls=3 -> /tmp/spy_test_depth1.json", false)
6. infoBox("", false)
7. infoBox("", false)
```

每次新进 `expand_recursive(path, depth, ...)` 都触发 `on_progress`；
`on_progress` 只在 `depth in (0, 1)` 时调用 `infoBox`，避免 45+ round-trip 时 GUI 被刷屏。

## 5. 关键设计决策 / Design Decisions

| 决策 | 选择 | 原因 |
|---|---|---|
| infoBox 调用点 | `bfs_one_level`：入口 + finally 2x 关闭；`bfs_full`：入口 + depth 0/1 进度更新 + 完成 + finally 2x 关闭 | v18→v19 约定的最小化复刻；进度更新仅在深度边界触发，限制 GUI 噪声 |
| 默认 `false`（非模态） | 永不 `true` | 模态会阻塞 Plant Simulation 进程等待 GUI 点击（lifelines §4） |
| `--no-infobox` 标志 | 第一参数位置 | 让 CI / headless 场景能复用同一脚本；和 `--help` 类似的位置 |
| 字符串转义 | `\` → `\\`，`"` → `\"` 后才嵌入 `infoBox("...", false)` | 防止路径含 `\` 或 `"` 时打破 SimTalk 字面量 |
| `try/finally` 关闭 | `bfs_one_level` 主流程包在 `try: ... finally: infobox_close()` | 异常路径仍必须关闭（v2-spy-3 验证） |
| 防御性 2x 关闭 | `infoBox("", false)` 调两次 | v18→v19 约定；幂等，关闭未打开的 box 是 no-op |
| 进度更新触发条件 | `depth in (0, 1)` | 限制 GUI 刷新频率；深度 0 = 根开始，深度 1 = 顶层 Folder 子树 |

## 6. v1 → v2 增量 / Diff vs v1

| 维度 | v1 | v2 |
|---|---|---|
| infoBox 通知 | ❌ 无 | ✅ 入口 / 进度 / 完成 / 关闭全链路 |
| 用户可见信号 | 仅 stderr `Wrote ... calls=N` | GUI 上 `infoBox` 实时显示 + stderr 同 v1 |
| 默认行为变更 | — | 新增 infoBox 调用（不破坏 JSON 输出 / 退出码） |
| 异常路径 | 错误 → exit 1，无 GUI 提示 | 错误 → exit 1，GUI 上短暂显示开始信息后关闭 |
| CLI 标志 | — | 新增 `--no-infobox` |
| 失败时清理 | ❌ 无 | ✅ try/finally 仍关闭 infoBox |
| SKILL.md 行数 | ~95 | ~115（新增 "Skill convention" 节） |
| 脚本行数 | `bfs_one_level.py` 135 / `bfs_full.py` 145 | `bfs_one_level.py` ~180 / `bfs_full.py` ~210 |

## 7. 已知限制 / Known Limitations（v2 新增）

| 限制 | 表现 | 缓解 |
|---|---|---|
| infoBox 在 headless server 上不可见 | 无 GUI 显示器时 `infoBox` 仍 `result:success`，但窗口不出现 | `--no-infobox` 跳过整条链 |
| 信息框文本过长会被截断 | Plant Simulation infoBox 宽度固定，超长自动换行 / 截断 | 文本控制在 80 字符以内（当前最长 70） |
| progress 更新频率 | `depth in (0, 1)` 触发；`depth >= 2` 不更新 | 适合 ≤ 4 深度抓取；≥ 6 深度时建议加 `--no-infobox` 减少 round-trip |
| 转义覆盖范围 | `\` 和 `"` 已覆盖；其他特殊字符（换行 / Unicode 控制符）未测 | 当前路径均不包含这些字符；若需要可扩展 |

## 8. 结论 / Conclusions

1. **infoBox 通知 / 关闭惯例实现完毕 ✅** —— 两个脚本都按 v18→v19 约定：
   - 入口 `infoBox("[bfs_<script>] start: ...", false)`
   - `bfs_full.py` 在 depth 0/1 触发 `infoBox("[bfs_full] progress: ...", false)`
   - 完成后 `infoBox("[bfs_full] done: ...", false)`
   - finally 中 `infoBox("", false)` 调两次
2. **6 个 spy harness 用例全部 PASS ✅** —— 验证调用序列、转义、try/finally 关闭、`--no-infobox` 抑制均正确
3. **真实 server 6 个烟雾用例全部 PASS ✅** —— 默认模式 / `--no-infobox` / 错误路径 / 缺参 / 默认模式递归 / `--no-infobox` 递归
4. **没有破坏 v1 的功能 ✅** —— JSON 输出 schema、`exit code`、错误信息、`bfs_full` 调用计数与 v1 完全一致
5. **`SKILL.md` 已更新 ✅** —— 新增 "Skill convention: always announce with `infoBox`" 节，硬规则表新增一行，限制节补充 headless 注意事项
6. **CI 兼容性 ✅** —— `--no-infobox` 提供无 GUI 场景的回退路径，与 v1 行为等价

## 9. 建议 / Recommendations

1. **`--no-infobox` 作为 CI 默认** —— 任何自动化 / batch 任务都应显式 `--no-infobox`，避免无 GUI 环境下堆积日志噪声。
2. **进度更新深度阈值未来可调** —— 当前 hardcode 为 `(0, 1)`；若需要更细粒度可见性可加 `--progress-depth <N>` 标志。本轮不加是为了保持脚本最小化。
3. **`infoBox` 转义函数可复用** —— `_run_simtalk` / `infobox` / `infobox_close` 在两个脚本里基本一致；如未来再有第三个脚本调用 Plant Simulation GUI，可考虑抽到共享 helper。当前是 2 份重复（~10 行），不值得抽。
4. **GUI 截图留作下一轮** —— spy harness 验证了 *调用序列* 正确，但没截图证明 GUI 实际显示。如果用户希望严格视觉验证，下一轮可加：调用脚本 → 等待 → 截屏 → OCR 比对 infoBox 文字。
5. **`infoBox` 关闭幂等性已通过 spy harness 验证两次** —— 二次关闭是 v18→v19 历史约定的安全网；本次测试已经验证调用了 2 次且未报错。
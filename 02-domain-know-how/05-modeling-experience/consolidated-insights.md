---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: 从 14 篇 session summary 中提炼的跨 session 高频主题与核心教训(2026-08-27 ~ 2026-09-01)
---

# 跨 Session 洞察与核心教训

本文档从 14 篇 session summary 中提炼出 **跨 session 反复出现的主题** 与 **核心教训**,作为高频模式的"摘要层"。

## 一、Plant Simulation 远程控制 80% 是传输层 Quirk

> "Plant Simulation 的远程控制 80% 是传输层 Quirk、15% 是 SimTalk 字面契约、5% 才是领域知识。先把传输层 Quirk 吃透,剩下 20% 的领域问题才值得花时间精雕。"
> —— [`skill-orchestration-guide.md`](../../03-modeling-know-how/03-software/skill-orchestration-guide.md) §六总结

14 篇 session 中 11 篇涉及传输层问题(readlog v15+ 退化、bridge lock 卡死、write_simtalk silent fail 等)。

## 二、5 大高频主题(按 session 出现频率排序)

### 主题 1:write 操作 silent failure 模式(5 篇 session 涉及)

| Session | 发现 |
|---|---|
| 2026-08-31_create-agv-claude-library | 首次发现 `write_simtalk [verify] OK` ≠ 落盘 |
| 2026-09-01_agv-claude-recovery-prep | 7 method 全部 `program_len:0` —— **silent fail 实锤** |
| 2026-09-01_agv-claude-v2-recovery | 必须 readback `o.Program` 确认非空(硬规则 #8) |
| 2026-09-01_agv-claude-v2-wrap | `.execute()` 不刷 `.Program` 缓存 —— close+reopen model 才能验证 |
| 2026-08-28_synctoolkit-foundation | `simtalk_run` 不能捕获返回值 + m.Program 不持久化 |

**核心教训**:

- **任何 write 操作完成后,必须 readback `o.Program` 确认非空**(硬规则 #8)
- **`write_simtalk [verify] OK` 是 silent failure**——见 `skill-orchestration-guide.md §2.2`
- **`m.Program :=` 不持久化**——bridge 写入只改 in-memory state,PS 重启即丢(必须 GUI File → Save)
- **`.execute()` 跑的是首次编译的旧版本**——close+reopen model 才能用新 `.Program`

### 主题 2:TCP / Bridge 卡死(4 篇 session 涉及)

| Session | 发现 |
|---|---|
| 2026-08-27_astar-challenge | Bridge + SimTalk 死循环耦合,只能 PS 重启恢复 |
| 2026-08-27_verify-9-skills | `bfs_one_level.py` 在 encrypted-method 屏障下 server 返 partial log |
| 2026-08-31_replicate-source-to-target | `bfs_full.py` 硬编码 50007 + target 50010 readlog frozen |
| 2026-09-01_agv-claude-recovery-prep | 大 batch probe 后服务端 JSON 层卡死(accept OK,handler 不回) |

**核心教训**:

- **bridge 卡死后不要盲目重试**——直接说明需要重启 Plant Simulation + 重建方法
- **大 batch 间必须插 ping**——把"长时间无 JSON 回包"作为触发停手的信号
- **TCP 连着 ≠ 桥活着**:accept() 工作不代表 handler 没卡死
- **TCP 服务端口可手动 rebind**——`mySocket.create("<port>")` 是 user-editable Variable
- **必须 wide-scan 端口**——任何"假设 server 在 50007"的 agent 都是 fragile 的

### 主题 3:SimTalk 字面契约与易踩坑(6 篇 session 涉及)

| Session | 发现 |
|---|---|
| 2026-08-27_astar-challenge | `table[T,V]` v15+ 运行期只读 + `make_array` 不存在 |
| 2026-08-31_create-agv-claude-library | 10 个 SimTalk 坑(`var x:object` ERR / `setSize` 已废 / `--` 注释行 让 argparse 终止等) |
| 2026-09-01_agv-claude-v2-recovery | `var x:table; x := str_to_obj(...)` 必须前置 `param` 声明;`length()` 不是函数 |
| 2026-09-01_agv-claude-v2-wrap | DataTable 必须用 `MaxYDim/MaxXDim` 属性;`make2DimArray` 第二参必须 1D |
| 2026-08-28_synctoolkit-foundation | `_3D.BoundingBoxSize` 是 content-dependent |
| 2026-08-27_session-summary | `bfs_one_level.py` 在 >130 子节点 stdout JSON 截断 |

**核心教训**:

- **`var x : any`** ——避开 `var x : object`(SYNTAX ERROR)
- **DataTable resize**:`MaxYDim :=` / `MaxXDim :=`(属性赋值),**不是** `setSize`(方法调用,已废)
- **字符串永远走 `strLen(s)`** —— 不要相信"string `.length` works"的旧记忆
- **DataTable 0×0 表写 cell**:"Access beyond list dimensions",**没有** auto-grow
- **不要链式 `.~.~.~.~...`** —— SimTalk 不接受链式深度属性访问
- **`--` 注释行让 `write_simtalk --code-file` argparse 终止** —— 必须 `grep -v ^--` 过滤

### 主题 4:模型切换与"先 BFS 再决策"(3 篇 session 涉及)

| Session | 发现 |
|---|---|
| 2026-08-27_learn-teaching-model | 当日第 3 次换模型 → 必须先 `bfs_full.py depth=1 of .` 确认加载的是哪个模型 |
| 2026-08-27_learn-new-assembly-model | depth=1 BFS 看到 `Tools` + 顶层 `ExperimentManager` Variable,无 `ApplicationObjects.HBW3D.*` → 确认非 Factory51 |
| 2026-08-27_learn-factory51-model | bfs_one_level 在 >130 子节点 stdout JSON 截断 → 用 bfs_full 替代 |

**核心教训**:

- **每个 session 第一动作**:`bfs_full.py . 1 /tmp/root_d1.json` 确认模型身份
- **廉价且权威**——depth=1 几十 round-trips 就能区分 Factory51 / assembly-line / teaching / custom

### 主题 5:写操作 5 步硬流程的强化演进(4 篇 session 涉及)

```
# 原始 5 步(2026-08-27 ~ 2026-08-28)
1. type-check        → str_to_obj + InternalClassType
2. backup            → print obj.program
3. compose           → quote(line) + chr(10) 串成 RHS
4. single-shot write → obj.program := <RHS>
5. verify            → simtalk_hasError + obj.execute(smoke_payload)

# 强化后(2026-09-01 之后)
5.5 readback o.Program 确认非空 (硬规则 #8)
5.6 用户 GUI File → Save 持久化 .psfm (硬规则 #9)
```

详见 [`skill-orchestration-guide.md`](../../03-modeling-know-how/03-software/skill-orchestration-guide.md) §2.2。

## 三、跨模型模式沉淀

14 篇 session 中,有 **4 个真实模型** 被深度学习,沉淀到 [`../../01-factory-know-how/`](../../01-factory-know-how/) 与 [`../../04-modeling-example/`](../../04-modeling-example/):

| 模型 | Sessions | 沉淀到 |
|---|---|---|
| **Factory51** | 2(离线 + TCP) | `01-factory-know-how/factory51/` |
| **assembly-line** | 1 + 1 addendum | `04-modeling-example/assembly-line-patterns.md` |
| **P4_CTU** | 2(实现 + verify) | `01-factory-know-how/ctu-warehouse/` |
| **MaterialFlow_AGV + AGV_Claude** | 4(learn + create + recovery + v2 wrap) | `04-modeling-example/vendor-library-extension.md` |

## 四、8 个"踩过的坑一次也不要再踩"的硬规则

按 session 反复验证频率排序:

1. **`simtalk_run` 软失败契约**(Quirk #7)——必须 parse `log` 字段,不要只看 `result`
2. **`.execute()` 不刷 `.Program` 缓存**——验证新 program 必须 close+reopen model
3. **`write_simtalk [verify] OK` ≠ 落盘**——必须 readback `o.Program`
4. **`m.Program :=` 不持久化**——bridge 写入只改 in-memory state
5. **TCP 端口可手动 rebind**——必须 wide-scan,不要假设 50007
6. **大 batch 间必须插 ping**——避免 server JSON 层卡死
7. **`var x : object` 是 SYNTAX ERROR**——必须用 `var x : any`
8. **`--` 注释行让 argparse 终止**——必须 `grep -v ^--` 过滤

## 五、推荐的 agent 冷启动流程

```
1. Read 02-domain-know-how/README.md (总入口)
2. Read 03-modeling-know-how/{01-objects,02-simtalk,03-software}/README.md
3. Read 02-simtalkclaude-knowhow/README.md
4. Read 05-modeling-experience/consolidated-insights.md (本文)
5. Read 05-modeling-experience/skill-test-coverage-matrix.md (skill 验证基线)
6. 按当前任务匹配的主题目录,深读对应文件
7. 仅当需要"决策上下文"时才打开 session-summaries/ 具体某篇

# 9 个 skill / 14 篇 session / 48 个文件 → 7 篇 README + 5 篇主体文档 (本目录入口)
```

## 经验 Log

> 本节是 **append-only** 时间线——新发现直接追加在末尾。

<!-- 暂无 entry——首个 entry 由下次踩坑时 append -->
</content>
</invoke>
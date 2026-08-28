# Session Summary — A* 通用图搜索挑战(`.P4_CTU.ctux1_agvx1.A_Star`)
**Date:** 2026-08-27  **Agent:** plant-simulation-expert
**Duration:** ~50 min(含 ~20 min 桥卡死 + 4 版本迭代 + 32 块 chunked-write)
**Skills called:** local-simtalk-execution(仅 `simtalk_send.py` + `simtalk_hasError` + `readlog`)

## 02-bridge-tool
- 桥 + SimTalk 死循环**耦合**:socket 超时杀不掉死循环进程,bridge 进入半死状态,后续 stall → **唯一可靠恢复:重启 Plant Simulation**(副作用:所有自定义方法丢失,需重建)→ 团队记忆 `memory/team/bridge-infinite-loop-safety.md`
- chunked-write 协议:~900B/chunk,每块必须 `readlog` 看 marker,**不能只信 `result: success`** → `02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log`(json.dumps antipattern)
- Bridge 调用必须**双层 timeout**:`simtalk_send.py --timeout N` + 外层 `subprocess.run(..., timeout=N+5)`
- `simtalk_hasError(s)` 是发送前廉价预检(可拦大部分语法错)

## 01-domain-concepts
- `table[T,V]` v15+ **运行期只读**——`table.append`/`delete` 语法接受、编译过,**运行期**返回 `Unknown identifier` → 用平行 `list[T]` + `list[V]` + 线性扫描模拟 hashmap → 团队记忆 `memory/team/simtalk-runtime-constraints.md`
- `pi` 是 SimTalk 保留常量,任何变量名 `pi` 编译拒(本次未实际踩到,从通用知识库借)
- **"编译通过 ≠ 运行通过"** 是本环境最大元教训:每步"以为成功"必须有独立成功信号(chunked-write 必须 readlog marker、method existence probe 必须验证、demo 必须看 print/log)

## 03-workflow-playbook
- 图搜索 while 循环必须显式处理"openSet 非空但全在 closed 内"边界——`picked: boolean` flag 哨兵,扫到末位仍未 picked → `return empty`(等价于 lazy-Dijkstra 的 OPEN-as-unvisited-inv 终止条件)
- 独立 verification agent 的价值在 **adversarial 设计**,不在"再跑一遍"——必加自环 / 孤立起点 / start==goal / 空图 case,才能区分"测试集恰好没覆盖"vs"真修了 bug"

## Cross-references
- per-skill logs: 本次未生成独立 usage log(verdict 步骤直接嵌入 session 流程)
- 02-simulation-file-experience entries: 团队记忆 `memory/team/{simtalk-runtime-constraints,bridge-infinite-loop-safety}.md`(源头);本次发现的算法/桥 pattern **建议下次沉淀**到 `02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log` 或新建 `02-bridge-tool/nontrivial-algorithm-patterns.md`
- A* v4 源码: `/tmp/_astar_code_v4.txt`(已随 /tmp 清理,下次需重建)

## Open questions / next steps
- 本次 `.P4_CTU.A_Star` 在当前 PS 进程里 — **建议用户立即 export `.P4_CTU.psfm`**
- 大图(>100 节点)线性扫描 map 退化;若要扩展考虑 A* 启发式 + 平行 list heap 模拟
- 通用 SimTalk 算法套路(table 只读 / chunked-write / 桥卡死 / picked 哨兵)建议沉淀一篇 `02-simulation-file-experience/02-bridge-tool/nontrivial-algorithm-patterns.md`

### 2026-09-01 by @plant-simulation-experience-curator — Bridge JSON 层在大 batch probe 后卡死;TCP accept 仍工作但所有 ping/run/readlog 无 JSON 回包

- **症状**:跑完 `read_library.py` 的 14 batch × 8 paths 大批量探针后,服务端 TCP `host.docker.internal:50007` 仍显示 `CONNECTED`(accept() 工作),但任何后续 `simtalk_send.py ping` / `simtalk_send.py run <...>` / `simtalk_send.py readlog` / `bfs_full.py ...` 全部:
  - `EXIT=1`(timeout)
  - 或 "JSON decode error"(server 返回非合法 JSON)
  - 或纯 hang(无 stdout/stderr,直到 `--timeout` 触发)
  服务端 `handler` 不再回包,但进程没崩。
- **根因**(best guess,需复测):Bridge 的 server-side handler (`SimtalkAction.Run_Simutalk` 等) 可能持有一把**未释放的 lock**——大 batch probe 之间没有 "release" 步骤,导致后续请求卡在等锁。Socket 还在 accept,所以 TCP 层 `connect` 看似 OK,但 handler 进入"等待自己"的 deadlock。
- **Workaround / 结论**:

  ```bash
  # 1. 立刻停手,不要 retry(死循环只会卡更死)
  # Hard Rule #1: 大 batch 出问题时不要盲目重试

  # 2. Mitigation A: 在 batch 之间插 ping 保持 channel
  python3 skills/local-simtalk-execution/scripts/simtalk_send.py ping
  # 然后跑下一 batch

  # 3. Mitigation B: 调长 timeout(默认 10s → 30s)
  python3 skills/local-simtalk-execution/scripts/simtalk_send.py --timeout 30 run '<sim>'

  # 4. Mitigation C: 调 Server.Reconnect 弹 socket(需要 SimTalkClaude server 暴露这个 API)
  python3 skills/local-simtalk-execution/scripts/simtalk_send.py run \
    '.SimtalkClaude.Server.Reconnect'   # 或类似 — 视 server 实现

  # 5. 终极方案:用户手动重启 Plant Simulation server
  #    - .SimtalkClaude2 Frame → init → start → 等 "Server listening on 50007"
  #    - 这是 100% 可靠但需要 GUI 操作
  ```

  **判定**:
  - TCP `CONNECTED` 但所有 simtalk_send EXIT=1 / JSON decode error → bridge JSON 层卡死
  - 看到 `Unknown identifier` / `Method not found` 等正常错误 → 不是卡死,是普通 fail
  - 看到 "Server has been shut down" / "Connection closed" → TCP 真的断了(不同情况)

- **tags**:`bridge-json-hang`, `tcp-accept-but-no-reply`, `lock-not-released`, `large-batch-trigger`, `silent-failure-mode-6`, `mitigation-required`
- **see also**:`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log entry 2026-08-28 (Bridge + SimTalk 死循环)`(相关:死循环卡死 = method 进入 infinite loop;本条 = bridge handler 卡死 = 大 batch 触发);`skills/local-simtalk-execution/references/lifelines.md §Quirk #13`(type 白名单外的 type 让服务端静默挂死到 timeout;本条类似但 trigger 是 batch size);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-recovery-prep.md` §Key findings 2;`skills/local-simtalk-execution/log/2026-09-01_agv-claude-recovery-prep.md` Step 5-9

> 这条经验教会我:
> - **"TCP 连着 ≠ 桥活着"**:accept() 工作不代表 handler 没卡死。下次 batch 大小 = 14 × 8 = 112 paths 这种规模,务必在 batch 间插 ping——把"长时间无 JSON 回包"作为触发停手的信号,而不是 "看到 CONNECTED 就以为活着"。
> - **大 batch 的隐藏成本**:虽然单 batch `simtalk_run` 都成功,但 server-side handler 累积状态。**任何"批跑工具"(bfs_full / probe_methods / read_library)都应该在 batch 间留窗口**——这是工具设计需要改进的地方,不只是 user 应急。
> - **与 lifelines Quirk #13 区分**:Quirk #13 是 `type` 字段非法直接挂死;本条是 `type` 合法但 handler lock 未释放。两者表现都是 "timeout",但根因 + mitigation 不同——**两者都需要新 Quirk #N**(quarantine 给 skills-optimizer)。
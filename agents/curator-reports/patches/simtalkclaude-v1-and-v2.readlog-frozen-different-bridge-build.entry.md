### 2026-09-01 by @plant-simulation-experience-curator — 不同 Plant Simulation 实例的 SimtalkClaude bridge build 可能不同,导致 readlog buffer 行为不一致;目标端 state 读回必须走 simtalk_run error 通道

- **症状**:在 `host:50010`(target PS 实例,用户加载的"空白"模型)上跑:
  ```bash
  python3 simtalk_send.py --port 50010 run 'print "hello world test marker 12345"'
  # → result: success
  python3 simtalk_send.py --port 50010 readlog
  # → 返回 715 字节固定窗口,内容是**早期** print 输出,**新 print 不出现**
  ```
  对比:同样 `print "..."` 在 `host:50007`(source PS 实例)上跑 `readlog` 正常返回新 print。
  - 两个 instance 都报 Plant Simulation 相同版本 `2606.0002`
  - 区别在**两个 instance 加载的 SimtalkClaude bridge build 不同**(用户 target 用的可能是旧 bridge 或 build 时未 enable 完整 protocol)
- **根因**(best guess,需复测):
  - target instance 的 bridge `m_str_send` / `RxBuffer` flush 机制不完整(readlog buffer ceiling 715 字节 = 早期某版本的 hard cap)
  - 或 readlog 的 handler 还在用旧的 print-buffer 而不是 scratch-buffer(参 `02-bridge-tool/simtalkclaude-protocol.md §4.1 scratch buffer pattern`)
  - PS 端 simtalk_run **确实执行了 print**(返回 success),只是 readlog 的采集端不刷新
- **Workaround / 结论**:

  ```bash
  # 1. 在 target 上做 state read-back:不要用 readlog,改用 simtalk_run error 通道
  python3 simtalk_send.py --port 50010 run '
    var obj : any := str_to_obj(".X");
    print "###MARKER###";
    print "NAME=" + obj.Name;
    print "TYPE=" + obj.InternalClassType;
    print "###END###"
  '
  ```

  **判定**(在 multi-bridge / multi-instance 场景):
  - simtalk_run 返 `result: success` 但 `readlog` 不动 → readlog broken,改用 simtalk_run error/scratch channel
  - simtalk_run 返 `result: failed` 且 `log` 以 `code execute failed` 开头 → 真 runtime error,正常路径
  - simtalk_run 返 `result: success` 且 `log` 以 `execute success` 开头 → 跑成功,**用 readlog 拿 print**(默认路径)
  - **target PS 实例的 readlog 一定先 verify 一次再依赖**

- **tags**:`multi-bridge`, `bridge-build-divergence`, `readlog-frozen`, `715-byte-window`, `state-readback-fallback`, `simtalk-run-error-channel`, `silent-failure-mode-9`, `inter-instance-non-uniform`
- **see also**:`simtalkclaude-v1-and-v2.md §经验 Log entry 2026-08-28 (Bridge + SimTalk 死循环)`;`simtalkclaude-v1-and-v2.md §经验 Log exp-007 (Bridge JSON 层在大 batch probe 后卡死)`;`simtalkclaude-v1-and-v2.md §经验 Log exp-010 (port-can-be-rebound)`;`02-bridge-tool/simtalkclaude-protocol.md §4.1 scratch buffer pattern`;`03-agent-memory/plant-simulation-expert-memory/2026-08-31_session-summary_replicate-source-to-target.md` Finding 3

> 这条经验教会我:
> - **"同一 Plant Simulation 版本" ≠ "同一 bridge 行为"**:bridge 是 plant simulation 上层的 Frame + Methods 集合,不同 instance 加载的 bridge 可能 build 不同。
> - **多 instance 场景的工作流硬规则**:在写"我要从 instance A 读 + 写到 instance B"的工具前,**两边都要跑 ping + 单 print + readlog 三件套 verify**。
> - **state read-back fallback 必须是 layer 1,不是 layer 3**:(1) readlog;(2) simtalk_run log 字段;(3) 通过 `simtalk_run 'dest := "<value>"'` 写 var 再读;(4) GUI 手工。
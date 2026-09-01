### 2026-09-01 by @plant-simulation-experience-curator — TCP 服务端口可手动 rebind(50007 → 50009);agents 必须扫/验证端口,不能假设默认 50007

- **症状**:
  - `simtalk_send.py ping` 默认 `--port 50007` 一直 EXIT=1 / timeout
  - 但 TCP `netstat -tlnp` 显示 50007 是 LISTEN——bridge accept 工作
  - 进一步 wide-scan 发现 50009 才是真正"活的"服务端口(50007 是 zombie: accept 但 handler 不回)
  - 任何 hardcode `--port 50007` 的 skill(`bfs_full.py` / `write_simtalk.py` / `add_note.py`)在用户切端口后全部失败
- **根因**:Plant Simulation 端 `.SimtalkClaude2` Frame 的 init 代码里 `mySocket.create("<port>")` 是 user-editable Variable。用户(或维护脚本)改了这个 Variable 就改了监听端口。Server 端没有"必须 50007"的硬约束——这是协议 **soft default**,不是 spec。
- **Workaround / 结论**:

  ```bash
  # 1. 启动时 wide-scan,不要假设 50007
  for port in 50001 50005 50007 50008 50009 50010; do
      python3 skills/local-simtalk-execution/scripts/simtalk_send.py --port $port ping 2>&1 | head -1
  done
  # 找到 "result: success" 那个 port = 真活端口

  # 2. 写 ~/.claude/ports.env 或 SKILL 上下文里 export SIMTALK_PORT=<discovered_port>
  export SIMTALK_PORT=50009
  # 让所有 simtalk_send 调用读这个 env

  # 3. skill 层:让 simtalk_send.py 默认读 SIMTALK_PORT 环境变量,fallback 到 50007
  # (修 SKILL.md + scripts/simtalk_send.py — quarantine 给 skills-optimizer)
  ```

  **判定**:
  - `simtalk_send.py ping` timeout → 检查 `--host` (默认 `host.docker.internal`?);再 wide-scan port
  - 看到 "Server has been shut down" → 端口对但 server 真的关了(不是 zombie)
  - 看到 "Connection refused" → 端口没监听(走 wide-scan)
  - 看到 TCP accept OK 但所有 simtalk_call timeout → zombie port(本条 quirk)

- **tags**:`tcp-port`, `port-rebind`, `50007-default`, `50009-actual`, `wide-scan-required`, `env-variable-needed`, `skill-hardcode-bug`, `silent-failure-mode-7`
- **see also**:`02-bridge-tool/simtalkclaude-protocol.md §3.1`(帧格式)+ `simtalkclaude-overview.md §支持动作`(skill 与默认 port 的约定);`skills/local-simtalk-execution/references/lifelines.md §1 连接目标`(默认 50007 + host.docker.internal);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings "TCP 探测顺序很关键";`03-agent-memory/plant-simulation-expert-memory/2026-08-31_session-summary_replicate-source-to-target.md` Finding #2(bfs_full.py 硬编码 50007 早报)

> 这条经验教会我:
> - **"默认 50007" 是约定不是协议**:任何 "我假设 server 在这个端口" 的 agent 都是 fragile 的——server 端可以改,改完 agent 静默失败。**唯一可靠 = 启动时 wide-scan**。
> - **多 skill 共享一个 hardcode port 是 anti-pattern**:`bfs_full.py` + `write_simtalk.py` + `add_note.py` 都各自硬编码 50007——任一 server 改 port,所有 skill 全错。**正确架构 = 全部读 `SIMTALK_PORT` env variable,fallback 50007**——这是 skills-optimizer 应该修的地方。
> - **wide-scan 是值得脚本化的 agent 工具**:`skills/local-simtalk-execution/scripts/` 应该有 `scan_port.py` 一键扫 50000-50100 找活端口。**当前没有 → quarantine 给 skills-optimizer 起草一个**。
---
last_updated: 2026-09-10
dimension: 01-skill-experience
source_sessions:
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-02_session-summary_port-50008-model-structure.md
  - 04-agent-memory/plant-simulation-expert-memory/2026-08-31_session-summary_replicate-source-to-target.md
  - 04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-recovery-prep.md
  - 04-agent-memory/student-memory/2026-09-07-Python_GA_Demo-jobsshop-ga-integration.md
skills_touched: [local-simtalk-get-folder-tree, local-simtalk-write-simtalk, local-simtalk-execution]
models_touched: [AGV_Claude, AGV_Claude_v2, Python_GA_Demo, Factory51]
---

# `bfs_*.py` / `write_simtalk.py` 硬编码 50007,多 server 场景全部打错目标

## 症状
- `local-simtalk-get-folder-tree` 的 `bfs_one_level.py` / `bfs_full.py` 子进程调用 `simtalk_send` 时**不带 `--port`/`--host`**,默认打 `50007`。
- `local-simtalk-write-simtalk` 的 `write_simtalk.py` 同样硬编码。
- 用户明确指定 port 50008 / 50009 / 50010 → skill 仍写默认 50007,导致:
  - **致命**:复制操作打到 source 而不是 target(08-31 session,两棵树 md5 完全相同)
  - **致命**:read-back 显示 7 method 空 body,误以为"silent failure",实际是写到了**另一台** server
  - **中等**:50007 port 被用户重定向到 50009 后(09-01),skill 默认 50007 不通 → 卡死
  - **次要**:student 在 Python_GA_Demo 上被 cp1252 trap 阻断 skill 路径,降级 direct socket 时绕开该问题
- 跨 ≥5 个 session 复现,跨 3+ 个 skill。

## 根因
- skill 子脚本的 `subprocess.run` 调用 `simtalk_send` 时未传 `--port` / `--host` 顶层参数(也不读 `SIMTALK_HOST/PORT` 环境变量)。
- `simtalk_send` 的 `--port` 必须在**子命令前**(顶层),不在 `run`/`syntax`/`ping` 子命令后。
- skill 设计者假设"单 server = 50007"成立,但实际多 server 并存是高频场景(50007 主 + 50008/50009 备份/实验)。

## Workaround / 结论
- **绕过姿势**(curator 用过的):复用 SKILL.md 里的 `SIMTALK_TEMPLATE` + 显式 `simtalk_send --port <N>`,写到 `/tmp/bfs_one_level_<port>.py`。
- **走 socket 直连**:student 在 cp1252 trap 时降级到 `04-agent-memory/student-memory/.tmp_socket2.py`,`json.dumps(..., ensure_ascii=False) + END_DELIM`,完全绕开 simtalk_send 子进程。
- **CLI 顺序**:`--host --port --timeout` 必须在**子命令前**(顶层),不是子命令后(实测踩坑)。
- **写后 readback 必须带正确 port**:任何 write 操作后 readback `o.Program` 确认非空,且 readback 的 socket 必须指向**同一 server**。

## see also
- `04-agent-memory/plant-simulation-expert-memory/2026-08-31_session-summary_replicate-source-to-target.md Critical finding #2`(早前已发现,但没修)
- `04-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-recovery-prep.md Key findings`(server lock 卡死)
- `@skills-optimizer 评审项`:
  - `local-simtalk-get-folder-tree/SKILL.md` 加 `--host`/`--port` 顶层参数
  - `local-simtalk-write-simtalk/SKILL.md` 同样
  - `local-simtalk-execution/SKILL.md` lifelines §5 加 cp1252 trap 通道化(走 direct socket 替代子进程)
  - `simtalk_send.py` CLI 顺序在 SKILL.md 标注

## 反思
这是"单 server 假设"类设计缺陷的典型 — 现实里多 server 并存是常态,但 skill 默认值锁死第一个 server,导致跨 server 操作全部打到错误目标。

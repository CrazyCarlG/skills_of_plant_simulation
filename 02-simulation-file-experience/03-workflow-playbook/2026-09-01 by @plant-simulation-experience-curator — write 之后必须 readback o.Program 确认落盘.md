### 2026-09-01 by @plant-simulation-experience-curator — write 之后必须 readback `o.Program` 确认落盘(硬规则 #8 强化)

> **Per CONTRIBUTING §6 强制 per-entry file**——本 entry 不嵌在 `skill-call-playbook.md §经验 Log`,独立成文件。
>
> 命名 / URL 编码规则:
> - 文件名:`2026-09-01 by @plant-simulation-experience-curator — write 之后必须 readback o.Program 确认落盘.md`
> - 空格 → `%20`,`@` → `%40`,`—` → `%E2%80%94`

---

- **症状**:`local-simtalk-write-simtalk`(或 `add_note.py` / `write_astart.py` 等任何"写 .Program"的工具)返回 `[verify] method executes OK after edit` 日志,但 readback `o.Program` 时发现 `program_len:0, program:""`(本次 `.AGV_Claude` 7 method 案例:08-31 session 报"全部 7/7 [verify] OK" → 09-01 read_library 看到全空,silent failure)。
- **根因**:`write_simtalk.py` 的 verify 步骤调 `m.execute(<smoke_input>)` —— 但 **`.execute()` 不刷新 `.Program` 编译缓存**(见 `simtalkclaude-v1-and-v2.md §经验 Log` exp-005)。所以 verify 跑的是首次编译的版本(可能是空、可能是上次版本),与刚写入的 `.Program` 无关。"OK" 只能证明"method object 存在 + 首次编译成功",不能证明"写入成功"。

  **核心差距**:**write 操作 ≠ verify 操作**。write 改 `.Program` attribute;verify 看 `.execute()` 行为。两者中间没有任何 "readback .Program 看是否非空" 的步骤——这是 skill 设计的盲区。

- **Workaround / 结论**:

  ```bash
  # canonical "write → verify" 流程(在现有 5 步硬流程基础上加 step 4.5)
  # 1. backup: simtalk_run '<obj>.Program' → 存盘 backup.txt
  # 2. compose: quote(line) + chr(10) 串成 RHS
  # 3. single-shot write: simtalk_run '<obj>.Program := <RHS>'
  # 4. verify-syntax: simtalk_hasError(<obj>.Program)  ← 不依赖 .execute()
  # 5. ⭐ READBACK (硬规则 #8): simtalk_run 'print <obj>.Program' → 必须看到非空源码
  # 6. functional-test: 用 executeSilent(<obj>.Program) 跑(永远 fresh compile,绕开缓存)
  ```

  **简化为单条命令**:
  ```bash
  # 一次性:write + syntax check + readback
  python3 skills/local-simtalk-execution/scripts/simtalk_send.py run '
    var m : any := str_to_obj("<path>");
    m.Program := "<new body>" + chr(10) + "...";
    print "###WRITE_OK_LEN=" + to_str(strLen(m.Program)) + "###"
  '
  # 期望:stdout 含 "###WRITE_OK_LEN=<positive number>###"
  # 若 len=0 → write 没生效(silent failure)→ 重试或换路径
  ```

  **判定**:
  - `WRITE_OK_LEN=0` → write 没生效;可能原因:`Program` 是 read-only attribute / `RHS` 解析失败 / object path 错
  - `WRITE_OK_LEN>0` 且与 backup.txt 不同 → write 成功
  - `WRITE_OK_LEN>0` 且与 backup.txt **完全相同** → write"看似成功"但内容没变(可能 cache / read-only quirk)

  **绝对禁忌**:**看到 `[verify] OK` 就以为完成**——本次 `.AGV_Claude` 案例证明 [verify] OK 与实际落盘完全无关。

- **tags**:`write-verify`, `silent-failure`, `readback-Program`, `must-verify`, `write-simtalk-skill-bug`, `hard-rule-8`, `executeSilent-fresh-compile`
- **see also**:`03-workflow-playbook/skill-call-playbook.md §2.2 写操作 5 步硬流程`(原 step 5 是 verify,但 verify 实现不充分;本 entry 是 step 5 的强化);`02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log exp-005 (.execute() 不刷 .Program 缓存)`(根因层);`skills/local-simtalk-write-simtalk/SKILL.md` Step "verify"(quarantine-001 指向这里——SKILL.md 需要明确写"verify 不保证落盘,必须 readback");`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-recovery-prep.md` §Key findings 1;`skills/local-simtalk-execution/log/2026-09-01_agv-claude-recovery-prep.md` §"What this run validated / learned"

> 这条经验教会我:
> - **任何"verify 操作"都必须有独立成功信号**——`[verify] OK` 的 OK 来自一个**可能不可靠**的检查(`.execute()` 跑旧缓存)。**真正可靠的信号 = 直接读 `.Program` 看是否非空**。这是一条 universal rule,适用所有"modify object state"类操作:write 之后 read back,read 之后再信。
> - **跨 skill 工作流责任**:上层 skill(`write_simtalk` / `add_note` / `class_management`)的 verify 步骤存在系统性盲区——它们用 `.execute()` 而非 readback。**这是 skills-optimizer 应该修的设计缺陷**(quarantine-001),不是 user 应急能解决的。但 user/agent 必须**知道这个盲区**,在自己的 workflow 里加 readback 步骤。
> - **本次 `.AGV_Claude` 7-method silent fail 是个 warning shot**:agent 看到"7/7 [verify] OK"就 merge 报告、用户报告"还有问题"才回头 readback → 浪费 1+ session。如果当天就有 readback 步骤,5 分钟就能发现。

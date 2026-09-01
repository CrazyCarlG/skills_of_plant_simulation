### 2026-09-01 by @plant-simulation-experience-curator — `m.Program :=` 写入的方法 / 属性 **不持久化**:Plant Simulation 重启即丢,必须用户 GUI 导出 `.psfm`

> **Per CONTRIBUTING §6 强制 per-entry file**——本 entry 不嵌在 `skill-call-playbook.md §经验 Log`,独立成文件。

- **症状**:通过 bridge 写入的所有 SimTalk 修改(`.Program := <body>` / `<obj>.<attr> := <value>` / `createAttr` / `deleteObject` 等)**只在内存中**生效。Plant Simulation 进程一重启,**全部丢失**,没有任何告警。常见 surface 现象:
  - "我昨天写好的 7 method 今天都空了"(AGV_Claude 案)
  - "DataTable create 之后再启动就 void 了"(09-01 wrap 案:`.InformationFlow.DataTable.create(...)` 全部失败)
  - "用户以为今天做了修改,明天 export 才发现 .psfm 还是昨天的"
- **根因**:
  1. Plant Simulation 的"模型状态"分两层:**in-memory state**(进程内的所有修改)和 **on-disk state**(`.psfm` 文件的序列化内容)
  2. bridge 写入的所有操作只改 **in-memory state** —— bridge 的 server-side handler 对 `.Program :=` / `createAttr` / `deleteObject` 等的调用只更新内存对象,从不触发 file save
  3. **只有 GUI 的 File → Save / Save As 才能写 `.psfm` 文件**——bridge 没有暴露 "save model" action
  4. Plant Simulation 重启 = 从 `.psfm` 文件 reload → in-memory 的所有 bridge-side 改动全部消失
  5. 这是 **设计层面的 gap,不是 bug**:Plant Simulation 假设"用户在 GUI 里写,GUI 自动 save";bridge 没考虑 GUI-less 的工作流
- **Workaround / 结论**:

  ```bash
  # 任何 bridge-side 写操作完成后,必须告诉用户:
  #
  #   ⚠️ 1. Plant Simulation: File → Save (或 Ctrl+S) 保存当前模型
  #   ⚠️ 2. 验证:File → Close → File → Open → 选刚才保存的 .psfm
  #   ⚠️ 3. 此时改动仍然存在 → 持久化成功
  #
  # 如果跳过 1 → 重启后改动全无
  ```

  **判定**(在 agent 报告"写操作完成"之前,自检):
  - [ ] 用户是否已经被告知 "请 File → Save"?
  - [ ] 写操作是否在"短期测试"语境(马上 restart)?如果是 → 不需要 save,但仍要在 session summary 标记 "non-persistent"
  - [ ] 写操作是否涉及"修改业务对象"(DataTable / Method body / 创建新对象)?是 → save 是 mandatory

- **tags**:`persistence`, `m.Program-not-persistent`, `in-memory-vs-disk`, `psfm-export-required`, `bridge-no-save-action`, `restart-data-loss`, `workflow-mandatory-save`
- **see also**:`skill-call-playbook.md §2.2 写操作 5 步硬流程`(原 step 5 只覆盖 verify);`simtalkclaude-v1-and-v2.md §经验 Log exp-005 (.execute() 不刷 .Program 缓存)`(缓存 vs 持久化);`03-agent-memory/plant-simulation-expert-memory/2026-08-28_session-summary_synctoolkit-foundation.md` §02-bridge-tool 第 4 条(Source A);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md` §03-workflow-playbook 第 2 条(Source B);`skills/local-simtalk-write-simtalk/log/2026-08-31_create-agv-claude-7-methods.md`(Source C 隐含证据)

> 这条经验教会我:
> - **"in-memory 修改" ≠ "持久化"**——这是 bridge-side 写操作最大的盲区。agent 报告 "wrote 7 methods, all verified OK" 时,真实状态 = "wrote 7 methods into Plant Simulation's memory, NOT saved to .psfm file"。
> - **3 层数据生命周期必须分清**:(1) bridge 写入的 .Program —— 进程内存,重启即丢;(2) GUI File→Save 后的 .psfm —— 文件系统;(3) export 到 .spp —— 跨 PS 版本。
> - **agent 工作流硬规则 #9**:bridge-side 写操作完成后,**必须 explicit 提示用户 GUI save**,并在 session summary 标记 "non-persistent across PS restart"。
> - **与 exp-006 (write-readback) 互补**:exp-006 是"确认写到了内存",本条是"内存 ≠ 文件"——两个加在一起才是完整的 write 闭环。
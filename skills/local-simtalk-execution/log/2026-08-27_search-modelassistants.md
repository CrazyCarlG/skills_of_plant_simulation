# Usage log — 寻找 live model 下的 ModelAssistants

**Date:** 2026-08-27  **Skill:** `local-simtalk-get-folder-tree` (read-only) + `local-simtalk-execution` (transport)  **Target:** basis root & live model root
**Mode / Action:** search  **Operator:** plant-simulation-expert

## Goal
定位用户当前 Plant Simulation 模型根目录下名为 `ModelAssistants` 的文件夹。

## Steps
1. `grep -i "modelassist\|model assistant\|wizard|insert dial"` 扫 `01-plantsimulation-knowledge/` → 0 命中。
2. 扫 `bookmarks.csv` → 命中 GAWizard / Statistics Wizard / TeamcenterWizard，无 ModelAssistants。
3. 扫 `02-offcial-psfm-model/` 与 `02-simulation-file-experience/` → 0 命中。
4. 读 `basis_tree_depth4.json` / `depth5_fresh.json`：basis 顶层 10 个 Folder = MaterialFlow / Resources / InformationFlow / UserInterface / MUs / Tools / UserObjects / Models / ExperimentManager(Var) / SimtalkClaude。无 ModelAssistants。
5. 读 `current_root_fresh.json` / `current_models_fresh.json` / `current_tools_fresh.json` / `current_userobjects_fresh.json` / `models_d2.json`：当前模型 `.Models` 下仅有 Assembly1、Assembly2 两个 Frame，无 ModelAssistants。Tools 子树 = BottleneckAnalyzer / EnergyAnalyzer / ExperimentManager。
6. 大小写不敏感扫整棵 depth-5 basis 树（递归）→ 0 命中。
7. Live TCP 验证：
   - `simtalk_send ping` → ✅ success
   - `simtalk_send run 'print "###TEST###"'` → ❌ `Illegal access to an encrypted method.`
   - `simtalk_send syntax 'print 1'` → ❌ 同上
   - 端口 `127.0.0.1:50007` refused（容器隔离）；`host.docker.internal:50007` OK。

## Result
- 离线缓存(basis 深度 5 + 全部 current 子树)中 ModelAssistants 不存在。
- Live TCP 阻塞：服务器返回 "Illegal access to an encrypted method"，说明 SimtalkClaude 的入口 Method (`.SimtalkClaude.SimtalkAction.simtalk_run` 或等价) 在当前 live model 中被加密 / 不可访问——`run` 与 `syntax` 两条路径都被堵死，无法 BFS live model。

## Verdict — PARTIAL
离线证据不足，live 路径被加密入口堵死。

## What this run validated / learned
1. **缓存深度边界**：现有 basis 缓存到 depth 5 仍未触达 ModelAssistants。若该 Frame 实际存在于 live model，要么它在 depth ≥ 6 的子树，要么它不在 basis 而在 `.current` 根(用户当前打开的模型 Frame)。
2. **加密入口信号**：`Illegal access to an encrypted method` 与 ping OK 组合 = SimtalkClaude 的执行入口被锁。这不是 skill bug，是 live model 状态。`lifelines.md` 未记录该错误模式，建议在下次 bookkeep 时补一条。
3. **下一步建议（任选）**：
   - (a) 用户在 Plant Simulation GUI 里把 SimtalkClaude 的执行入口 Method 解密（右键 Method → Edit → 不勾 Encrypted），回复"已解密"后我重跑 BFS；
   - (b) 用户直接告知 ModelAssistants 在哪一层(例如 `.Models.Model.ModelAssistants` 或 `.current.ModelAssistants`)，我精准 BFS；
   - (c) 用户在 GUI 里展开 ModelAssistants 截图或导出 JSON，我离线分析。

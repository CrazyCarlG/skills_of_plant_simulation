# Session Summary — SyncToolkit foundation + copy/sync + MLayout (4 addenda)
**Date:** 2026-08-28  **Agent:** plant-simulation-expert
**Duration:** ~09:30 → 13:00 (4 addenda across context windows)
**Skills called:** local-simtalk-execution, local-simtalk-write-simtalk, local-simtalk-class-management

## 02-bridge-tool
- 桥 TCP 单次 payload ~2.7KB 上限(inline `simtalk_run`),用 chunked writer via `m.Program := cur + chr(10) + rhs` 绕过 → `02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log`(json.dumps antipattern)
- `simtalk_hasError` 对合法 SimTalk body 有 false-positive → 改靠 `kit.<Method>` 自身执行结果验证 → 同上 §经验 Log
- `simtalk_run` 桥**不能**捕获 Method 返回值(`print X` 被 Quirk #6 拦截;`return X` 报 "method has no return value" on wrapper)→ 唯一可靠路径:Method 内写入 string Variable,再 `attr_modify --read-only --type string` 读出
- 通过 `m.Program :=` 写入的方法**不持久化**(PS 重启即丢)→ 必须让用户 export .psfm

## 03-workflow-playbook
- 2D Frame 布局完成后必须跑 pairwise bbox overlap check(34 节点 = 561 对)→ `03-workflow-playbook/skill-call-playbook.md §经验 Log`
- MLayout Method 自身要包含在 LAYOUT 列表里(self-locating Method)——否则 Method 自己留在 (0,0),后续执行位置错

## 01-domain-concepts
- `_3D.BoundingBoxSize` 是 content-dependent:Variable 空串宽 2.69,80 字符宽 23.55(8.7×)→ `01-domain-concepts/derived-methods-quirks.md §经验 Log`
- `make_array` **不是** SimTalk v15+ 内置 → 用 `lst.create` + `lst.insert(N, value)` 替代(可在官方 `Small Parts Production/BottleneckAnalyzer` 模型验证)
- `lp.Value := ""`(纯 string Variable)**合法**清空;只有 `(string, length)` 等 typed Variable 用 `:=` 才丢类型 → `02-bridge-tool/simtalkclaude-v1-and-v2.md §经验 Log`(lp.Value := "" works)
- Variable 通过 `object` 引用赋 string 值(`dest := s` 或 `dest.Value := s`)在 v15+ 编译失败 → MPaste 故意跳过 Variable 同步(配置 Variable 应按 target 单独设)

## Cross-references
- per-skill logs:
  - `skills/local-simtalk-write-simtalk/log/2026-08-28_synctoolkit-foundation-layer.md`
  - `skills/local-simtalk-write-simtalk/log/2026-08-28_synctoolkit-frame-relayout.md`
- 02-simulation-file-experience entries: 上述 4 处 §经验 Log 引用

## Open questions / next steps
- TCP transport layer(MStartServer/Client/Stop/Send/OnReceive)用 SimTalk `Socket` 对象实现 — 下次 session
- Dialog wiring(button handlers) — 下次
- 跨版本 smoke test(2 个 PS 实例跑 MSave → file → MLoad + MSyncLibrary) — 下次
- v4 MPaste 支持 DataTable / PythonModule / Dialog / controls(当前 MPaste 返 2 skip)
- Encrypted code 复制未验证 end-to-end

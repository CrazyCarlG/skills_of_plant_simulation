# Session Summary — study `.ModelAssistants` + 02 code-experience alignment
**Date:** 2026-08-27  **Agent:** plant-simulation-expert
**Duration:** ~30 min
**Skills called:** local-simtalk-get-folder-tree, local-simtalk-read-library, local-simtalk-get-class-inheritance

## 04-model-case-studies
- `.ModelAssistants` 是 productivity toolkit(11 dialog-driven Frames,每个做一类工作流:rename / find-frame / encrypt / autosave / derive class / copy attribute / 3D convert / Python AI bridge / model replication)
- **`ModelSyncCopy` 是最重组件**:TCP serialize/deserialize 协议(chr(1)/chr(2) 帧 + chunked RxBuffer + 完整 Frame attr walk 含 position / icon / class metadata);最长方法 `M_BuildFrameNodes` 6.4KB;Frame 含 26 Methods + 6 Variables + 2 Sockets(server + client)+ 自定义 Dialog
- **AIBot 是空 Methods + PythonModule 模式**:`Py_SendRequest` 装实际代码,SimTalk 端是 glue
- **Inheritance 干净**(30 Frame/Dialog 节点):13 root classes + 17 derived;每个 Dialog 派生自 `BasicObjects.UserInterface.Dialog`(单 template,多 tool instances);每个 production Frame 是 root class(无 PS 内建 parent);`ClassAssistant.Frame` + `Namer.Frame` 是 parameter-rack UI 的 sub-Frame templates

## 01-domain-concepts
- 79 个 Methods:0 encrypted, 0 语法错, 24 空 bodies(Templates Method + lifecycle hooks 如 `autoexec` / `onCloseModel` / `autoexecLoadObj` 等待 deployment 时填充)
- 14 direct children of `.ModelAssistants`:11 Frames + 1 Folder + Templates Method + Internal Folder

## 03-workflow-playbook
- **`probe_inheritance.py` 不支持 `--no-infobox`,`probe_methods.py` 支持** — script inconsistency,统一性 PR 待提
- TSV probe 嵌入真 newline → `csv.reader` 拆错 → **必须** split raw text by lines starting with `.` 且 8+ tabs,直到下一个 record start

## Cross-references
- per-skill logs:
  - `skills/local-simtalk-get-folder-tree/log/2026-08-27_modelassistants-bfs.md`
  - `skills/local-simtalk-read-library/log/2026-08-27_modelassistants-probe.md`
  - `skills/local-simtalk-get-class-inheritance/log/2026-08-27_modelassistants-inheritance.md`
- 02-simulation-file-experience entries: 本次只读 3 篇(`class-instance-frame-folder.md` / `simtalkclaude-v1-and-v2.md` / `skill-call-playbook.md`),无新增沉淀
- Data dumps: `ModelAssistants_depth4.json` / `ModelAssistants_library.json` / `inheritance_map.json`

## Open questions / next steps
- user 后续若要改 `.ModelAssistants`,按 `skill-call-playbook §6.2` 5-step 写流程;backup 先到 `*.original.txt`
- `Internal.Socket` + `ModelSyncCopy.SocketServer/SocketClient` 值得下次 drill(类似 `.SimtalkClaude` 远程驱动场景)
- `AIBot.Py_SendRequest` PythonModule 本次未读 — 需确认 `read-library` 是否支持 PythonModule,或直接读 .py 文件

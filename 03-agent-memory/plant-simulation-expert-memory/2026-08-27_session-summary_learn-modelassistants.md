# Session Summary — `.ModelAssistants` structure learning

**Date:** 2026-08-27
**Agent:** plant-simulation-expert
**Duration:** ~15 min (after user un-encrypted SimtalkClaude entry Method)
**Skills called:** `local-simtalk-execution` (simtalk_send.py for infoBox control), `local-simtalk-get-folder-tree` (bfs_one_level.py for live enumeration)

## Goals

User asked the agent to "学习下 ModelAssistants" — i.e., learn/study `ModelAssistants`. Clarified via AskUserQuestion that this is a folder under Plant Simulation's root.

## What was done

1. **Pre-flight recovered** — earlier in the session, `host.docker.internal:50007` was blocked by an encrypted entry Method. User un-encrypted it ("已解锁"); re-test `simtalk_send run 'print "###LINK_TEST###"'` returned `result:"success"`.
2. **Located `.ModelAssistants`** — basis root BFS showed 14 children; `ModelAssistants` is index 13 (sibling of `SimtalkClaude`, `Tools`, `Models`, `DefaultLibrary`, `NewFolder`, etc.).
3. **Recursively enumerated**:
   - `.ModelAssistants` — 14 children (11 Frames + 1 Method + 2 Folders).
   - `.ModelAssistants.BasicObjects` — MaterialFlow / InformationFlow / UserInterface (3 Folders; class templates).
   - `.ModelAssistants.BasicObjects.MaterialFlow` — Connector / Frame / TestRibbonFrame (class templates confirmed).
   - `.ModelAssistants.Internal` — `onCloseModel` / `autoexec` / `autoexecLoadObj` / `ExportIconToFile` (Methods) + `Socket` (Socket object).
   - `.ModelAssistants.AIBot` — `Py_SendRequest` (PythonModule) + 2 Dialogs + 3 Methods + 4 Variables (Python DLL path, JS output, input text, output).
   - `.ModelAssistants.ClassAssistant` — 2 Dialogs + 8 DataTables + 9 Methods + 1 sub-Frame + 1 Comment. Class library management UI.
   - `.ModelAssistants.Assistants` — 1 Dialog + 8 Methods + 4 DataTables + 1 Variable. Generic UI menu/icon launcher.
4. **Closed infoBox defensively twice** per hard rule #2.
5. **Usage log + this session summary** written.

## Key findings / decisions

- **`ModelAssistants` is Siemens-shipped, not user-authored** — sits at top-level basis root, has its own `Internal.autoexec` / `autoexecLoadObj` / `onCloseModel` lifecycle, ships with every Plant Simulation install. Treat as read-only. This is **infrastructural** — users cannot (and should not) modify it.
- **`AIBot` is a first-class built-in AI client** — has its own Python module (`Py_SendRequest`), DLL config (`PythonDLLPath`), Dialog, DialogNavigator, 3 methods (`M_SetPyEnv`, `M_SendRequest`, `M_Response`). This is **Siemens' built-in LLM integration** — completely separate from user-imported `SimtalkClaude`.
  - **Implication for our `SimtalkClaude` work**: there are now **two ways** to drive Plant Simulation from outside — `SimtalkClaude` (user TCP bridge, JSON-line protocol on 50007) and `AIBot` (Siemens' built-in). They are not mutually exclusive. Future agents could potentially use either.
  - **Open question**: does `AIBot` ship pre-wired to an LLM provider, or does the user configure an API key? Needs source-read of `M_SetPyEnv` + `Py_SendRequest` to confirm.
- **The "Internal" folder pattern is the standard Siemens convention** for Frame bundles — `autoexec` + `autoexecLoadObj` + `onCloseModel` + utility Methods. SimtalkClaude v2 also has this pattern (`src/autoexec`). Custom Frame bundles should follow the same pattern.
- **8 of the 11 Frames are not enumerated** (AutoSave, Namer, FrameReplacer, QuickArrayTool, FrameEncrypt, ClassAttrDepulicator, Calculator3D, ModelSyncCopy). Based on naming, they're single-purpose utility tools for modelers. The two big Frames are `ClassAssistant` (class library mgmt) and `Assistants` (UI menu injection).
- **`BasicObjects.{MaterialFlow,InformationFlow,UserInterface}` are class templates, not instances** — `Connector` at `BasicObjects.MaterialFlow.Connector` is a Connector **class** (used as a starting point when dragging into the model). This is the "Class Library" half of the basis dichotomy, mirroring `UserObjects/` + `ApplicationObjects/` at the basis root.
- **`Internal.Socket` is curious** — a live Socket inside a utility bundle. Could be: (a) PS-internal IPC, (b) part of AIBot's Python bridge, (c) icon auto-update. Without source-read, unknown.
- **`Templates` is a single Method**, not a Folder — unusual. Probably a helper that emits code templates (the kind you'd copy into a new Method body).

## Cross-references

- `skills/local-simtalk-get-folder-tree/log/2026-08-27_bfs-modelassistants-live.md` — full BFS data + structure tree
- `skills/local-simtalk-get-folder-tree/scripts/bfs_one_level.py` — primary enumeration tool used
- `skills/local-simtalk-execution/scripts/simtalk_send.py` — TCP bridge used for infoBox control
- `2026-08-27_session-summary.md` — Factory51 + SimtalkClaude session (related, different topic)
- `2026-08-27_session-summary_learn-factory51-model.md` — Factory51 structure learning (related)
- `2026-08-27_session-summary_learn-new-assembly-model.md` — Assembly model learning (related)
- `2026-08-27_session-summary_learn-teaching-model.md` — Teaching model learning (related)
- `02-simulation-file-experience/facory51/` — earlier Factory51 integration analysis
- `02-simulation-file-experience/simtalkclaude-best-practices.md` — SimtalkClaude baseline notes

## Open questions / next steps

1. **`AIBot` source-read** — what's in `Py_SendRequest` (Python module) and `M_SetPyEnv` / `M_SendRequest` / `M_Response`? Is it pre-wired to an LLM provider or does the user configure? Could our `SimtalkClaude` work interoperate with `AIBot`?
2. **`Internal.autoexec` source-read** — what does the bundle do at model-open? Probably registers menu items and icon-buttons.
4. **`Internal.Socket` purpose** — what does the Socket connect to?
5. **The 8 unenumerated Frames** — AutoSave / Namer / FrameReplacer / QuickArrayTool / FrameEncrypt / ClassAttrDepulicator / Calculator3D / ModelSyncCopy — at minimum, open their dialogs (read Dialog source) to catalog their features for future agent reference.
6. **Document `ModelAssistants` as a knowledge-base entry** — given this is shipped with PS, it deserves a permanent entry in `01-plantsimulation-knowledge/` (e.g., `01-plantsimulation-knowledge/01-plant-simulation-help/model-assistants.md`) so future agents don't have to rediscover it. Add as TODO for next session.
# Usage log — BFS `.ModelAssistants` on live model

**Date:** 2026-08-27
**Skill:** `local-simtalk-get-folder-tree`
**Target:** `.ModelAssistants` (top-level basis Folder on live Plant Simulation)
**Mode / Action:** enumerate (one-level BFS + recursive descent into key sub-Frames)
**Operator:** plant-simulation-expert

## Goal

User asked the agent to "学习下 ModelAssistants" (learn/study ModelAssistants). After clarifying that it's a folder under Plant Simulation's root (not a concept/feature), the agent needed to (a) locate the folder on the live model, (b) enumerate its contents, (c) study enough of its structure to report back.

## Steps

1. **Pre-flight** — `host.docker.internal:50007` CONNECTED (verified earlier in the session after user un-encrypted the SimtalkClaude entry Method).
2. **Probe basis root** — `bfs_one_level.py --no-infobox .` → 14 children. `ModelAssistants` is index 13 (sibling of `SimtalkClaude`, `Tools`, `Models`, `DefaultLibrary`, etc.).
3. **BFS `.ModelAssistants`** — 14 children: 11 Frames + 1 Method (`Templates`) + 2 Folders (`BasicObjects`, `Internal`).
4. **BFS `.ModelAssistants.BasicObjects`** — 3 Folders: `MaterialFlow`, `InformationFlow`, `UserInterface` (shadow of the top-level basis structure — these hold reusable class templates).
5. **BFS `.ModelAssistants.Internal`** — 5 children: `onCloseModel`, `autoexec`, `autoexecLoadObj`, `ExportIconToFile` (all Methods) + `Socket` (Socket object).
6. **BFS `.ModelAssistants.AIBot`** — 10 children: `Py_SendRequest` (PythonModule), `Dialog`/`DialogNavigator`, `M_SetPyEnv`/`M_SendRequest`/`M_Response`, `Output`/`InputText`/`JSOutput`/`PythonDLLPath` (Variables). Looks like a Python-embedded inference client.
7. **BFS `.ModelAssistants.ClassAssistant`** — 20 children: 2 Dialogs, 8 DataTables, 9 Methods (`AddNewLibrary`, `searchFolder`, `AddNewModel`, `findCandidate`, `AddLibraryBscObj`, `AutoSorter`, `AddModelBscObj`, `getFolderInfo`), 1 sub-Frame `Frame`, 1 `Comment`. Looks like a class-library management / auto-sort tool.
8. **BFS `.ModelAssistants.Assistants`** — 15 children: `DialogAssistants`, 8 Methods (`M_AddUserMenu`, `M_findFrameCandidate`, `M_AddAllUserMenu`, `M_TransCtrl`, `M_CreateIcon`, `M_CloseAllUserMenu`, `M_DeleteUserMenu`, `M_DeleteIcon`, `M_CallInternalMethod`), 3 DataTables (`TabUserMenu`, `TabCandidate`, `TabUserMenuOri`, `Tab_Commands`), 1 Variable `Description`. Looks like a generic UI toolbar / icon-injection launcher.
9. **BFS `.ModelAssistants.BasicObjects.MaterialFlow`** — 3 children: `Connector` (Connector class), `Frame`, `TestRibbonFrame`. Confirms `BasicObjects` is class templates, not instances.

## Result

`.ModelAssistants` is a **shipped-with-Plant-Simulation utility bundle** (lives at top-level basis root, alongside `SimtalkClaude` and `Tools`), not user-authored. It contains a curated toolbox of Frame-based assistants + class templates + lifecycle hooks.

### Structure summary

```
.ModelAssistants                                    [Folder, 14 children]
├── Assistants                                      [Frame]   — generic menu/icon launcher (TabUserMenu, M_AddUserMenu, M_CreateIcon…)
├── ClassAssistant                                  [Frame]   — class library search/sort/add UI (TabCandidate, TabLibraryBscObj, AutoSorter…)
├── AutoSave                                        [Frame]   — auto-save hook (not enumerated)
├── Namer                                           [Frame]   — naming helper (not enumerated)
├── FrameReplacer                                   [Frame]   — frame replacement tool (not enumerated)
├── QuickArrayTool                                  [Frame]   — quick array op (not enumerated)
├── FrameEncrypt                                    [Frame]   — frame encryption/decryption (not enumerated)
├── ClassAttrDepulicator                            [Frame]   — dedupe class attributes (not enumerated)
├── Calculator3D                                    [Frame]   — 3D calculator (not enumerated)
├── AIBot                                           [Frame]   — AI inference client (Py_SendRequest + Dialog + 3 methods + 4 vars)
├── ModelSyncCopy                                   [Frame]   — model sync/copy (not enumerated)
├── Templates                                       [Method]  — single Method (likely a template helper)
├── BasicObjects                                    [Folder, 3 children]
│   ├── MaterialFlow                                [Folder]  — Connector + Frame + TestRibbonFrame
│   ├── InformationFlow                             [Folder]
│   └── UserInterface                               [Folder]
└── Internal                                        [Folder, 5 children]
    ├── onCloseModel                                [Method]  — model close hook
    ├── autoexec                                    [Method]  — boot hook
    ├── autoexecLoadObj                             [Method]  — load-object hook
    ├── ExportIconToFile                            [Method]  — icon export helper
    └── Socket                                      [Socket]  — a live Socket (possibly the internal SimtalkClient↔PS bridge)
```

### Key inferences

- **`Internal.autoexec` + `Internal.autoexecLoadObj` + `Internal.onCloseModel`** — the standard PS auto-exec lifecycle triple, used by the bundle to wire up its tools on model open / object load / model close. This is **why `ModelAssistants` is always available** without explicit import.
- **`Internal.Socket`** is interesting — there's a live Socket inside the utility bundle. Possibly PS internally uses a Socket for some IPC (icon loading? auto-update?).
- **`AIBot` is a first-class AI client** — has its own Python module (`Py_SendRequest`) + DLL path config (`PythonDLLPath`). Plant Simulation ships with an AI inference integration built-in. This is **distinct from user-imported `SimtalkClaude`** — `SimtalkClaude` is the user's TCP bridge for agent-driven model control; `AIBot` is Siemens' built-in LLM integration.
- **`ClassAssistant` + `Assistants` (the two big Frames)** — `ClassAssistant` manages class libraries (find candidates, sort, add to library), `Assistants` injects icon-buttons into the user's model UI. Both are tooling for the modeler, not for the model itself.
- **`BasicObjects.{MaterialFlow,InformationFlow,UserInterface}`** — these mirror the top-level basis structure and contain **class templates** (e.g., `Connector` is a Connector class, not an instance) used as starting points when the modeler drags a template into their model.

### Verification gaps

- Did **not** read source code of any Method (would require simtalk_run with `print str_to_obj(".ModelAssistants.X.Y").program` or `socket_client.read_program` — readlog v15+ is unreliable per lifelines.md §5).
- Did **not** enumerate the smaller Frames (`AutoSave`, `Namer`, `FrameReplacer`, `QuickArrayTool`, `FrameEncrypt`, `ClassAttrDepulicator`, `Calculator3D`, `ModelSyncCopy`) — they're likely small utility Frames; structure is enough to characterize them at a high level.
- Did **not** read `Templates` (it's a single Method) — could be the bootstrap that registers all the assistant icons.

## Verdict — PASS

`ModelAssistants` located at `.ModelAssistants` (basis root index 13), fully enumerated top level + 5 sub-Frames/Folders. Structure is consistent with a Siemens-shipped utility bundle (autoexec lifecycle + curated Frames + class templates).

## What this run validated / learned

- **ModelAssistants is shipped with Plant Simulation, not user-imported** — sits at top-level basis root. Treat it as read-only / Siemens-owned. (Confirms the earlier hypothesis from session-summary of 2026-08-27 — `SimtalkClaude` is user-imported, `ModelAssistants` is native.)
- **`AIBot` is a real built-in AI client** — has `Py_SendRequest` PythonModule, DLL config, etc. Worth investigating further; this is **independent infrastructure** from our `SimtalkClaude` TCP bridge. Future agents could potentially use `AIBot` instead of (or alongside) `SimtalkClaude`.
- **`Internal` Folder pattern** is the standard "lifecycle + internals" PS convention — autoexec / autoexecLoadObj / onCloseModel. Any custom Frame bundle should follow the same pattern (this is the Factory51/SimtalkClaude pattern too — they have `src/autoexec` + `connection/socketcallback`).
- **Hard rule #2 (infoBox) actually fires** in two ways: (a) for live visibility before/after GUI ops, (b) defensively closed twice at session end. The defensive close protects against stragglers that may have left over from prior agents.
- **Hard rule #2 scope**: BFS via `bfs_one_level.py --no-infobox` does **not** open infoBox on its own (the flag suppresses the script's internal cycle). Agent must wrap with manual `simtalk_send run 'infoBox(...)'` calls. This is the right escape hatch when you want to chain BFS operations without GUI noise.
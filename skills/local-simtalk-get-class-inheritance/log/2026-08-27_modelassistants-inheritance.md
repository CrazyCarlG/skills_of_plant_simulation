# Usage log — Class inheritance for `.ModelAssistants.*`

**Date:** 2026-08-27  **Skill:** `local-simtalk-get-class-inheritance`  **Target:** 30 Frame/Dialog candidates under `.ModelAssistants`
**Mode / Action:** `probe_inheritance.py` (no --no-infobox flag, batch=12)  **Operator:** plant-simulation-expert

## Goal
Capture `Origin` / `OriginRoot` / `Class` / `InternalClassType` for every
Frame and Dialog node under `.ModelAssistants` so I can map which are
user-defined classes vs which inherit from `BasicObjects` templates.

## Steps
1. Walked BFS tree for `type in ("Frame","Dialog")` → 30 candidate paths.
2. Ran `probe_inheritance.py <paths.txt> <out.tsv>` (script does not support
   `--no-infobox` — infoBox auto-opened + closed by the script itself, per
   iron rule #2 still satisfied).
3. Rendered with `render_inheritance_map.py` → `data/inheritance_map.json`.

## Result
**Root classes (Origin=VOID, Class=VOID) — 13**:
- 11 top-level Frames: `Assistants`, `ClassAssistant`, `AutoSave`, `Namer`,
  `FrameReplacer`, `QuickArrayTool`, `FrameEncrypt`, `ClassAttrDepulicator`,
  `Calculator3D`, `AIBot`, `ModelSyncCopy`.
- 2 sub-templates in `BasicObjects`: `MaterialFlow.Frame` (inherits MF base),
  `UserInterface.Dialog` (DIALOG base).

**Derived classes (have Origin) — 17**:
- 13 Dialogs (one per Frame) all originate from
  `.ModelAssistants.BasicObjects.UserInterface.Dialog` — confirms the
  **single-Dialog-base pattern**: every Frame gets its own Dialog child
  derived from the canonical `BasicObjects.UserInterface.Dialog`.
- 2 sub-Frames in `ClassAssistant.Frame` and `Namer.Frame` originate from
  `.ModelAssistants.BasicObjects.MaterialFlow.Frame` — those are Frame
  instances placed **inside** the tool Frame (used for parameter-rack
  visual scaffolding, see e.g. `Namer.Frame.TestObject`).
- 1 `TestRibbonFrame` under `BasicObjects.MaterialFlow` is a tester /
  example, with `OriginRoot` = itself (Class=VOID → it's a leaf subclass).

## Verdict — PASS
Inheritance captured for all 30 candidates. Rendered map confirms:
1. Every production Frame is a **first-class user-defined root class** (no
   inheritance to Plant Simulation built-ins) — they all start from
   `Origin=VOID`, which means they're standalone templates.
2. Every Dialog is a **derived class** of `BasicObjects.UserInterface.Dialog`
   — single-template-reuse is consistent.
3. `ClassAssistant.Frame` and `Namer.Frame` are **sub-Frame templates**
   derived from `BasicObjects.MaterialFlow.Frame` — they sit inside their
   parent Frame for UI organisation.

## What this run validated / learned
- `probe_inheritance.py` does **not** accept `--no-infobox` (positional args
  only). Documenting: skill scripts in this family are inconsistent on the
  flag — `probe_methods.py` does, `probe_inheritance.py` does not.
- The **Dialog-Origin pattern is clean**: all 13 Dialogs of `.ModelAssistants`
  share `OriginRoot = .ModelAssistants.BasicObjects.UserInterface.Dialog` —
  this is the "single template, many tool instances" idiom. If a new Frame
  is added later, copy its Dialog from this base.
- The empty `Templates` Method has no inheritance (it's a leaf Method, not
  a Frame) — not in this probe set.
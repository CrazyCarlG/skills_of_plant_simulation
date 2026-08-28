---
last_updated: 2026-08-27
contributors: [@z004bjuu, @plant-simulation-expert]
scope: assembly-line 模型探索的总入口（目录导览 + 子文件索引）
---

# assembly-line — Assembly-line Model Business Logic Experience

> Patterns extracted from the **assembly-line model** currently loaded in
> Plant Simulation (`Models.Assembly1` + `Models.Assembly2`,
> `.UserObjects.*`). This is a custom **instrumented production line**
> with `WorkerChart`, `PalletOptimization`, `BottleneckAnalyzer`,
> `EnergyAnalyzer`. It is **not** the Siemens Factory51 reference model.

| File | Purpose |
|---|---|
| `README.md` | This index + key cross-references |
| `assembly-line-business-logic.md` | **Main report** — model architecture, `UserObjects` library pattern, `WorkerChart`, `PalletOptimization` rule engine, A/B baseline-vs-instrumented design |
| `analyzers-pattern.md` | Supplement — `BottleneckAnalyzer` (8-state utilization) + `EnergyAnalyzer` (observer + 2D/3D visualization) detailed patterns |
| `probe-pipeline-quirks.md` | Supplement — `probe_methods.py` + `render_library.py` pipeline bugs encountered while learning the model, with workarounds |

## Top-level findings

1. **`UserObjects/` is a class-library + module-template split** —
   `.UserObjects.Classes.*` holds reusable class definitions
   (Toolbar Library, Track CrossTransfer, Station MS, Station AS,
   Worker ×3, PickAndPlace Robot); `.UserObjects.Modules.*` holds
   instance templates (`PreProduction` Frame with full
   Source/Station/Conveyor/Connector/Robot assembly). Each line
   instance embeds its own `PreProduction` instance. **Two-level
   separation** that the Factory51 model does not use.
2. **Assembly1 vs Assembly2 is A/B baseline-vs-instrumented design** —
   identical 113-child assembly line topology. Assembly1 is the "lean
   baseline" (no analyzers); Assembly2 adds `BottleneckAnalyzer` (13
   methods), `EnergyAnalyzer` (17 methods), `BufferOptimization`,
   `EnergySavingMeasures`, `DisplayEnergy`.
3. **`PalletOptimization` and `BufferOptimization` have an identical
   135-node structure** (verified by failed BFS that emitted identical
   method lists up to char 11971). **High drift risk** — duplicated
   Frames are likely to diverge if either side is edited independently.
4. **`WorkerChart` is a textbook Frame-with-UI pattern** — Frame +
   Dialog + 2 DataTables + VarObj Variable + internal chart.
   `Open` uses SimTalk 2.0 syntax (`is`/`do`/`inspect`/`when`/`end;` +
   `then`), all other methods use SimTalk 1.0.
5. **`NwWorkerPool` is the worker-pool class** — `internalClassName`
   check in `DragAndDrop` guards the type.
6. **SimTalk 2.0 syntax is used selectively** — only `WorkerChart.Open`
   uses 2.0. Likely because it was rewritten later. SimTalk 1.0 is the
   project default.

## Cross-references

- `02-simulation-file-experience/02-bridge-tool/simtalkclaude-v1-and-v2.md` —
  SimtalkClaude v1+v2 baseline (still applies; same TCP bridge)
- `../factory51/` — Siemens Factory51 +
  SimtalkClaude v2 experience (orthogonal model, complementary
  patterns)
- `../ctu-warehouse/` — class-inheritance
  reverse-verification pattern (a different approach to library
  navigation)
- `../../03-workflow-playbook/skill-call-playbook.md` — 9-skill
  usage playbook
- `skills/local-simtalk-get-folder-tree/data/models_d2.json` —
  fresh depth=2 of `.Models`
- `skills/local-simtalk-get-folder-tree/data/userobjects_d2.json` —
  Classes + Modules structure
- `skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-palletOptimization-workerChart.md`
- `skills/local-simtalk-read-library/log/2026-08-27_learn-assembly-model-bottleneckAnalyzer-energyAnalyzer.md`
- `03-agent-memory/plant-simulation-expert-memory/2026-08-27_session-summary_learn-new-assembly-model.md`
  — source session summary

## Environment note

The probe session ran against `host.docker.internal:50007` with
Plant Simulation live and SimtalkClaude bridge running. All findings
were derived from real `simtalk_run` + `readlog` output — **not from
documentation**. See `probe-pipeline-quirks.md` for the pipeline bugs
encountered and the workarounds used.
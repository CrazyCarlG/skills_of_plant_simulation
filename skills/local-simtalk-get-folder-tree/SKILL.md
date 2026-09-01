---
name: local-simtalk-get-folder-tree
description: Enumerate the Plant Simulation class-library folder tree (basis root + descendant Folders / Frames / contents) by sending SimTalk to the running server via the `local-simtalk-execution` skill. Use when the user wants to inspect "what's inside basis", explore an unknown model's Class Library, list the contents of a Folder/Frame, or build a structured map of a loaded model's object hierarchy. Triggers include: "show me basis folder tree", "list the model's folders", "what's under .Models.Model", "enumerate children of <path>", "give me the folder structure of this model". This skill does NOT modify the server model — it only reads.
---

# local-simtalk-get-folder-tree

Read-only exploration of the Plant Simulation **basis** root (the Class Library
root that holds every folder/frame visible to SimTalk) and any of its descendant
Folder/Frame subtrees. Output is JSON, written to disk for offline analysis.

This skill **does not** talk to the server directly — it composes a SimTalk
program that does, then wraps the result. It depends on the
`local-simtalk-execution` skill for transport.

## When to use

- "Explore the basis folder tree" / "What folders does this model expose?"
- "List contents of `<path>`" / "What's inside `.Models.Model`?"
- "Build a tree-shaped inventory of the loaded model"
- "Verify a path is valid" / "How many children does `<X>` have?"

Do **not** use this skill for:
- Reading the value of a specific attribute / variable — that's a one-shot
  `local-simtalk-execution` `run` with a `print` (Quirk #6 means `data` field
  is always empty, so use print + readlog)
- Editing the model
- Running a simulation experiment
- **Re-running BFS when you already have a fresh snapshot on disk.** Before
  calling `bfs_full.py`, check `data/` for `*_fresh.json` files
  (e.g. `basis_tree_depth5_fresh.json`, `current_models_fresh.json`). If
  one exists with a recent timestamp from this session and the same loaded
  model, **read it instead of re-running BFS**. Re-running wastes 30–60
  TCP round-trips and triggers GUI `infoBox` open/close churn.
  
  The `*_fresh.json` convention is **per-session and per-model** — the
  cache becomes stale when:
  - the operator swaps the loaded model (e.g. `.Models.Factory51` →
    `.Models.Assembly1` → `.Models.internal.Admin` in one day), or
  - the date in the filename is older than today.
  
  Verify before reuse: `stat data/basis_tree_depth*_fresh.json | grep
  Modify` and confirm the mtime matches the current session.

## How it works

The skill's two scripts implement a 2-step protocol per node:

1. **`scripts/bfs_one_level.py [--no-infobox] <path>`** — sends one SimTalk
   program that calls `str_to_obj(<path>)`, then enumerates the direct children
   of that object via `<obj>.numNodes` + `<obj>.node(i)` + `<obj>.Name` +
   `<obj>.InternalClassType`. It builds a JSON object as a string and `print`s
   it (Quirk #6 — `data` field never carries the value back; only `print +
   readlog` works). Then it calls `readlog` and parses out the marker-delimited
   JSON.
2. **`scripts/bfs_full.py [--no-infobox] <path> <max_depth> <output.json>`** —
   driver that recursively calls `bfs_one_level.py` for every Folder/Frame
   descendant up to `<max_depth>` and writes a nested tree JSON to disk.

Both scripts depend on:
- `local-simtalk-execution/scripts/simtalk_send.py` (transport + Quirk-aware
  exit codes) — see that skill's `references/lifelines.md` for the protocol
  hard-rules.

### Skill convention: always announce with `infoBox`

Per the `local-simtalk-execution` v18 → v19 convention, every invocation of
this skill **opens a non-modal `infoBox(text, false)` on the Plant Simulation
GUI before doing any work, and closes it (defensively twice) on exit**. The
text tells the operator what the skill is currently doing — without it, the
GUI gives no signal that a long BFS is in flight.

| Stage | What the script does |
|---|---|
| Entry | `infoBox("[bfs_one_level] start: path=<path>", false)` or `infoBox("[bfs_full] start: path=<path> depth=<N> -> <out>", false)` |
| Progress (`bfs_full` only) | At depth 0 and 1 boundary nodes, `infoBox(...)` updates the box with `calls=<n> depth=<d> path=<p>` so the operator sees traversal progress |
| Exit (success or failure) | `infoBox("", false)` **twice** — defensive double-close is idempotent if no box is up, but guards against a stuck GUI box |
| Headless / batch runs | Pass `--no-infobox` as the **first** argument to both scripts to suppress the open / update / close cycle entirely |

The second argument `false` is the modal flag — non-modal so it never freezes
the GUI while BFS round-trips are in flight. Quirk: do **not** swap to
`infoBox(text, true)` (modal) — that would block the server waiting for a GUI
click (lifelines §4).

## Usage

```bash
# One level at a time (opens + closes infoBox automatically)
python3 scripts/bfs_one_level.py .
python3 scripts/bfs_one_level.py .SimtalkClaude
python3 scripts/bfs_one_level.py .Models.Model

# Suppress infoBox for headless / CI runs
python3 scripts/bfs_one_level.py --no-infobox .
python3 scripts/bfs_full.py --no-infobox . 4 data/basis_tree_depth4.json

# Full recursive enumeration with progress updates on the GUI
python3 scripts/bfs_full.py . 4 data/basis_tree_depth4.json
```

> ⚠️ **The path argument cannot be an empty string.** `bfs_one_level.py ""`
> fails with `ERR: cannot resolve path: ""` — `str_to_obj("")` returns void,
> and the script exits with the resolve-failure error. Use `"."` for the
> basis root (the basis identifier is anonymous; `obj_to_str(basis)` returns
> the empty string, but the **string literal** `"."` is what `str_to_obj`
> expects). See [GFT-2 below](#gft-2-empty-string-root-path-rejected) for
> the underlying reason.

Both scripts run on the **WSL2 / Docker container** that hosts the bridge to
Plant Simulation. Default target is `host.docker.internal:50007` (matches
`local-simtalk-execution`'s default).

## Output shape

```json
{
  "root_path": "",                  // "" because basis is anonymous
  "root_name": "Basis",
  "root_type": "Folder",
  "root_numNodes": 10,
  "children": [
    {
      "i": 1,
      "name": "MaterialFlow",
      "type": "Folder",
      "path": ".MaterialFlow",
      "children": [ ... recursive ... ]
    },
    ...
  ]
}
```

Non-Folder/Frame children appear as a flat list of `{i, name, type, path}`.
Their type may be anything Plant Simulation supports: `Method`, `Variable`,
`DataTable`, `Socket`, `Button`, `Dialog`, `Chart`, `HtmlReport`, `DataList`,
`Comment`, `Part`, `Connector`, `EventController`, `Station`, `Conveyor`,
`Container`, `Source`, `Drain`, `Buffer`, `Sorter`, `Track`, `Worker`, `Exporter`,
`Broker`, `AGVPool`, `ShiftCalendar`, `FileInterface`, `MQTTInterface`,
`Display`, `SankeyDiagram`, `CostAnalyzer`, `AttributeExplorer`, `Trigger`,
`Generator`, etc. (See `data/basis_tree_depth4.json` for the full type list.)

## Hard rules / Quirks (subset of `local-simtalk-execution/references/lifelines.md`)

| Rule | Why |
|---|---|
| `type` field must be one of `ping` / `simtalk_syntax` / `simtalk_run` / `readlog` | Unknown types cause silent server-side hang (Quirk #13) |
| Use `--resp-mode delimiter --resp-delimiter '\|\|END\|\|'` for reply framing | Server never closes the socket (lifelines §2) |
| `simtalk_run` `data` field is **always** empty | Quirk #6 — server doesn't serialize return values |
| Runtime errors return `result:"success"` with `log:"code execute failed..."` | Quirk #7 — must double-check (simtalk_send.py exit codes 10/11) |
| Avoid `prompt` / `infoBox` / `promptList*` / writing undeclared global attrs | Modal trap — server blocks until GUI click (lifelines §4) |
| `param` declarations are silently accepted but not bound by simtalk_run | We bake the path into the code instead (lifelines §A2) |
| **Always `infoBox(text, false)` on entry, close twice on exit** | Skill convention from `local-simtalk-execution` v18→v19 — gives the GUI operator a visible signal that a BFS is in flight. Pass `--no-infobox` for batch runs |

### Skill-specific quirks

| # | Quirk | Workaround |
|---|---|---|
| GFT-1 | `bfs_one_level.py` truncates stdout for sub-frames with > ~130 children. A sub-frame with 142 children (`Factory51`) hits `ERR: unbalanced braces after marker` — the single-shot JSON dump exceeds the readlog buffer / one-shot log emission limit | Use `bfs_full.py --no-infobox .Models.<Subframe> 1 data/<subframe>_children.json` (depth-1 recursive, writes to disk) instead of stdout for large sub-frames. The `bfs_full.py` driver writes the JSON to a file and avoids stdout buffering constraints. See `references/exploration-log.md` §"Day 2 — large-subframe JSON-dump limit" |
| GFT-2 | Empty-string root path is rejected: `bfs_one_level.py ""` fails with `ERR: cannot resolve path: ""`. `str_to_obj("")` returns void, and the script's resolve-failure path exits with that error | Use `"."` for the basis root. The basis identifier is anonymous (`obj_to_str(basis)` returns `""`), but the **string literal** `"."` is what `str_to_obj` expects — `"."` and `""` are different inputs to the parser |

## Path resolution

`str_to_obj(<path>)` is the SimTalk built-in that turns a string path into an
object reference. Paths follow the Plant Simulation convention:

| Path string | Resolves to |
|---|---|
| `.` | the basis root (display name "Basis", anonymous path) |
| `.Models.Model` | the Frame at `<basis>/Models/Model` |
| `.SimtalkClaude.main` | the Frame at `<basis>/SimtalkClaude/main` |

The basis identifier itself is **anonymous** — `obj_to_str(basis)` returns the
empty string. That's why `root_path` is `""` in the output.

## Limitations

- **Read-only.** No writes.
- **`infoBox` requires a GUI session.** The `infoBox(text, false)` call targets
  the Plant Simulation GUI window — if the server is running headless (no
  display), the call still returns success but no box appears. Use
  `--no-infobox` in CI / headless contexts.
- **One readlog per call.** Quirk #7 means `print + readlog` is the only path
  back to the client. `readlog` is currently degraded (lifelines §5) — buffer
  may show exponential growth if called repeatedly in tight loops, so
  `bfs_full.py` adds a small `time.sleep`-equivalent by paying TCP RTT per
  node. At depth 4 with branching factor ≈ 5, expect 30–60 round-trips.
- **`max_depth` semantics.** Depth 1 means "show basis + its direct children".
  Depth 4 stops recursing at depth 4 — children of depth-4 frames are **not**
  expanded. Use higher depth for fully enumerated sub-trees.
- **No streaming.** Each level completes before the next starts, so a deep
  traversal is O(depth × RTT). For a typical model, depth 5 finishes in a
  couple of minutes.

## Key files

- `scripts/bfs_one_level.py` — single-level enum + readlog parser
- `scripts/bfs_full.py` — recursive driver, writes nested JSON to disk
- `references/exploration-log.md` — what was discovered in the 2026-08-25
  exploration of the production model
- `data/basis_tree_depth4.json` — captured tree (depth ≤ 4) of the model
  loaded on the server at exploration time

## Logging

Every invocation of this skill **must** produce exactly one new log file
under `log/` — appending to existing logs is forbidden, one file per
session. Filename pattern:

```
<YYYY-MM-DD>-<agent>-<topic>.md
```

- `<agent>` is the calling agent in kebab-case. Default: `plant-simulation-expert`.
- `<topic>` is a kebab-case slug (≤ 5 words) describing what this call
  did. Example for this skill: `bfs-basis-depth4`.
- Same-day multiple sessions: append `-2`, `-3`, … before `.md`.
- DO NOT rename or move existing log files (old
  `YYYY-MM-DD_<topic-slug>.md` files stay as historical record).

Full schema (frontmatter fields, required sections, verdict rubric):
see `log/CONTRIBUTING.md`.

## Related skills

- `local-simtalk-execution` — the underlying TCP transport skill; consult its
  `references/lifelines.md` for protocol details before modifying these scripts.
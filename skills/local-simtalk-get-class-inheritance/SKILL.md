---
name: local-simtalk-get-class-inheritance
description: Enumerate the Plant Simulation Class Library's class-inheritance tree — for every candidate class, query the read-only attributes `Origin` (immediate parent), `OriginRoot` (root of inheritance chain), `Class` (the class-library object from which the instance was derived), and `InternalClassType` — by sending SimTalk to the running server via `local-simtalk-execution`. Use when the user wants to know "what classes does this model define", "which classes are derived from `<base>`", "show me the inheritance map of `<X>`", "is `<path>` a root or a derived class", "what's the parent of `<path>`". Builds a parent→children map of the basis + user-defined subclasses. Depends on `local-simtalk-get-folder-tree` (which provides the candidate-class inventory) and `local-simtalk-execution` (TCP transport). This skill does NOT modify the server model — it only reads.
---

# local-simtalk-get-class-inheritance

Read-only exploration of the Plant Simulation **class-inheritance structure** —
for every candidate class in the loaded model, capture the `Origin` /
`OriginRoot` / `Class` / `InternalClassType` attributes and emit a
**parent → children map** plus a flat list of derived (user-defined) classes.

This skill **does not** talk to the server directly — it composes SimTalk
that does, then wraps the result. It depends on the `local-simtalk-execution`
skill for transport, and on `local-simtalk-get-folder-tree` for the
candidate-class inventory.

## When to use

- "What classes does this model have / inherit from?" / "Show me the
  inheritance tree"
- "Which user-defined classes extend `<base>`?"
- "Is `<path>` a root class or a derived class?"
- "What's the parent of `<path>`?" / "What's the inheritance root of `<X>`?"
- "Build a class-inheritance map of this model"

Do **not** use this skill for:

- Reading individual attribute values (use `local-simtalk-execution` directly)
- Editing the model
- Running simulation experiments
- Enumerating folder/frame children (that's `local-simtalk-get-folder-tree`)

## How it works

The skill's two scripts implement a 2-step protocol:

1. **`scripts/probe_inheritance.py <paths.txt> [out.tsv]`** — takes a flat
   list of candidate class paths (one per line), batches them in groups of
   12, and for each batch sends one `simtalk_run` (the SimTalk enumerates
   `str_to_obj(p).Origin`, `.OriginRoot`, `.Class`, `.InternalClassType` for
   each path and prints them with a per-batch `###INH_BATCH###` marker),
   followed by one `readlog`. The script extracts the marker's content from
   the cumulative buffer using `rsplit(marker, 1)`, parses the printed
   `<path> | name=... | type=... | Origin=... | OriginRoot=... | Class=...`
   lines into a dict, and writes TSV rows to disk.
2. **`scripts/render_inheritance_map.py <raw.tsv>`** — partitions the rows
   into **root classes** (Origin=VOID — Plant Simulation built-ins) and
   **derived classes** (Origin≠VOID — user-defined subclasses), and renders
   a parent → children tree plus a derived-class detail view.

Both scripts depend on:
- `local-simtalk-execution/scripts/socket_client.py` (raw TCP transport —
  used directly to avoid shell escaping issues with embedded `+` and `\\"`)

### Skill convention: always announce with `infoBox`

Every invocation opens a non-modal `infoBox(text, false)` on the Plant
Simulation GUI before doing any work and closes it (defensively twice)
on exit. See
[`../local-simtalk-execution/references/infoBox-convention.md`](../local-simtalk-execution/references/infoBox-convention.md)
for the full protocol.

> ⚠️ **`--no-infobox` is NOT supported.** Unlike `bfs_one_level.py` /
> `probe_methods.py` / `attr_modify.py`, `probe_inheritance.py` is a
> positional-args-only parser — passing `--no-infobox` errors out
> (`unrecognized arguments: --no-infobox`). The script self-manages the
> `infoBox` lifecycle; GUI is opened at entry and closed twice on exit
> regardless. If you need a fully silent run, wrap the call in a
> context that suppresses GUI focus (e.g., dedicated Plant Simulation
> headless frame). See INH-7 below.

## Usage

```bash
# 1. Probe inheritance for every candidate path (one per line)
python3 scripts/probe_inheritance.py paths.txt data/inheritance_raw.tsv

# 2. Render the parent -> children map from the raw TSV
python3 scripts/render_inheritance_map.py data/inheritance_raw.tsv
```

A typical pipeline (given the sibling folder-tree skill has produced a
candidate list):

```bash
# a) Filter the folder-tree JSON down to class candidates
python3 - <<'PY'
import json
tree = json.load(open(
  "skills/local-simtalk-get-folder-tree/data/basis_tree_depth4.json"))
classes = set()
def walk(n):
    if n["type"] not in ("Folder", "Frame", "Method", "Variable",
                          "DataTable", "Socket", "Button", "Dialog",
                          "Chart", "HtmlReport", "DataList", "Comment",
                          "FileLink"):
        classes.add(n["path"])
    for c in n.get("children", []):
        walk(c)
walk(tree)
with open("paths.txt", "w") as f:
    for p in sorted(classes): f.write(p + "\n")
PY

# b) Probe each class's Origin / OriginRoot / Class
python3 scripts/probe_inheritance.py paths.txt data/inheritance_raw.tsv

# c) Render the inheritance tree
python3 scripts/render_inheritance_map.py data/inheritance_raw.tsv
```

## Output shape

`data/inheritance_raw.tsv` (probe output):

```
.MaterialFlow.Connector<TAB>Connector<TAB>Connector<TAB>VOID<TAB>.MaterialFlow.Connector<TAB>VOID
.UserObjects.MyFrame.Station<TAB>Station<TAB>Station<TAB>.MaterialFlow.Station<TAB>.MaterialFlow.Station<TAB>.MaterialFlow.Station
...
```

Six tab-separated fields per row: `path`, `name`, `type`, `origin`, `originroot`, `cls`.

`data/inheritance_map.json` (rendered output, written alongside `inheritance_raw.tsv`):

```json
{
  "captured_at": "2026-08-26",
  "total_classes": 65,
  "root_classes": [
    ".MaterialFlow.Connector",
    ...
  ],
  "derived_classes": [
    {
      "path": ".UserObjects.MyFrame.Station",
      "name": "Station",
      "type": "Station",
      "origin": ".MaterialFlow.Station",
      "originroot": ".MaterialFlow.Station",
      "class": ".MaterialFlow.Station"
    },
    ...
  ],
  "tree": {
    "VOID": [
      { "path": ".MaterialFlow.Connector", "name": "Connector", ... },
      ... (61 root classes)
    ],
    ".MaterialFlow.Station": [
      { "path": ".UserObjects.MyFrame.Station",
        "name": "Station", "type": "Station",
        "origin": ".MaterialFlow.Station",
        "originroot": ".MaterialFlow.Station",
        "class": ".MaterialFlow.Station" }
    ],
    ...
  }
}
```

- `root_classes` is a flat sorted list of paths with `Origin == VOID`.
- `derived_classes` is a list of full row objects (all 6 fields) for every
  class with `Origin != VOID`.
- `tree` maps each parent (including a sentinel `VOID` key holding the 61
  root classes for downstream convenience) to a list of child row objects
  with all 6 fields (`path`, `name`, `type`, `origin`, `originroot`,
  `class`).

`render_inheritance_map.py` also prints a human-readable parent → children
tree to stdout, and a detailed view of every derived class with its full
Origin / OriginRoot / Class triple.

## Inheritance semantics (Plant Simulation)

See
[`../local-simtalk-execution/references/inheritance-semantics.md`](../local-simtalk-execution/references/inheritance-semantics.md)
for the authoritative `Origin` / `OriginRoot` / `Class` /
`InternalClassType` table, the `VOID` sentinel semantics, and the
worked example.

## Hard rules / Quirks

The 7 universal quirks (#6, #7, #13, modal trap, response framing,
readlog v15+ regression, `infoBox` convention) are inherited from
`local-simtalk-execution`. See
[`../local-simtalk-execution/references/quirks-canonical.md`](../local-simtalk-execution/references/quirks-canonical.md)
for the cross-skill pointer.

### Skill-specific quirks

| # | Quirk | Workaround |
|---|---|---|
| INH-1 | `readlog` v15+ exhibits cumulative-buffer growth; full-tree dumps can exceed the 65536-byte cap and truncate JSON | Batch ≤ 12 paths per `simtalk_run`; tag each batch with a unique `###INH_BATCH###` marker; `rsplit(marker, 1)` to extract only the most recent batch |
| INH-2 | The log field's newlines are JSON-escaped (`\\n`), not real newlines | `log.replace("\\n", "\n").split("\n")` before line-by-line scanning |
| INH-3 | Embedding SimTalk code via shell heredoc corrupts embedded `+` and `\\"` | Build the JSON payload with Python's `json.dumps()` and pass it directly to `socket_client.py` via `--data` (no shell intermediary) |
| INH-4 | `array` is not a SimTalk type — must use `list` | `var l: list[string]` (or just build path literals into code) |
| INH-5 | List literals can't be assigned to `var l: list` ("Left and right sides of the assignment are incompatible") | Generate code with hardcoded path literals (no runtime list construction) |
| INH-6 | A SimTalk `var` declared inside a loop body collides on the second iteration ("'o' is already defined as a local variable") | Declare `var o: object` **once** before the loop; only `o :=` assign inside |
| INH-7 | `probe_inheritance.py` does **NOT** accept `--no-infobox` (positional-args-only parser) | Don't pass the flag — script self-manages `infoBox`; for headless runs see SKILL §"Skill convention" note |

## Path resolution

`str_to_obj(<path>)` is the SimTalk built-in that turns a string path into an
object reference. Paths follow the Plant Simulation convention (leading
`.` per depth level). See
[`../local-simtalk-get-folder-tree/SKILL.md` §"Path resolution"](../local-simtalk-get-folder-tree/SKILL.md#path-resolution)
for the full table.

## Limitations

- **Read-only.** No writes.
- **Candidate paths come from elsewhere.** This skill does NOT enumerate the
  class inventory — it expects a `paths.txt` produced upstream by
  `local-simtalk-get-folder-tree` (or hand-curated). For unknown models,
  run `bfs_full.py` first.
- **`infoBox` requires a GUI session.** The `infoBox(text, false)` call
  targets the Plant Simulation GUI window — if the server is running
  headless, the call still returns success but no box appears. There is
  **no `--no-infobox` flag** on this script (see INH-7); to suppress
  visual chatter in CI / headless contexts, run under a headless
  Plant Simulation frame.
- **Batch size 12 is empirical.** With the v15+ `readlog` regression, larger
  batches risk cumulative-buffer overflow; smaller batches mean more
  round-trips. 12 paths/batch balances speed and reliability.
- **Some classes can have `Class == Origin == OriginRoot` or unusual
  chains.** The render script prints all three values for inspection —
  don't rely on a single attribute alone when reasoning about the
  inheritance hierarchy.

## Key files

- `scripts/probe_inheritance.py` — batch probe + readlog extraction; writes TSV
- `scripts/render_inheritance_map.py` — renders parent→children tree from TSV
- `references/exploration-log.md` — what was discovered in the 2026-08-26
  inheritance probe of the loaded model
- `references/protocol-notes.md` — the v15 readlog workarounds in detail
- `data/inheritance_map.json` — captured inheritance map (65 classes: 61 root
  built-ins + 4 user-defined derived)
- `data/inheritance_raw.tsv` — captured raw probe data
- `log/test-session-20260826-v1.md` — full test session log

## Related skills

- `local-simtalk-execution` — the underlying TCP transport skill; consult
  its `references/lifelines.md` for protocol details before modifying these
  scripts.
- `local-simtalk-get-folder-tree` — produces the candidate-class inventory
  (`paths.txt`) that this skill consumes.
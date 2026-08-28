---
name: local-simtalk-read-library
description: Read the **Method objects** in a loaded Plant Simulation model — capture each Method's metadata (path, name, type, encrypted flag, NumInExecution) and its **source code** (`&Method.Program`) — by sending SimTalk to the running server via `local-simtalk-execution`. Use when the user wants to "understand this model", "dump all the SimTalk code", "show me every method's source", "give me a library inventory with bodies", "what does Method X actually do", "which methods are encrypted", "which methods have syntax errors". Produces a per-method JSON dump (metadata + verbatim source) that downstream skills can index, search, or render. Composes `local-simtalk-get-folder-tree` (to enumerate Method paths) and `local-simtalk-get-class-inheritance` (to know which Method objects live on which class). This skill does NOT modify the server model — it only reads.
---

# local-simtalk-read-library

Read-only **source-code inventory** of every Method object visible in a loaded
Plant Simulation model. For each Method, captures:

- identity (`path`, `name`, `InternalClassType`)
- state (`Encrypted`, `HasSyntaxError`, `NumInExecution`)
- the verbatim **SimTalk source** (`&Method.Program`)

Output is a JSON dump that lets a downstream reader answer
"what does this model actually do?" without touching Plant Simulation.

This skill **does not** talk to the server directly — it composes SimTalk
that does, then wraps the result. It depends on:

- **`local-simtalk-execution`** for TCP transport (Quirk-aware)
- **`local-simtalk-get-folder-tree`** for the candidate-path inventory
  (gives us the list of Method paths to probe)
- **`local-simtalk-get-class-inheritance`** (optional) for understanding
  which Method lives on which user-defined class — useful when reasoning
  about overrides vs. inherited bodies

## When to use

- "Give me a library dump of every Method in this model"
- "Show me the source code of `<method-path>`"
- "Which methods have syntax errors?"
- "Which methods are encrypted / hidden?"
- "I want to understand the model — read all the SimTalk code"
- "Compare user-defined Method bodies against their Origin chain"

Do **not** use this skill for:

- Reading non-Method object attributes (that's `local-simtalk-execution` direct)
- Editing source code (writes are out of scope)
- Running a simulation
- Enumerating folder structure (use `local-simtalk-get-folder-tree`)

## How it works

The skill is a **3-step pipeline**:

1. **Inventory** — `local-simtalk-get-folder-tree` enumerates the folder
   tree down to a chosen depth; we filter its JSON for `type == "Method"`
   nodes to get a candidate-path list.
2. **Probe** — `scripts/probe_methods.py` batches the candidate paths in
   groups of 8 and sends one `simtalk_run` per batch. Each batch:
   - prints a `###LIB_HEADER<id>###` marker followed by per-method
     metadata lines (`PATH=...`, `NAME=...`, `TYPE=...`, `ENCRYPTED=...`,
     `HAS_SYNTAX_ERROR=...`, `NUM_IN_EXECUTION=...`)
   - then a `###LIB_BODY<id>###` marker, followed by the verbatim
     source code (printed via `print &o.Program`), followed by a
     `###LIB_END<id>###` marker
   - We then parse the most-recent batch's three markers (using
     `rsplit`, exactly like the inheritance probe — see
     `references/protocol-notes.md` §1).
3. **Render** — `scripts/render_library.py` aggregates the probe output
   into a single `data/library_dump.json` and prints a human-readable
   summary: total Methods, count encrypted / has-syntax-error / empty,
   per-Method one-line summaries, and (when run with `--show-source`)
   the verbatim source body of every Method.

A convenience driver `scripts/read_library.py` chains the three steps
end-to-end (run folder-tree → filter Methods → probe → render). It
returns the **per-Method library dump** as a structured JSON object
suitable for search / index / LLM ingestion.

Both probe scripts depend on:
- `local-simtalk-execution/scripts/socket_client.py` (raw TCP transport —
  used directly to avoid shell-escaping the source code, which can
  contain literal `+`, `\\"`, and embedded `if`/`end` keywords).

### Skill convention: always announce with `infoBox`

Per the `local-simtalk-execution` v18 → v19 convention, every invocation
opens a non-modal `infoBox(text, false)` on the Plant Simulation GUI
before doing any work and closes it (defensively twice) on exit.

| Stage | What the script does |
|---|---|
| Entry | `infoBox("[probe_methods] start: paths=<N> batch=<B>", false)` |
| Per-batch progress | `infoBox("[probe_methods] batch <i>/<B>: paths=<start>-<end>", false)` |
| Exit (success or failure) | `infoBox("", false)` **twice** — defensive double-close |

The second argument `false` is the modal flag — non-modal so it never
freezes the GUI while batch round-trips are in flight. Pass
`--no-infobox` to suppress for headless / CI runs.

## Usage

```bash
# === End-to-end pipeline (recommended) ===
# 1) Run folder-tree once (depth 5 to catch nested Methods in custom
#    Frames; depth 4 is enough for typical models).
python3 ../local-simtalk-get-folder-tree/scripts/bfs_full.py --no-infobox . 5 data/tree.json

# 2) Filter the tree to candidate Method paths (we expose a helper).
python3 - <<'PY'
import json
tree = json.load(open("data/tree.json"))
methods = []
def walk(n):
    if n.get("type") == "Method":
        methods.append(n["path"])
    for c in n.get("children", []):
        walk(c)
walk(tree)
with open("data/method_paths.txt", "w") as f:
    for p in sorted(set(methods)):
        f.write(p + "\n")
print(f"wrote {len(methods)} method paths")
PY

# 3) Probe each method (Program + metadata).
python3 scripts/probe_methods.py --no-infobox \
  data/method_paths.txt data/methods_raw.tsv

# 4) Render the library dump + human-readable summary.
python3 scripts/render_library.py data/methods_raw.tsv data/library_dump.json
```

Or, with the end-to-end driver:

```bash
python3 scripts/read_library.py --no-infobox \
  --tree-depth 5 \
  --out data/library_dump.json
```

The driver handles steps 2–4; you only need to point it at a folder-tree
JSON or let it call `bfs_full.py` for you.

### Single-method shortcut

To dump just one method (no batch, no marker):

```bash
python3 - <<'PY'
import json, subprocess
path = ".Models.Model.init"
code = f'''
var o: object := str_to_obj("{path}")
print "PATH=" + str_to_obj("{path}").Name
print &o.Program
'''
payload = json.dumps({"type":"simtalk_run",
                      "action_id":"x",
                      "simtalk_code":code}) + "||END||"
subprocess.run(["python3",
  "skills/local-simtalk-execution/scripts/socket_client.py",
  "--host","host.docker.internal","--port","50007",
  "--data", payload,
  "--resp-mode","delimiter","--resp-delimiter","||END||",
  "--timeout","30"])
PY
```

## Output shape

### `data/methods_raw.tsv` (probe output)

Tab-separated, one row per Method:

```
<path>\t<name>\t<type>\t<encrypted:bool>\t<has_syntax_error:bool>\t<num_in_execution:int>\t<program_len:int>\t<program:str>
```

`<program:str>` is the verbatim SimTalk source with literal `\n` (two
characters: backslash, `n`) embedded where Plant Simulation uses real
newlines. The renderer decodes this on read.

### `data/library_dump.json` (rendered output)

```json
{
  "captured_at": "2026-08-26",
  "total_methods": 27,
  "encrypted_methods": [ ".Models.Model.SecretLogic", ... ],
  "syntax_error_methods": [],
  "empty_methods": [ ".Models.Model.unusedInit", ... ],
  "methods": [
    {
      "path": ".Models.Model.init",
      "name": "init",
      "type": "Method",
      "encrypted": false,
      "has_syntax_error": false,
      "num_in_execution": 0,
      "program_len": 142,
      "program": "// Initialize the model\nparam ...\n..."
    },
    ...
  ]
}
```

- `encrypted_methods` — paths where `&o.Encrypted` returned `true`. The
  `program` field for these is the literal string `<encrypted>` — we
  cannot read encrypted source code (the server returns it but it is
  opaque; we record the fact and skip rather than surface bogus bytes).
- `syntax_error_methods` — paths where `&o.HasSyntaxError` returned
  `true`. Useful for "what's broken in this model" queries.
- `empty_methods` — paths whose `program_len` is 0 (newly-inserted
  Methods with no body yet).

### Human-readable summary (stdout)

`render_library.py` prints a per-Method one-line summary like:

```
.Models.Model.init                       Method   142 B   ok
.Models.Model.SecretLogic                Method   --- B   ENCRYPTED
.Models.Model.drain                      Method    87 B   SYNTAX ERROR
.Models.Model.unusedInit                 Method     0 B   empty
```

Plus aggregate counts at the top. With `--show-source`, the verbatim
source of every Method is also printed.

## Hard rules / Quirks

Inherited from `local-simtalk-execution/references/lifelines.md` —
see that doc for the full list; the most relevant subset:

| Rule | Why |
|---|---|
| `type` field must be one of `ping` / `simtalk_syntax` / `simtalk_run` / `readlog` | Unknown types cause silent server-side hang (Quirk #13) |
| Use `--resp-mode delimiter --resp-delimiter '\|\|END\|\|'` for reply framing | Server never closes the socket (lifelines §2) |
| `simtalk_run` `data` field is **always** empty | Quirk #6 — server doesn't serialize return values |
| Runtime errors return `result:"success"` with `log:"code execute failed..."` | Quirk #7 — must double-check (script exit codes 10/11) |
| Avoid `prompt` / `infoBox` / writing undeclared global attrs | Modal trap — server blocks until GUI click (lifelines §4) |
| **Always `infoBox(text, false)` on entry, close twice on exit** | Skill convention from `local-simtalk-execution` v18→v19 |

### Skill-specific quirks

| # | Quirk | Workaround |
|---|---|---|
| LIB-1 | Method's source code can be **large** (multi-KB). Embedding it in a `simtalk_run` payload via shell heredoc corrupts it (lifelines §A2) | Build the JSON payload with Python's `json.dumps()` and pass it directly to `socket_client.py` via `--data` (no shell intermediary) |
| LIB-2 | `readlog` v15+ exhibits cumulative-buffer growth; library dumps with 20+ methods can exceed the 65536-byte cap and truncate JSON | Batch ≤ 8 Methods per `simtalk_run`; tag each batch with a unique `###LIB_HEADER<id>###` marker; `rsplit(marker, 1)` to extract only the most recent batch |
| LIB-3 | The `log` field's newlines are JSON-escaped (`\\n`), not real newlines | `log.replace("\\n", "\n").split("\n")` before line-by-line scanning |
| LIB-4 | An encrypted Method's `Program` returns opaque bytes (the encryption is server-side) | Skip those rows: when `Encrypted == true`, replace `program` with the literal string `"<encrypted>"` so downstream tools can detect and ignore |
| LIB-5 | Reading `&Method.Program` via `str_to_obj(p).Program` is the **same** as `&str_to_obj(p).Program` — both work because `str_to_obj` returns an `object` reference. But `Method` requires `&` for direct attribute access (`MyMethod.Program` won't compile because plain `MyMethod` is the source-code content, not the object) | Always go through `var o: object := str_to_obj(p); &o.Program` |
| LIB-6 | `infoBox` requires a GUI session | Use `--no-infobox` in CI / headless contexts |
| LIB-7 | The TSV field 8 (`program`) is **multi-line** — naïve per-line `ln.split("\t")` in `render_library.py` parses a 4-method dump into 7+ phantom rows, with each method's `program` containing the metadata lines of the next method | `render_library.py` `parse_tsv` detects record headers (first field starts with `.`, ≥ 8 tab fields) and accumulates continuation lines into field 8 until the next record starts. See `references/protocol-notes.md` §LIB-10 |

## Method-object facts (from the knowledge base)

The probe reads attributes documented in
`01-plantsimulation-knowledge/.../Method/attributes` and
`.../Method/read-only-attributes`:

| Attribute | Type | Read via | Notes |
|---|---|---|---|
| `Program` | string (rw) | `&m.Program` | The verbatim source code |
| `Encrypted` | boolean (ro) | `&m.Encrypted` | If true, source is opaque |
| `HasSyntaxError` | boolean (ro) | `&m.HasSyntaxError([byref ErrorMessage:string, byref Line:integer])` | Returns true if source has compile errors |
| `NumInExecution` | integer (ro) | `&m.NumInExecution` | Count of in-flight invocations |
| `RandomSeed` | integer (rw) | `&m.RandomSeed` | Per-Method RNG stream |
| `UsingNewSyntax` | boolean (rw) | `&m.UsingNewSyntax` | SimTalk 2.0 vs 1.0 mode |

We read the first four; the last two are read-write state that the
skill currently does not capture (call out for future expansion if
needed).

## Path resolution

`str_to_obj(<path>)` resolves a path-string to an `object` reference.
Paths follow Plant Simulation convention (leading `.` per depth level).
See `local-simtalk-get-folder-tree/SKILL.md` §"Path resolution".

The basis identifier itself is **anonymous** — `obj_to_str(basis)`
returns the empty string. That's why folder-tree uses `root_path: ""`.

## Limitations

- **Read-only.** No writes — the skill never assigns `Program` or
  calls `encrypt` / `decrypt` / `execute`.
- **Encrypted source is opaque.** When `&m.Encrypted` is `true`, the
  `program` field is recorded as `"<encrypted>"`. There is no way to
  recover encrypted source through this protocol (you would need the
  encryption password + `decrypt` permission, which the skill does
  not attempt).
- **Depends on upstream inventory.** This skill does NOT enumerate the
  folder tree itself — it expects a `method_paths.txt` produced
  upstream (or use the `read_library.py` driver which calls
  `bfs_full.py` for you).
- **Batch size 8 is empirical.** With the v15+ `readlog` regression,
  larger batches risk cumulative-buffer overflow. 8 Methods/batch
  balances speed and reliability for typical models (where Methods
  range 100 B – 5 KB).
- **`infoBox` requires a GUI session.** `--no-infobox` in CI / headless.
- **No cross-class diff.** The skill does not currently compare Method
  bodies across an `Origin` chain (i.e. "what did the user override
  from the base class?"). Future work — for now, see
  `local-simtalk-get-class-inheritance` to identify which Methods
  live on a derived class.

## Key files

- `scripts/probe_methods.py` — batch probe + marker-based readlog extraction
- `scripts/render_library.py` — aggregates probe rows into `library_dump.json`
- `scripts/read_library.py` — end-to-end driver: BFS → filter Methods → probe → render
- `references/protocol-notes.md` — protocol-level workarounds specific to reading Method source
- `references/exploration-log.md` — what was discovered in the 2026-08-26 read-library probe
- `example/example.md` — end-to-end walk-through with observed outputs
- `data/library_dump.json` — captured library dump (regenerated by probe)
- `data/methods_raw.tsv` — captured raw probe data (regenerated by probe)
- `log/test-session-20260826-v1.md` — full test session log

## Related skills

- `local-simtalk-execution` — the underlying TCP transport; consult
  its `references/lifelines.md` before modifying these scripts.
- `local-simtalk-get-folder-tree` — produces the candidate-Method
  inventory this skill consumes.
- `local-simtalk-get-class-inheritance` — produces the
  Origin / OriginRoot / Class map; useful for "which class is this
  Method's owner" and "is this Method inherited or overridden".
- `01-plantsimulation-knowledge/.../Method/` — authoritative docs on
  the Method object (Program / HasSyntaxError / Encrypted / etc.).
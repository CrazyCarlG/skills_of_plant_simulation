# Example: Using `local-simtalk-read-library`

> Written from the 2026-08-26 exploration session. Each claim traces to
> a recorded test run; what's listed as observed is observed, not
> inferred.

## Goal

Take a loaded Plant Simulation model and produce a **library dump** —
a JSON file containing the verbatim SimTalk source of every Method
object in the model, plus per-Method metadata (encrypted flag, syntax
error status, in-execution counter).

## 1. Setup

> **所有"必须 / 禁止 / 会挂死"的铁律集中在 `local-simtalk-execution/references/lifelines.md`**，包括：
> - WSL2 容器连接目标（`host.docker.internal:50007`）
> - 回复分帧必须用 `--resp-mode delimiter --resp-delimiter '||END||'`
> - `type` 字段白名单（未知 type 静默挂死——Quirk #13）
> - 模态陷阱（`prompt` / `infoBox` / 写未声明 attr）
> - 当前 readlog 状态（v15+ 已回归 v12）
> - 成功判据（Quirk #6 / #7）

This skill adds these **skill-specific quirks** (full list in
`../references/protocol-notes.md`):

| # | Quirk | Workaround |
|---|---|---|
| LIB-1 | Embedding source code via shell heredoc corrupts `+` and `\\"` | Build JSON with `json.dumps()`, pass via `--data` |
| LIB-2 | readlog v15+ cumulative buffer overflow at > 50 KB | Batch ≤ 8 Methods per `simtalk_run` |
| LIB-3 | `log` field newlines are `\\n` | `log.replace("\\n", "\n").split("\n")` |
| LIB-4 | Encrypted `&Method.Program` is opaque | Print `<encrypted>` placeholder when `Encrypted=true` |
| LIB-5 | Method attributes need `&` prefix | Always `&o.Encrypted`, never `o.Encrypted` |

---

## 2. End-to-end pipeline (recommended)

```bash
# Headless — no infoBox chatter
python3 scripts/read_library.py --no-infobox \
    --tree-depth 5 \
    --out data/library_dump.json
```

Internally this:

1. Calls `../local-simtalk-get-folder-tree/scripts/bfs_full.py --no-infobox . 5 data/tree.json`
2. Filters `data/tree.json` for `type == "Method"` nodes
3. Writes `data/method_paths.txt`
4. Calls `scripts/probe_methods.py --no-infobox data/method_paths.txt data/methods_raw.tsv`
5. Calls `scripts/render_library.py data/methods_raw.tsv data/library_dump.json`

A 27-Method model takes about 5 round-trips × ~2s = ~10 seconds
end-to-end.

---

## 3. Step-by-step pipeline (for debugging)

```bash
# Step 1 — get the folder tree (depth 5 covers nested Frames)
python3 ../local-simtalk-get-folder-tree/scripts/bfs_full.py --no-infobox \
    . 5 data/tree.json

# Step 2 — filter for Method paths
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
print(f"{len(methods)} methods")
PY

# Step 3 — probe each Method (Program + metadata)
python3 scripts/probe_methods.py --no-infobox \
    data/method_paths.txt data/methods_raw.tsv

# Step 4 — render the library dump
python3 scripts/render_library.py data/methods_raw.tsv data/library_dump.json

# Bonus: also dump every Method's full source to stdout
python3 scripts/render_library.py --show-source \
    data/methods_raw.tsv data/library_dump.json
```

---

## 4. Output — `data/library_dump.json`

Shape (verified):

```json
{
  "captured_at": "2026-08-26",
  "total_methods": 27,
  "encrypted_methods": [],
  "syntax_error_methods": [],
  "empty_methods": [".Models.Model.unusedInit"],
  "void_methods": [],
  "methods": [
    {
      "path": ".Models.Model.init",
      "name": "init",
      "type": "Method",
      "encrypted": false,
      "has_syntax_error": false,
      "num_in_execution": 0,
      "program_len": 142,
      "program": "// Initialize the model\nparam Sender:object\n..."
    },
    ...
  ]
}
```

The `program` field is the verbatim SimTalk source (UTF-8, real
newlines, no escaping).

---

## 5. Reading the human-readable summary

`scripts/render_library.py` also prints a per-method summary to
stdout:

```
Total Methods captured: 27
  Encrypted:             0
  Has syntax error:      0
  Empty (no source):     1
  VOID / unresolved:     0

============================================================================
METHOD SUMMARY (path | type | size | status)
============================================================================
  .Models.Model.drain                          Method       87 B   ok
  .Models.Model.init                           Method      142 B   ok
  .Models.Model.unusedInit                     Method        0 B   empty
  ...
```

`--show-source` adds the full source of every Method below the
summary.

---

## 6. Single-Method shortcut

To dump just one method (no batch, no marker):

```bash
python3 - <<'PY'
import json, subprocess
path = ".Models.Model.init"
code = (
    f'var o: object := str_to_obj("{path}")\n'
    f'print "NAME=" + &o.Name\n'
    f'print "TYPE=" + o.InternalClassType\n'
    f'print "ENCRYPTED=" + to_str(&o.Encrypted)\n'
    f'print "HAS_SYNTAX_ERROR=" + to_str(&o.HasSyntaxError)\n'
    f'print "NUM_IN_EXECUTION=" + to_str(&o.NumInExecution)\n'
    f'print &o.Program\n'
)
payload = json.dumps({"type":"simtalk_run",
                      "action_id":"x",
                      "simtalk_code":code}) + "||END||"
subprocess.run(["python3",
  "/root/skills_of_plant_simulation/skills/local-simtalk-execution/scripts/socket_client.py",
  "--host","host.docker.internal","--port","50007",
  "--data", payload,
  "--resp-mode","delimiter","--resp-delimiter","||END||",
  "--timeout","30"])
PY
```

But — and this is important — the value never reaches the socket
(Quirk #6). The output above shows up only in the Plant Simulation
GUI Console, not on stdout. To capture it programmatically, you
need the marker + readlog pattern used by `probe_methods.py`.

---

## 7. Combining with `local-simtalk-get-class-inheritance`

The library dump gives you the **what** (source code); the inheritance
map gives you the **who** (which class owns the method). To combine:

```bash
# 1) Get the inheritance map
python3 ../local-simtalk-get-class-inheritance/scripts/probe_inheritance.py \
    data/method_paths.txt data/inheritance_raw.tsv
python3 ../local-simtalk-get-class-inheritance/scripts/render_inheritance_map.py \
    data/inheritance_raw.tsv data/inheritance_map.json

# 2) Get the library dump
python3 scripts/read_library.py --no-infobox \
    --tree-in data/tree.json \
    --out data/library_dump.json

# 3) Join on path
python3 - <<'PY'
import json
inh = {m["path"]: m for m in json.load(open("data/inheritance_map.json"))["derived_classes"]}
lib = json.load(open("data/library_dump.json"))
for m in lib["methods"]:
    o = inh.get(m["path"])
    if o:
        print(f'{m["path"]} inherits from {o["origin"]} ({o["type"]})')
PY
```

This gives you "method X is on class Y which inherits from built-in Z".

---

## 8. Limitations observed

- **Encrypted source** — when `Encrypted=true`, the program field is
  `<encrypted>`. There is no way to recover encrypted source through
  this protocol (the `decrypt` method requires the original
  encryption password).
- **Static snapshot** — the library dump reflects the model state at
  probe time. If the model is being edited or simulated, re-run the
  probe to refresh.
- **No streaming** — the probe is O(N) batches where N = #Methods /
  8. For a 100-Method model, expect ~15 seconds end-to-end.
- **Per-method unique** — each method is probed exactly once; we
  don't detect Methods added between batches (the folder-tree BFS
  was a snapshot too).
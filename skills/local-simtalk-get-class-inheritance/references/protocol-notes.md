# Protocol Notes — Class Inheritance Probe

These are the protocol-level workarounds the `local-simtalk-get-class-inheritance`
skill uses to extract `Origin` / `OriginRoot` / `Class` from the Plant
Simulation server. They're accumulated from the 2026-08-26 exploration
session; the rationale for each is recorded so future maintainers don't
have to re-derive them.

> **Companion docs**:
> - `local-simtalk-execution/references/lifelines.md` — the upstream
>   transport-skill quirks (Quirk #6 / #7 / #13 etc.) that this skill
>   inherits.
> - `local-simtalk-get-folder-tree/references/exploration-log.md` — the
>   parent skill that produced the candidate-class inventory.

---

## §1 — The v15+ `readlog` regression and the marker-based extraction trick

### What it is

Since the server's readlog implementation was bumped to v15, the
cumulative log buffer exhibits **exponential growth** when called in a
tight loop. Symptoms:

- Single `print` right after `simtalk_run` still works — the marker line
  appears in the `log` field.
- Calling `readlog` repeatedly (e.g. without intervening server work)
  causes the buffer to grow by ~2× per call, hitting a **65536-byte
  truncation cap** within 4–6 round-trips.
- Truncated JSON makes strict `json.loads()` fail with
  `Unterminated string` / `Expecting ',' delimiter`.

### Why it matters here

The class-inheritance probe needs to send up to 65 paths. If you try to
pack them all into one `simtalk_run`, you get:
- A very long SimTalk program (errors can be silently truncated).
- A huge single `readlog` response that exceeds the buffer cap.

### The fix — small batches + unique marker per batch

`scripts/probe_inheritance.py` splits the path list into batches of 12
paths (empirical). For each batch it:

1. Generates SimTalk that begins with `print "###INH_BATCH###"`, then for
   each path:
   ```simtalk
   o := str_to_obj("<p>")
   if o = void then print "<p> | VOID"
   else print "<p> | name=" + o.Name + " | type=" + o.InternalClassType
        + " | Origin=" + obj_to_str(o.Origin) + " | OriginRoot=" + obj_to_str(o.OriginRoot)
        + " | Class=" + obj_to_str(o.Class)
   end
   ```

2. Sends the batch via `socket_client.py` (`simtalk_run`).

3. Sends a `readlog` and parses the JSON envelope (with a regex fallback
   for truncated responses — `re.search(r'"log":\s*"(.*?)"\s*\}\|\|END\|\|', raw, re.S)`).

4. Extracts only the content from the most recent marker using
   `log_text.rsplit("###INH_BATCH###", 1)[-1]`. This works because the
   `print "###INH_BATCH###"` line sits at the **start** of every batch's
   output, so `rsplit(..., 1)[-1]` returns just this batch's lines.

5. Parses each `<path> | name=... | type=... | Origin=... | OriginRoot=...
   | Class=...` line via regex into a row dict.

The buffer-growth problem still happens, but each batch's data is fully
captured before the buffer gets too large, so we never lose data.

---

## §2 — Embedded `+` and `\\"` in shell heredocs corrupt SimTalk code

### What it is

SimTalk print statements for multi-attribute output look like:

```simtalk
print "<p> | name=" + o.Name + " | type=" + o.InternalClassType + " | Origin=" + obj_to_str(o.Origin)
```

The `+` characters and the escaped `\\"` inside shell heredocs cause two
distinct problems:

- Bash treats `+` literally in unquoted heredocs, but **strips** the
  backslashes from `\\"`, turning `"<p> | name=" + o.Name` into
  `"<p> | name=" + o.Name` with broken string concat.
- Quoting rules in `bash -c`/`zsh` differ; some quoting paths silently
  mangle the code such that the server receives
  `rint ".Fluids.Portioner | ...` (leading `"p` stripped to `rint`).

### The fix — build the JSON payload in Python and pass it via `--data`

`scripts/probe_inheritance.py` does NOT pipe SimTalk through the shell.
It builds the JSON envelope with Python's `json.dumps()` and passes it
straight to `socket_client.py` via `--data`:

```python
payload = json.dumps({"type": "simtalk_run",
                      "action_id": os.urandom(8).hex(),
                      "simtalk_code": code}) + "||END||"
subprocess.run([sys.executable, SOCKET_CLIENT,
                "--host", HOST, "--port", str(PORT),
                "--data", payload,
                "--resp-mode", "delimiter",
                "--resp-delimiter", "||END||",
                "--timeout", "30"], ...)
```

Because `subprocess.run([...])` (list form, not string) bypasses the
shell entirely, no quoting is applied — the JSON byte stream goes
verbatim to the server.

The code string itself is built with Python f-strings, which do their
own (well-tested) escaping:

```python
esc = p.replace('\\', '\\\\').replace('"', '\\"')
lines.append(f'o := str_to_obj("{esc}")')
```

---

## §3 — SimTalk type quirks

### `array` is not a SimTalk type — use `list`

An earlier draft used:

```simtalk
var paths: array[string]
paths := [".MaterialFlow.Station", ".MaterialFlow.Conveyor"]
```

The server returned `Syntax error near line 2 at 'array'`. SimTalk's
container types are `list`, `table`, `dictionary`, etc. — not `array`.
Fix: `var paths: list[string]` (and accept the Quirk §10.2 limitation
that list literals can't be assigned to a typed variable — see below).

### List literals can't be assigned to `var l: list` (Quirk §10.2)

Trying:

```simtalk
var paths: list[string]
paths := [".a", ".b"]
```

Gives: `Left and right sides of the assignment are incompatible.`

**Fix**: don't build a list at all. Bake the paths as hardcoded SimTalk
literals directly into the generated code. This sidesteps the issue and
also matches the `local-simtalk-execution/references/lifelines.md` §A2
guidance that `param` declarations are silently accepted but not bound,
so path-as-param doesn't work either.

### `var` declared inside a loop body collides on the second iteration

If you write:

```simtalk
for i := 1 to 5
    var o: object
    o := str_to_obj(".MaterialFlow.Station")
end
```

The second iteration raises `'o' is already defined as a local variable`.

**Fix**: declare `var o: object` **once** before the loop, only `o :=`
inside.

---

## §4 — Parsing the JSON-escaped log field

### What it is

The `log` field in the `readlog` response has newlines as the literal
two-character sequence `\\n` (backslash-n), not real newlines. A naive
`log.split("\n")` returns the entire content as one chunk.

### The fix

```python
chunks = log_text.replace("\\n", "\n").split("\n")
```

Only the newline escape is replaced; other escapes (`\\`, `\"`, etc.) are
left intact (none of them affect our line-by-line scan).

---

## §5 — Detecting `VOID` responses

When `str_to_obj(p)` returns `VOID` (path doesn't exist), `o.Name`
etc. would throw `object reference is void`. The probe script guards
with:

```simtalk
if o = void then print "<p> | VOID"
else print "<p> | name=" + o.Name + ...
end
```

On the client side:

```python
VOID_LINE_RE = re.compile(r'^(?P<path>\S+)\s*\|\s*VOID\s*$')
...
m = VOID_LINE_RE.match(payload)
if m:
    rows[key] = {"path": key, "name": "", "type": "",
                 "origin": "VOID", "originroot": "VOID",
                 "cls": "VOID"}
```

This keeps the row shape consistent — VOID rows are still 6 fields
(origin / originroot / cls all `VOID`), so downstream renderers don't
need a special case.

---

## §6 — Reproducible batch-size heuristic

The empirical sweet spot is **12 paths per batch**. With 65 paths this
gives 6 batches (5 × 12 + 1 × 5), each producing a small enough
`readlog` payload to fit under the buffer cap with margin. Smaller
batches would mean more round-trips; larger batches risk overflow.

If a future server version raises the cap, the batch size can be
increased. To find the new ceiling empirically, double the batch size
until `readlog` responses start truncating.

---

## §7 — Re-using the marker trick for any batched readlog workload

The marker + `rsplit(..., 1)` extraction isn't specific to this skill —
any skill that wants to split a long probe into multiple
`simtalk_run` + `readlog` round-trips can adopt the same pattern. The
recipe is:

1. Choose a unique marker string per batch (random hex is overkill but
   safe — `###INH_BATCH###` is fine if only one skill is talking).
2. Begin every batch with `print "<marker>"` BEFORE the real probe
   output.
3. After `readlog`, `rsplit(marker, 1)[-1]` returns only the content
   since the most recent marker.
4. Combine batches by appending to a master dict keyed by path.

The `local-simtalk-get-folder-tree` skill uses a similar pattern
(`###BFS_MARKER###`) — see its `scripts/bfs_one_level.py`.

---

## §8 — Pre-filtering candidate paths to avoid empty returns

### What it is

When a candidate path's target object is **not a class-defining type**
(Frame / Dialog / Part / etc.), the probe's `print` block for that path
returns nothing useful — `Origin` / `OriginRoot` / `Class` come back
empty or VOID. Empirically, walking the full BFS tree and probing every
node gives **40-60% empty rows**.

Specifically (2026-08-27 `orientation-summary-from-fresh-data-2.md`):
- 40 candidate paths from a teaching-model BFS walk
- 24 returned nothing (`Comment`, `DataTable`, etc.)
- 16 captured (all root classes with `Origin = VOID`)

### Why it matters

Each empty row still costs:
- 1 TCP round-trip inside the batch
- Buffer growth toward the v15+ 65536-byte cap (see §1)
- A row entry that downstream renderers must skip

Pre-filtering the BFS tree down to type classes that meaningfully expose
`Origin` cuts round-trips by ~60% with no information loss.

### The fix — filter by `type` before probing

```python
import json

tree = json.load(open("data/basis_tree_depth5_fresh.json"))
KEEP_TYPES = {"Frame", "Dialog", "TableFile", "Method", "Part"}

paths = set()
def walk(n):
    if n.get("type") in KEEP_TYPES and n.get("type") not in {"Folder"}:
        # Top-level Frame nodes usually hold the *class*, not the instance
        # — keep them as candidates; the probe will VOID-mark the empty ones
        paths.add(n["path"])
    for c in n.get("children", []):
        walk(c)
walk(tree)
with open("paths.txt", "w") as f:
    for p in sorted(paths):
        f.write(p + "\n")
```

The 5-type filter (`Frame` / `Dialog` / `TableFile` / `Method` / `Part`)
captures every user-defined class that meaningfully carries an
inheritance chain. `Comment` / `DataTable` / `Variable` / `Chart` /
`Button` / `HtmlReport` / `DataList` / `FileLink` / `Socket` are
**excluded** — they typically don't expose `Origin` at the
inheritance-probe layer (they're leaves or single-instance templates,
not class definitions).

### When to relax the filter

If a downstream skill needs to know "is this `Comment` template
derived from a user-defined base?", add `Comment` to `KEEP_TYPES` and
expect 30-50% empty rows. The empty rows are still safe to ignore in
the rendered output (`render_inheritance_map.py` already drops rows
with all three of `origin`/`originroot`/`cls` == `""`).

### Sanity check

After probing, the ratio of root-classes (`origin == "VOID"`) to
derived-classes (`origin != "VOID"`) should match the model's design
intent. For example, in a teaching model:
- 13 root Frames in `.ModelAssistants.*` (top-level toolkit)
- 17 derived Dialogs (all originating from
  `.ModelAssistants.BasicObjects.UserInterface.Dialog`)

If the ratio is wildly off (e.g., 0 derived when the model is supposed
to have a dozen subclasses), the pre-filter probably over-pruned.
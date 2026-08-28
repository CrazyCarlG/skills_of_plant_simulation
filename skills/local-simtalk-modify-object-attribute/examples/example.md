# Example: Using `local-simtalk-modify-object-attribute`

> Written from the 2026-08-26 verification session that motivated the creation
> of this skill. All `before → after` values below were captured by
> `print + readlog` round-trips against the live server at
> `host.docker.internal:50007`.

## Setup

```bash
# Confirm the server is reachable
python3 skills/local-simtalk-execution/scripts/simtalk_send.py ping
# Expect: { "type": "ping", "result": "success" }
```

## 1. Read a single attribute

The skill's `--read-only` flag triggers just the read path — no write, no
risk of side effects.

```bash
python3 scripts/attr_modify.py \
    --path .Models.Model.EventController \
    --attr SkipLongEventIntervals \
    --read-only
```

Observed output (matches the live server at the time of the test):

```
=== .Models.Model.EventController.SkipLongEventIntervals (None) ===
  SkipLongEventIntervals: true
```

> Note: `--read-only` mode doesn't require `--type` because the code path only
> reads, never writes — the type is irrelevant.

## 2. Modify a boolean attribute and auto-restore

```bash
python3 scripts/attr_modify.py \
    --path .Models.Model.EventController \
    --attr SkipLongEventIntervals \
    --value false \
    --type boolean \
    --restore
```

Observed output:

```
=== .Models.Model.EventController.SkipLongEventIntervals (boolean) ===
  SkipLongEventIntervals: true -> false

=== restoring ===
  restore OK
```

The script:
1. Read `before = true`
2. Wrote `false`
3. Read `after = false` (confirmed the change stuck)
4. On exit, restored `true` (printed via the `restored: <path>.<attr> := <val>` line)

## 3. Modify a numeric attribute

```bash
python3 scripts/attr_modify.py \
    --path .Models.Model.EventController \
    --attr RealtimeScale \
    --value 5 \
    --type real \
    --restore
```

Observed output:

```
=== .Models.Model.EventController.RealtimeScale (real) ===
  RealtimeScale: 3 -> 5

=== restoring ===
  restore OK
```

> `RealtimeScale` is `real` typed, but Plant Simulation coerces integer
> literals cleanly. The `to_str()` round-trip preserves the rendered form
> (`5` not `5.0`), which is fine because Plant Simulation re-coerces on write.

## 4. Batch — modify three attributes at once

```bash
python3 scripts/attr_modify.py \
    --path .Models.Model.EventController \
    --batch SkipLongEventIntervals=false:boolean \
           RealtimeScale=5:real \
           RandomNumbersVariant=7:integer \
    --restore
```

Observed output:

```
=== .Models.Model.EventController.SkipLongEventIntervals (boolean) ===
  SkipLongEventIntervals: true -> false
=== .Models.Model.EventController.RealtimeScale (real) ===
  RealtimeScale: 3 -> 5
=== .Models.Model.EventController.RandomNumbersVariant (integer) ===
  RandomNumbersVariant: 1 -> 7

=== restoring ===
  restore OK
```

Each attribute gets its own `simtalk_run` (one TCP round-trip per attribute)
so a partial failure on one attribute doesn't leave the others in a
half-modified state — but be aware: the batch is **not transactional**. If
attribute 2 of 3 fails after attribute 1 has already changed, attribute 1
will be modified and `--restore` will still restore **all** captured values
(the successful read of attribute 1 captures its new value, not the
original). For a true transactional restore, do single-attribute runs.

## 5. Manual SimTalk snippet (without the helper)

If you want full control, you can write the SimTalk snippet yourself:

```bash
python3 skills/local-simtalk-execution/scripts/simtalk_send.py \
    --timeout 15 run '
var ec: object := str_to_obj(".Models.Model.EventController")
var before: integer := ec.RandomNumbersVariant
ec.RandomNumbersVariant := 7
var after: integer := ec.RandomNumbersVariant
print "###MARKER###"
print "RandomNumbersVariant: " + to_str(before) + " -> " + to_str(after)
print "###END###"
'

python3 skills/local-simtalk-execution/scripts/simtalk_send.py readlog
```

Expected log output (grep for `###MARKER###`):

```
2026-08-26 12:51:04: ###MARKER###
2026-08-26 12:51:04: RandomNumbersVariant: 1 -> 7
2026-08-26 12:51:04: ###END###
```

> **Caveat:** `readlog` is marked degraded in v15+ (see
> `local-simtalk-execution/references/lifelines.md` §5). In the 2026-08-26
> session it worked reliably for the marker-grep pattern, but you may
> occasionally see stale content or empty markers — retry once before
> assuming the write failed.

## 6. What the helper does NOT do

- It does **not** touch `.SimtalkClaude.*`. If the path contains
  `.SimtalkClaude`, the script exits with code 2 and prints `REFUSED`.
- It does **not** create new attributes. Writing to an undeclared attribute
  triggers the modal-trap hang (lifelines §4) — if you need a new attribute,
  declare it in the Plant Simulation GUI first.
- It does **not** modify the `.spp` / `.psfm` file on disk. This skill talks
  to the running server only.
- It does **not** call methods. Use plain `simtalk_run` for that.

## 7. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `REFUSED: this skill does not write inside .SimtalkClaude.*` | Path contains `.SimtalkClaude` | Pick a different path (out of scope by user convention) |
| `EXEC FAIL: result="success" log="code execute failed..."` | Modal trap (undeclared attr) or `str_to_obj` returned `void` | Check path is loaded; confirm attribute exists in the Plant Simulation knowledge base |
| `WARN: marker not found in log/readlog` | `readlog` degradation (v15+) or simtalk_run errored before printing | Retry once; if still missing, check the GUI console (Window ribbon → Console) manually |
| `RESTORE FAIL` at end of run | Restore `simtalk_run` failed | Manually re-run with the captured `before` value; the failure to restore does **not** roll back already-modified attributes |
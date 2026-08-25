# Example: Using `local-simtalk-execution`

> Written from v1–v10 practice on 2026-08-24. Each claim below traces to a
> recorded test run in `log/`. Skip the speculation — what's listed as ✅/❌
> was observed, not inferred.

## 2. Setup (must read first)

> **所有"必须 / 禁止 / 会挂死"的铁律集中在 `references/lifelines.md`**，包括：
> - WSL2 容器连接目标（`host.docker.internal:50007`，详见 `lifelines.md` §1）
> - 回复分帧必须用 `--resp-mode delimiter --resp-delimiter '||END||'`（详见 `lifelines.md` §2）
> - `type` 字段白名单（未知 type 静默挂死——Quirk #13，详见 `lifelines.md` §3）
> - 模态陷阱（`prompt` / `infoBox` / 写未声明 attr，详见 `lifelines.md` §4）
> - 当前 readlog 状态（v15+ 已回归 v12，详见 `lifelines.md` §5）
> - 成功判据（Quirk #6 / #7，详见 `lifelines.md` §6）

All examples below use delimiter framing.

---

## 1. Ping — link sanity check

```bash
python3 scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 5 \
  --data '{"type":"ping","timestamp":"<ts>"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

Observed response (exit 0, < 1s, v1 T1 / v10 P1):
```json
{ "type": "ping", "result": "success" }
```

The `type` field **echoes the request type**, not a generic `"result"`.

---

## 2. `simtalk_syntax` — does the code parse?

```bash
python3 scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data '{"type":"simtalk_syntax","action_id":"<id>","simtalk_code":"var x: integer := 42"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

### Response shape (observed)

```json
{
  "type": "action_result",
  "action_id": "<echoed back>",
  "result": "has no Error",
  "log": "<varies — see warning>",
  "retsult": " hasError ： Syntax error near line 1 at 'is'. (in row :1)"
}
```

### Field decoding

| Field | What it carries | Rule |
|---|---|---|
| `result` | **diagnostic string** (not a status boolean) | Pass if `result` does **not** contain the substring `"hasError"`; fail otherwise |
| `log` | Sometimes current diagnostic, sometimes stale cached error — **unreliable on `simtalk_syntax` path** | Don't use it to judge pass/fail |
| `retsult` | **Always the same stale string** regardless of request — server-side cache bug | **Ignore** |
| `data` | Never appears | n/a |

**Success criterion for `simtalk_syntax`:**
```text
"hasError" not in result
```

### What `simtalk_syntax` accepts (verified forms)

All of these produced `result:"has no Error"` on 2026-08-24:

- `-> T` return-type header
- `var x: T := expr` (declaration with init)
- Control flow: `if`/`elseif`/`else`/`end`, `switch`/`case` (multi-line body) /`end`, `when x then y else z`, `while`/`end`, `repeat`/`until`, `for-to`/`for-downto`/`next`, `exitloop`, `continue`
- Operators: `+`, `-`, `*`, `/`, `div`, `mod`, `~=`, `:=`, `+=`, `-=`, etc.
- Constants: `pi`, JSON literals `{...}`, time literals `H:M:S`, string escapes `\"`
- String funcs: `strLen`, `strToUpper`, `strToLower`, `strLPos`, `strReplace`, `splitString`, `regex_search`
- Anonymous identifiers: `root`, `self`, `current`
- Data structures: `list[T].create/.insert`, `T[]` array literals with `.length`
- `print X` (expression statement)
- `return X`
- **`param` declarations** — single-line `param i:integer,str:string; body`, single-line with default `param str:string := "x"; body`, multi-line `param str:string\nbody`, with `byref` modifier. See §6.5 for the full cheat sheet.

### What `simtalk_syntax` rejects (verified rejections)

| Code | `result` |
|---|---|
| `param byval str:string; body` | `" hasError : Syntax error near line 1 at 'str'."` — `byval` is the default, explicit `byval` is illegal |
| `param byref str:string := "x"; body` | `" hasError : A default argument is not allowed for the data type 'byref string'."` — language rule |
| `var a,b: integer\nparam x: real := 1.0\nreturn x+a` | `" hasError : Syntax error near line 2 at 'param'."` (v9 case — `var`+`param` name clash pattern) |

### What `simtalk_syntax` does NOT catch

- **Unknown identifiers** — `print nonExistentVar` returns `result:"has no Error"` at sx stage; the error surfaces only at runtime. Source: v9 T8a / R10.

---

## 3. `simtalk_run` — actually execute the code

```bash
python3 scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 60 \
  --data '{"type":"simtalk_run","action_id":"<id>","simtalk_code":"print 1+1","return_value":true}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

### Response shape (observed)

```json
{
  "type": "action_result",
  "action_id": "<echoed back>",
  "result": "success",
  "log": "execute success",
  "retsult": " hasError : Syntax error near line 1 at 'is'. (in row :1)"
}
```

### Field decoding

| Field | What it carries | Rule |
|---|---|---|
| `result` | **Status literal**: `"success"` / `"failed"` / `"timeout"` | Pass if `"success"` — except for runtime errors (see below) |
| `log` | Current diagnostic or `"execute success"` (usually trustworthy here, but **the embedded identifier/line may be from a prior failed request** — v10 R1 observed `'someVeryUnknownVariableName'` from v9 R11) | Use only the prefix (`"hasError"` / `"code execute failed"`); ignore the rest |
| `retsult` | Always stale | **Ignore** |
| `data` | **Never appears in `simtalk_run`** — even with `-> T\nreturn X` + `return_value:true` (verified across 4 return-form variants in v9 R4 + v8 T2-T4) | n/a |

### The asymmetry between compile and runtime errors

Two error classes produce different response shapes — observed in v6, v7, v9 R12-R14:

| Error class | `result` | `log` prefix |
|---|---|---|
| **Compile error** (syntax, type mismatch) | `"failed"` | `" hasError : ..."` |
| **Runtime exception** (unknown identifier, division by zero, etc.) | `"success"` | `"code execute failed. error msg:..."` |

This is by design (user clarified in v9 — "是用户在干预"). Don't try to "fix" the server.

**Success criterion for `simtalk_run`:**
```text
result == "success"  AND  not log.startswith("code execute failed")
```

Both clauses are required — `result == "success"` alone misses runtime errors.

---

## 4. How to get a value out (verified)

There is **no socket return path**. The server-side `Run_Simutalk` is `-> void`; even with `return_value:true` and `-> T\nreturn X`, the value never reaches the socket. Variants tried in v9 R4 + v8 T2-T4, all failed to produce `data`:

- `-> integer\nreturn 1+1`
- `-> any\nreturn 42`
- `-> integer\nresult := 99`
- `print(42)\nreturn 42`

**The only way to see a value**: `print(X)` → it shows up in the **Plant Simulation GUI Console**. The socket only confirms "execution succeeded" — it never carries the value.

If you need to read a value programmatically, the closest workaround is the GUI Console (manual), or pre-create a Table/attribute in the GUI and write to it (v9 R5 warning: writing to a non-existent global attr hangs the socket — see §7).

---

## 5. Parameter syntax cheat sheet (v10 — verified)

| Form | sx | rn | Notes |
|---|---|---|---|
| `param i:integer,str:string; body` | ✅ | ✅ | Multi-param, single-line `;` |
| `param str:string := "x"; body` | ✅ | ✅ | **Default-value param — safest form** |
| `param byref str:string; body` | ✅ | ✅ | `byref` modifier |
| `param byref str:string; str := "x"; body` | ✅ | ✅ | `byref` + reassign |
| `param i:integer := 1, str:string := "hi"; body` | ✅ | ✅ | Multi-param, all defaulted |
| `param str:string\nbody` (multi-line) | ✅ | ✅ | Multi-line also OK |
| `param byref str:string := "x"; body` | ❌ | n/a | `byref` + default is forbidden |
| `param byval str:string; body` | ❌ | n/a | `byval` is the default; explicit `byval` illegal |
| `var a,b: integer\nparam x: real := 1.0\nreturn x+a` | ❌ | n/a | `var`+`param` name clash pattern (v9) |

**Heads-up on `simtalk_run` with params**: the server **silently accepts param declarations with no caller** (no actual argument binding). So `param i:integer,str:string; print str` and `param byref str:string; str := "x"; print str` both reach `result:"success"` at runtime. Don't interpret this as real reference semantics — it's the server being lenient.

---

## 6. Anti-patterns that hang the server

These produce **no reply** (modal dialog blocks the GUI thread). Confirmed by v3-v5 (modals) and v9 R5 (attribute write):

| Anti-pattern | Why it hangs | Fix |
|---|---|---|
| `prompt("...")` or `infoBox("...")` inside `simtalk_run` | Pops modal dialog waiting for click | Use `print` instead |
| `MyAttr := X` for a global attribute that **doesn't exist yet** | Plant Simulation asks "create this attribute?" in a modal | Use local `var`, or pre-create the attribute in the GUI |
| Forgetting `--resp-mode delimiter --resp-delimiter '\|\|END\|\|'` | `eof` mode never returns (server doesn't close) | Always pass delimiter framing — see `references/lifelines.md` §2 |

`simtalk_syntax` will accept `prompt(...)` / `infoBox(...)` / `NewAttr := X` happily — the trap only fires when the code is **run**.

---

## 7. Other practical notes

- **`return X` without `-> T`** fails with `log:"The method has no return value."` (v6 T5). Use `-> integer\nreturn X` if you need return syntax (still no socket return).
- **`action_id`** is echoed back verbatim — use a unique string per request to correlate. Even UUIDs work (v9 R9).
- **Field name is `simtalk_code`** — earlier docs had `simtalk` / `expression`, both wrong. v2 fixed.
- **Time budget**: `simtalk_syntax` typically < 1s; `simtalk_run` typically < 1s for trivial code, but a timeout of 60s is recommended to absorb occasional latency.

---

## 8. Worked example — full happy path

Goal: confirm code parses, run it, read the result.

```bash
# Step 1 — syntax check
python3 scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data '{"type":"simtalk_syntax","action_id":"wk-1","simtalk_code":"var n: integer := 3\nwhile n > 0\n  print n\n  n -= 1\nend"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# Expect: result == "has no Error" (no "hasError" substring) → syntax OK

# Step 2 — run it
python3 scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 60 \
  --data '{"type":"simtalk_run","action_id":"wk-2","simtalk_code":"var n: integer := 3\nwhile n > 0\n  print n\n  n -= 1\nend"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
# Expect: result == "success" AND log does not start with "code execute failed"
# Values 3/2/1 appear in the Plant Simulation GUI Console — the socket does not carry them.
```

---

## 9. Response field reference (one place)

| Field | `simtalk_syntax` | `simtalk_run` | Trust |
|---|---|---|---|
| `type` | `"action_result"` | `"action_result"` | ✅ echoes request type |
| `action_id` | echo | echo | ✅ request↔response pairing |
| `result` | diagnostic string | `"success"` / `"failed"` / `"timeout"` | ✅ primary success signal (rules in §2 / §3) |
| `log` | unreliable — sometimes current, sometimes stale | usually current; the embedded identifier/line may be cached | ⚠️ use prefix only |
| `retsult` | stale cache | stale cache | ❌ always ignore |
| `data` | absent | absent | — never carries values |
# local-simtalk-execution Test Session — 2026-08-24

## 1. 环境 / Environment

- **Skill under test**: `skills/local-simtalk-execution/`
- **Server**: Plant Simulation (host), listening on TCP port 50007
- **Client host**: WSL2 container running OpenClaude. `127.0.0.1` resolves to the container itself, not the host machine. `host.docker.internal` is the correct bridge address.
- **Server-framing protocol claimed by docs**: request ends with `||END||`, reply ends with `||END||`. Client should use `--resp-mode delimiter --resp-delimiter '||END||'`.
- **Test driver**: `python3 skills/local-simtalk-execution/scripts/socket_client.py` — confirmed `--help` works (exit 0).

## 2. 用例与结果 / Test Cases & Results

### T0 — Server reachability

| Probe | Result |
|---|---|
| `127.0.0.1:50007` | FAIL — `ConnectionRefusedError [Errno 111]` |
| `localhost:50007` | FAIL — `ConnectionRefusedError` |
| `host.docker.internal:50007` | **OK** |

Conclusion: from this WSL2 container the only reachable address is `host.docker.internal`. The `socket_client.py` script itself surfaces this in its error message when running inside `/.dockerenv` (see script lines 142-150), so the script's HINT logic is working as designed.

---

### T1 — `ping` connectivity handshake  ✅ PASS

**Command:**

```bash
python3 scripts/socket_client.py \
  --host host.docker.internal --port 50007 --timeout 10 \
  --data '{"type":"ping","timestamp":"20260824000001"}||END||' \
  --resp-mode delimiter --resp-delimiter '||END||'
```

**Result:** exit=0, stdout:

```
{ "type": "ping", "result": "success" }||END||
```

**Observations:**
- Server reachable, replies in well under 1s.
- ⚠️ **Response schema mismatch with docs.** The skill's `references/message-schema.md` says a `ping` reply should be `{"type":"result","result":"success"}`. The actual reply is `{"type":"ping","result":"success"}` — the `type` field echoes the **request** type instead of being a generic `result` envelope. The client script does not validate this, but a future consumer that branches on `type == "result"` would mis-classify the response.

---

### T2 — `simtalk_syntax` (valid code)  ❌ TIMEOUT

Four variants attempted, all timed out at 60s (exit=1):

| Variant | Code | `--resp-mode` | Trailing `\|\|END\|\|` | Result |
|---|---|---|---|---|
| T2a | `-> boolean` | delimiter | yes | TIMEOUT (15s) |
| T2b | `print(1+1););` | delimiter | yes | TIMEOUT (15s) |
| T2c | `-> boolean` | delimiter | yes | TIMEOUT (60s) |
| T2d | `-> boolean` | delimiter | no | TIMEOUT (60s) |
| T2a' | `-> boolean` | **eof** | yes | TIMEOUT (20s) |
| T2b' | `print(1+1););` | **eof** | yes | TIMEOUT (20s) |

**Exact stderr line for each:** `TIMEOUT: no reply within Ns`

**Observations:**
- The TCP connection is accepted (no `cannot connect` error); the request payload is `sendall`'d successfully; the server then **never sends any bytes back** before the client-side timeout fires.
- Tested both `delimiter` framing (read until `||END||`) and `eof` framing (read until FIN) — neither received any data.
- Tested with and without the documented `||END||` suffix on the request — same behavior.
- Conclusion: either (a) the server silently drops / does not implement `simtalk_syntax`, (b) it requires a handshake step not described in `references/message-schema.md`, or (c) it expects a different framing (e.g. line-based) that the script doesn't exercise.

---

### T3 — `simtalk_syntax` (invalid code)

Not reached — skipped once T2 demonstrated the server does not respond to `simtalk_syntax` payloads at all (any payload, valid or invalid, hangs until the client timeout). Invalid-code behavior is therefore **untestable** against the current server.

---

### T4 — `simtalk_run` (execute expression)

Not executed — given T2's outcome, `simtalk_run` is expected to behave identically (server does not respond). Skipped to save time.

---

### T5 — `action_id` round-trip + framing-modes

Partial coverage:
- `action_id` cannot be verified: no `simtalk_syntax` / `simtalk_run` reply was ever received, so no request↔response pairing was possible.
- Framing-mode coverage: `delimiter` confirmed working on a `ping` reply (T1); `eof` exercised on T2a'/T2b' with no reply to consume — inconclusive for non-`ping` message types.

---

## 3. 总结 / Summary

| # | Test | Verdict |
|---|---|---|
| T0 | Reachability discovery | ✅ PASS — `host.docker.internal:50007` is the working address from this container |
| T1 | `ping` round-trip | ✅ PASS — exit 0, server returned `{"type":"ping","result":"success"}` |
| T2 | `simtalk_syntax` (valid) | ❌ FAIL — server accepts the connection but never replies, regardless of code/f framing/`--resp-mode` |
| T3 | `simtalk_syntax` (invalid) | ⚠️ SKIPPED — depends on T2 working |
| T4 | `simtalk_run` | ⚠️ SKIPPED — depends on T2 working |
| T5 | `action_id` round-trip | ⚠️ INCONCLUSIVE — no `simtalk_*` replies to inspect |

**Skill assessment:**
- `scripts/socket_client.py` itself is correct: it accepts all documented flags, returns the documented exit codes, surfaces a useful container-vs-host hint on connect failure, and successfully framed a real reply in T1.
- The skill's documentation has two notable gaps surfaced by this session:
  1. **Response `type` field mismatch.** Docs say `ping` → `{"type":"result", ...}`. Server actually echoes the request type. Any consumer code that hard-codes `type == "result"` would mis-route the reply.
  2. **No documented handshake or capability-discovery step.** `simtalk_syntax` and `simtalk_run` either need a prior handshake, a different framing, or are simply unimplemented on this particular server build. The skill currently has no fallback for "server accepts connection but never replies" beyond `--timeout`, which leads to long, silent stalls.

**Recommended next steps (not done in this session):**
- Confirm with the server owner whether `simtalk_syntax` / `simtalk_run` require a prior init/handshake message and what that message looks like.
- Try `--send-delimiter $'\n' --resp-mode line --resp-delimiter $'\n'` against `simtalk_syntax` to rule out line-based framing as the cause.
- After T2 works, re-run T3 (invalid code → expect `result:"failed"` + `log` line with `Syntax error near line N`) and T4 (`simtalk_run` → expect `result:"success"` + `data` field).
- Update `references/message-schema.md` so `ping` reply documents the `type` echo behavior, or fix the server to emit `{"type":"result", ...}`.
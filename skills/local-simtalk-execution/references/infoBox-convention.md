# infoBox skill convention (v18 → v19)

Every mutating operation in a server-touching skill opens a non-modal
`infoBox(text, false)` on the Plant Simulation GUI before doing the work,
and closes it (defensively twice) on exit.

| Stage | What the script does |
|---|---|
| Entry | `infoBox("[<script_name>] start: <summary>", false)` |
| Progress (optional) | `infoBox("[<script_name>] <progress message>", false)` |
| Exit | `infoBox("", false)` **twice** — defensive double-close |

The second argument `false` is the modal flag — non-modal so it never
freezes the GUI while requests are in flight. **Do NOT** swap to
`infoBox(text, true)` (modal) — that blocks the server waiting for a GUI
click (lifelines §4).

**Headless / CI:** pass `--no-infobox` (positional rule varies per skill —
see each skill's Usage section, or
`agents/optimizer-reports/cross-cutting-2026-08-27.md` Theme 2 for the
cross-skill positional rule summary).
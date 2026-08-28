# SimTalk comment syntax — authoritative locations

When unsure about SimTalk comment syntax (single-line `--` / `//`,
block `/* ... */`, inline `/* */`), these three locations in the
local Plant Simulation help docs are the source of truth:

## 1. `--` and `//` — single-line comments

`01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/language-fundamentals/values-variables-parameters/values-variables-parameters.md`

- `//` examples: lines 45, 59, 76, 87, 96, 97, 98, 201, 217, 227
- `--` examples: lines 96, 97, 98, 239, 240, 241, 242, 267-298

## 2. `/* ... */` — multi-line block comment

`01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/predefined-functions-ii-http-utilities/server-communication/server-communication.md`

- Multi-line `/* ... */` block comment: lines 497-502 (canonical
  example wrapping several lines of plain text)

## 3. `/* ... */` — inline block comment

`01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/predefined-functions-iii-type-query-inputoutput-conversion-debug/for-any/for-any.md`

- Inline `/* ... */`: line 41
  (`return when value then /*true*/4 else /*false*/5`)

## Summary

SimTalk 2.0+ accepts three comment forms:

| Form | Use | Example |
| --- | --- | --- |
| `-- ...` | Single-line comment (Plant Simulation convention) | `-- local counter` |
| `// ...` | Single-line comment (C-style, also valid) | `// local counter` |
| `/* ... */` | Multi-line block OR inline | `/* true */`, or wrapping many lines |

Use these as the source of truth when verifying what is and isn't a
valid comment in any Plant Simulation Method. For the `/* ... */`
block pattern in particular, see `quirks.md` Q11 for why decoration
lines (e.g. `=====`) MUST sit inside the block and not as bare lines
outside it.

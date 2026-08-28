# SimTalk reserved words — Method name blocklist

Plant Simulation's SimTalk lexer reserves a set of identifiers that **cannot be
used as a Method instance name**. Calling `duplicate()` (or any other creation
path) with one of these names fails with:

```
Invalid identifier or identifier already exists in the name scope
of the object or one of its instances.
```

`local-simtalk-create-method-object` rejects these names **before** the server
call so the user gets a clean error envelope instead of a runtime exception.

## How the blocklist is maintained

The list lives inline in `scripts/create_method_object.py` (`SIMTALK_RESERVED_WORDS`).
Comparison is **case-insensitive** — `Method`, `METHOD`, `method` all collide.

This file is the canonical human-readable reference; the script's set is the
authoritative runtime check.

## Categories

### 1. Built-in data types

These are parsed by the lexer as data-type keywords, so creating a class
instance named `method` (lowercase) is impossible. The same applies to
`variable`, `list`, `table`, etc.

| Identifier | Notes |
|---|---|
| `method` | Most common offender — see `local-simtalk-write-simtalk/log/session-20260826.md` |
| `variable` | InformationFlow class |
| `table` | InformationFlow class |
| `list` | InformationFlow class |
| `string`, `integer`, `boolean`, `real` | Scalar data types |
| `length`, `time`, `speed`, `acceleration`, `weight`, `currency` | Unit-bearing numeric types |
| `object`, `any`, `date`, `timewindow` | Generic / date / window |

### 2. Built-in module roots

These would create ambiguous dot-paths if used as instance names.

| Identifier | Notes |
|---|---|
| `informationflow` | Root for all InformationFlow classes |
| `materialflow` | Root for MaterialFlow classes |
| `workerpool`, `resources` | Root for Worker / Resource classes |
| `connectors`, `eventcontroller`, `infobox` | GUI-side roots |

### 3. Implicit variables

These are special variables SimTalk implicitly defines inside every Method.
Reusing them as instance names is ambiguous.

| Identifier | Notes |
|---|---|
| `result` | The implicit return value of every Method |
| `self` | The Method's own object reference |
| `current` | The currently-executing Method |
| `currentuser` | The active simulation user |

### 4. SimTalk control-flow keywords

These are syntactically never valid identifiers, but blocked defensively in
case Plant Simulation's lexer ever softens the rule.

`if`, `then`, `else`, `end`, `for`, `next`, `while`, `loop`, `return`, `do`,
`call`, `var`, `param`, `print`, `true`, `false`, `void`, `and`, `or`, `not`,
`mod`.

### 5. Class-operation keywords

`create`, `derive`, `duplicate`, `delete`, `move`, `rename`.

The `create` keyword is the one that traps users — Plant Simulation's
`duplicate()` is the only working Method-creation path. See `session-20260826.md`
for the three `create()` patterns that all fail.

## What to do if your Method needs a similar name

If your Method really wants to be called `method` (e.g. an educational
exercise that mirrors SimTalk source code), create it under a Folder that's
NOT the basis root and use the Folder's namespace to disambiguate. In
practice, just pick a different name — `myMethod`, `doMethod`, `MethodImpl`,
`M_calc` are all safe.

## Source / authority

- `local-simtalk-write-simtalk/log/session-20260826.md` — discovered the
  `method` (lowercase) collision empirically.
- `01-plantsimulation-knowledge/01-plant-simulation-help/programming-a-method/`
- `01-plantsimulation-knowledge/01-plant-simulation-help/objects/common-methods/common-methods.md`
  (Method / Variable / Table / List entries)
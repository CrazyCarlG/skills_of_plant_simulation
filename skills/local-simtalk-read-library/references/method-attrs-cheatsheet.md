# Method-object attribute cheatsheet

The `Method` object in Plant Simulation exposes the following attributes.
For the authoritative reference, see
`01-plantsimulation-knowledge/01-plant-simulation-help/objects/information-flow-objects/Method/attributes/`
and `.../Method/read-only-attributes/`.

| Attribute | Type | Read via | Notes |
|---|---|---|---|
| `Program` | string (rw) | `&m.Program` | The verbatim source code |
| `Encrypted` | boolean (ro) | `&m.Encrypted` | If true, source is opaque |
| `HasSyntaxError` | boolean (ro) | `&m.HasSyntaxError([byref ErrorMessage:string, byref Line:integer])` | Returns true if source has compile errors |
| `NumInExecution` | integer (ro) | `&m.NumInExecution` | Count of in-flight invocations |
| `RandomSeed` | integer (rw) | `&m.RandomSeed` | Per-Method RNG stream |
| `UsingNewSyntax` | boolean (rw) | `&m.UsingNewSyntax` | SimTalk 2.0 vs 1.0 mode |

## Read access idiom

```simtalk
var o: object := str_to_obj(p)
&o.Program        -- verbatim source
&o.Encrypted      -- bool
&o.HasSyntaxError -- bool
&o.NumInExecution -- int
```

The `var o: object := str_to_obj(p); &o.<attr>` form is **required** —
plain `<p>.Program` won't compile because bare `Method` (or any class
identifier) in SimTalk refers to the source-code content, not the
object itself. The `&` prefix is what retrieves the object reference.

## Encrypted source

When `Encrypted` is `true`, `Program` returns opaque bytes (the
encryption is server-side). There is no protocol-level way to recover
the source — you would need the encryption password + `decrypt`
permission, which the read-library skill does not attempt.

## Quirk: `Method` is a data type

`str_to_obj(p).Program` and `&str_to_obj(p).Program` are **the same**
because `str_to_obj` returns an `object` reference. But `Method.Program`
won't compile because `Method` is the SimTalk data type name, not an
object reference. Always go through `var o: object := str_to_obj(p); &o.Program`.

## What `local-simtalk-read-library` actually reads

The probe script reads `Program`, `Encrypted`, `HasSyntaxError`, and
`NumInExecution`. The remaining attributes (`RandomSeed`, `UsingNewSyntax`)
are read-write state that the skill currently does not capture — call
out for future expansion if needed.
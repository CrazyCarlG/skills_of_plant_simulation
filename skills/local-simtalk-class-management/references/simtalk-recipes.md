# SimTalk Recipes for Class Management

Each subcommand in `class_ops.py` ships a small SimTalk snippet that:

1. Resolves the target path with `str_to_obj(<path>)`.
2. Prints a `###CLASS_OP###` marker so the dispatcher can locate the
   result block in the cumulative `log` field.
3. Calls one Plant Simulation method (`derive`, `duplicate`, `setName`,
   `deleteObject`, `moveToFolder`, `createAttr`, `deleteAttr`,
   `setAttribute`, or `inheritAttribute`).
4. Prints the `KEY:VALUE` lines that build the `before` / `after`
   envelope.
5. Closes with `###CLASS_OP_END###`.

The dispatcher (`class_ops.py`) builds the snippet by Python-side
string substitution and sends it through `local-simtalk-execution`'s
`simtalk_send.py run` helper. The returned `log` field is parsed with
`###CLASS_OP###` … `###CLASS_OP_END###` as delimiters, with timestamp
prefixes (`YYYY-MM-DD HH:MM:SS:`) stripped on each line.

## Path escaping

Every path that lands inside a SimTalk double-quoted string literal is
escaped with this rule:

```python
def esc_str(s):
    return s.replace("\\", "\\\\").replace("\"", "\\\"")
```

This means a path like `.Foo.Bar\baz` becomes `.Foo.Bar\\baz` in the
SimTalk literal, and `My "Quoted" Class` becomes `My \"Quoted\" Class`.
The dispatcher's `esc_str` enforces this for every subcommand.

## Marker block grammar

Inside the marker block, every line is either:

- `KEY:VALUE` — recorded in the envelope's `data` dict.
- `ERR:<message>` — aborts the parse; the envelope becomes
  `ok:false, error:<message>`.

For `list`, the lines use a different shape (four colon-separated
fields: `CHILD:<i>:<name>:<type>:<path>`) and are not folded into
`data`; the script collects them into a `children` array directly.

## Subcommand → SimTalk mapping

### `list <folder>`

```simtalk
var folderObj: object
folderObj := str_to_obj("<folder>")
if folderObj = void
  print "###CLASS_OP###"
  print "ERR:folder_does_not_resolve:<folder>"
  return
end
var n: integer := folderObj.numNodes
print "###CLASS_OP###"
print "FOLDER:" + obj_to_str(folderObj)
print "COUNT:" + to_str(n)
var ch: object
var i: integer
for i := 1 to n
  ch := folderObj.node(i)
  print "CHILD:" + to_str(i) + ":" + ch.Name + ":" + ch.InternalClassType + ":" + obj_to_str(ch)
next
print "###CLASS_OP_END###"
```

### `inspect <path>`

```simtalk
var o: object
o := str_to_obj("<path>")
if o = void
  print "###CLASS_OP###"
  print "ERR:path_does_not_resolve:<path>"
  return
end
print "###CLASS_OP###"
print "PATH:" + obj_to_str(o)
print "NAME:" + o.Name
print "TYPE:" + o.InternalClassType
print "ORIGIN:" + obj_to_str(o.Origin)
print "ORIGINROOT:" + obj_to_str(o.OriginRoot)
print "CLASS:" + obj_to_str(o.Class)
print "NUMATTRIBUTES:" + to_str(o.numAttributes)
print "NUMMETHODS:" + to_str(o.numMethods)
print "NUMNODES:" + to_str(o.numNodes)
print "###CLASS_OP_END###"
```

### `derive <parent> [dest] [name]`

```simtalk
var parentObj: object
parentObj := str_to_obj("<parent>")
if parentObj = void
  print "###CLASS_OP###"
  print "ERR:parent_does_not_resolve:<parent>"
  return
end
print "###CLASS_OP###"
print "BEFORE_PATH:" + obj_to_str(parentObj)
print "BEFORE_NAME:" + parentObj.Name
print "BEFORE_TYPE:" + parentObj.InternalClassType
var newObj: object := parentObj.derive(<arg list>)
if newObj = void
  print "ERR:derive_returned_void:name_collision_or_folder_full"
  return
end
print "AFTER_PATH:" + obj_to_str(newObj)
print "AFTER_NAME:" + newObj.Name
print "AFTER_TYPE:" + newObj.InternalClassType
print "AFTER_ORIGIN:" + obj_to_str(newObj.Origin)
print "AFTER_ORIGINROOT:" + obj_to_str(newObj.OriginRoot)
print "AFTER_CLASS:" + obj_to_str(newObj.Class)
print "###CLASS_OP_END###"
```

`<arg list>` is built dynamically:

| Given | `<arg list>` literal |
|---|---|
| neither `dest` nor `name` | `parentObj.derive` (no parens) |
| only `dest` | `parentObj.derive(str_to_obj("<dest>"))` |
| only `name` | `parentObj.derive(void, "<name>")` |
| both | `parentObj.derive(str_to_obj("<dest>"), "<name>")` |

Plant Simulation accepts the no-arg form because all three parameters
are optional. We do **not** call `derive` on a Folder/Frame — the
dispatcher enforces `parent.InternalClassType` is a class (not a
folder) by checking for the `ERR:parent_does_not_resolve` line.

### `duplicate <source> [dest] [name]`

Same shape as `derive`, but the call site becomes
`srcObj.duplicate(<arg list>)`. Note `duplicate` does not accept a
`NextRandomSeedValue` parameter — only `derive` does.

### `rename <path> <new_name>`

```simtalk
var o: object
o := str_to_obj("<path>")
if o = void
  print "###CLASS_OP###"
  print "ERR:path_does_not_resolve:<path>"
  return
end
print "###CLASS_OP###"
print "BEFORE_PATH:" + obj_to_str(o)
print "BEFORE_NAME:" + o.Name
var ok: boolean := o.setName("<new_name>")
if not ok
  print "ERR:setName_returned_false:name_not_unique_or_reserved"
  return
end
print "AFTER_PATH:" + obj_to_str(o)
print "AFTER_NAME:" + o.Name
print "###CLASS_OP_END###"
```

### `delete <path>`

```simtalk
var o: object
o := str_to_obj("<path>")
if o = void
  print "###CLASS_OP###"
  print "ERR:path_does_not_resolve:<path>"
  return
end
print "###CLASS_OP###"
print "BEFORE_PATH:" + obj_to_str(o)
print "BEFORE_NAME:" + o.Name
print "BEFORE_TYPE:" + o.InternalClassType
var ok: boolean := o.deleteObject
if not ok
  print "ERR:deleteObject_returned_false:live_instances_may_exist"
  return
end
print "RESULT:deleted"
print "###CLASS_OP_END###"
```

### `move <path> <folder>`

```simtalk
var o: object
o := str_to_obj("<path>")
if o = void
  print "###CLASS_OP###"
  print "ERR:path_does_not_resolve:<path>"
  return
end
var folderObj: object
folderObj := str_to_obj("<folder>")
if folderObj = void
  print "###CLASS_OP###"
  print "ERR:dest_folder_does_not_resolve:<folder>"
  return
end
print "###CLASS_OP###"
print "BEFORE_PATH:" + obj_to_str(o)
print "BEFORE_NAME:" + o.Name
var res: object := o.moveToFolder(folderObj)
if res = void
  print "ERR:moveToFolder_returned_void"
  return
end
print "AFTER_PATH:" + obj_to_str(o)
print "AFTER_NAME:" + o.Name
print "###CLASS_OP_END###"
```

### `add-attr <path> <name> <type>`

```simtalk
var o: object
o := str_to_obj("<path>")
if o = void
  print "###CLASS_OP###"
  print "ERR:path_does_not_resolve:<path>"
  return
end
print "###CLASS_OP###"
print "BEFORE_PATH:" + obj_to_str(o)
var ok: boolean := o.createAttr("<name>", "<type>")
if not ok
  print "ERR:createAttr_returned_false:name_collision_or_invalid_type"
  return
end
print "AFTER_PATH:" + obj_to_str(o)
print "ATTR_NAME:<name>"
print "ATTR_TYPE:<type>"
print "###CLASS_OP_END###"
```

`<type>` must be a Plant Simulation type name. Known-good values:

| Type | SimTalk literal | Example |
|---|---|---|
| integer | `integer` | `o.createAttr("lotsize", "integer")` |
| real | `real` | `o.createAttr("weight", "real")` |
| boolean | `boolean` | `o.createAttr("isActive", "boolean")` |
| string | `string` | `o.createAttr("label", "string")` |
| length | `length` | `o.createAttr("trackLen", "length")` |
| time | `time` | `o.createAttr("cycleTime", "time")` |
| object | `object` | `o.createAttr("ref", "object")` |
| method | `method` | `o.createAttr("callback", "method")` |
| list | `list` | `o.createAttr("queue", "list")` |
| table | `table` | `o.createAttr("data", "table")` |

### `del-attr <path> <name>`

```simtalk
var o: object
o := str_to_obj("<path>")
if o = void
  print "###CLASS_OP###"
  print "ERR:path_does_not_resolve:<path>"
  return
end
print "###CLASS_OP###"
print "BEFORE_PATH:" + obj_to_str(o)
var ok: boolean := o.deleteAttr("<name>")
if not ok
  print "ERR:deleteAttr_returned_false:attr_inherited_or_not_found"
  return
end
print "ATTR_NAME:<name>"
print "RESULT:deleted"
print "###CLASS_OP_END###"
```

### `set-attr <path> <name> <value>`

```simtalk
var o: object
o := str_to_obj("<path>")
if o = void
  print "###CLASS_OP###"
  print "ERR:path_does_not_resolve:<path>"
  return
end
print "###CLASS_OP###"
print "BEFORE_PATH:" + obj_to_str(o)
var attrRef: any := o.<name>
if attrRef = void
  print "ERR:uda_not_found:<name>"
  return
end
attrRef.setAttribute("InitValue", <value_literal>)
print "AFTER_PATH:" + obj_to_str(o)
print "ATTR_NAME:<name>"
print "ATTR_VALUE_TYPE:<type_tag>"
print "ATTR_VALUE_RAW:<raw_value>"
print "###CLASS_OP_END###"
```

`<value_literal>` is built by `class_ops.py:_coerce_value_literal`:

| Input | `<value_literal>` emitted | `<type_tag>` |
|---|---|---|
| `true` | `true` | `boolean` |
| `false` | `false` | `boolean` |
| `42` / `+7` / `-3` | `42` / `+7` / `-3` | `integer` |
| `3.14` / `1e-3` | `3.14` / `1e-3` | `real` |
| `hello` | `"hello"` (escaped) | `string` |
| `[1,2,3]` | as string literal — **will fail at runtime** | `string` |
| `(table)` reference | as string — **will fail at runtime** | `string` |

For complex typed values (lists, tables, objects), the script cannot
emit a working SimTalk literal — fall back to `local-simtalk-execution`
with a hand-written snippet.

### `inherit-attr <path> <name>`

```simtalk
var o: object
o := str_to_obj("<path>")
if o = void
  print "###CLASS_OP###"
  print "ERR:path_does_not_resolve:<path>"
  return
end
print "###CLASS_OP###"
print "BEFORE_PATH:" + obj_to_str(o)
var attrRef: any := o.<name>
if attrRef = void
  print "ERR:uda_not_found:<name>"
  return
end
attrRef.inheritAttribute("InitValue")
print "AFTER_PATH:" + obj_to_str(o)
print "ATTR_NAME:<name>"
print "RESULT:inheritance_restored"
print "###CLASS_OP_END###"
```

`inheritAttribute` on a UDA takes the **sub-attribute name** (typically
`"InitValue"`). Restoring inheritance on `"InitValue"` means the UDA's
init value now follows the parent class again.

## Quirk reminders

- **`return` inside SimTalk returns from the method.** Our snippets are
  sent as method bodies via `simtalk_run`, so `return` exits the
  snippet. This is how we bail out on `void` lookups without raising
  an exception.
- **`obj_to_str(<obj>)` of `void` returns the string `"VOID"`.** Our
  `Origin`/`OriginRoot`/`Class` lines therefore print `"VOID"` for
  root classes — that is the expected sentinel value.
- **`print` always uses the GUI Console, never the network reply.**
  That's why we must wrap every output line in a `###CLASS_OP###`
  marker and recover via the `log` field (Quirk #6 — see
  `local-simtalk-execution/references/lifelines.md`).
- **No batching.** Each snippet does one mutating op so a partial
  failure leaves the model in a known state.
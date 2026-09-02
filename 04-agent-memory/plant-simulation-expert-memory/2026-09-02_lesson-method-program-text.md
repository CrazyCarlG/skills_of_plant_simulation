---
type: lesson-learned
date: 2026-09-02
session: 2026-09-02_session-summary_write-model-structure-comments.md
quorum: private
---

# Lesson: Method 程序文本必须用 `m.Program := ...`,不是 `.~` 也不是 `&m.Program`

## 唯一正确路径

```simtalk
var m: object;
m := str_to_obj(".Models.<Frame>.<MethodName>");
m.Program := "<chunk1>" + chr(10) + "<chunk2>" + chr(10) + ...;
```

## 反例(全部失败,实测验证)

| 写法 | 错误信息 | 原因 |
|---|---|---|
| `m.~ := string` | `Left and right sides of the assignment are incompatible` | `.~` 是 numeric(Method 的 contents-of-Method 视图) |
| `&m.Program := string` | `The ref-operator has no effect in this context` | `&` 在 `simtalk_run` formula eval 上下文禁用,只在 Method 体内有效 |
| `write_simtalk.py --code-file <full --comment>` | `add_note.py --mode replace failed (rc=2)` | Quirk #10:`--` 注释行让 argparse 截断 `--note` 值 |

## 官方依据

`01-plantsimulation-knowledge/01-plant-simulation-help/objects/information-flow-objects/Method/attributes/attributes.md` 的 `Program [SimTalk]` 段:
- Type: Attribute (string-typed)
- Syntax: `<&>Method.Program:string`
- 例:`&MyMethod.Program := "->real return 0.0"`(在 Method 体内)

桥接到 `simtalk_run` 时 `&` 被禁用,所以走 `m.Program :=` 直赋 + `chr(10)` 拼接。

## 配套纪律

- 2.7KB SimTalk ceiling:长 Method body(注释类尤其容易超)按 <1.5KB chunked 写
- 写后 readback:v15+ readlog 不捕获 print,只能用 `simtalk_syntax` + `target_path` 代理验证
- chunk 拼接方式:`"line1" + chr(10) + "line2" + chr(10) + ...`(不是 `chr(13) + chr(10)`;SimTalk `chr(10)` = LF)
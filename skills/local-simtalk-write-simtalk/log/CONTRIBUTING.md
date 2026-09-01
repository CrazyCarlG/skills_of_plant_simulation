---
last_updated: 2026-09-01
skill: local-simtalk-write-simtalk
audience: plant-simulation-expert (writer), skills-optimizer (consumer), verification (auditor)
---

# Contributing to `skills/local-simtalk-write-simtalk/log/`

每次调用产生一份新日志,**禁止 append 到已有日志**。

## 文件名 / Filename

```
<YYYY-MM-DD>-<agent>-<topic>.md
```

- `<agent>` 默认为 `plant-simulation-expert`(kebab-case)。
- `<topic>` kebab-case,≤ 5 个英文词,描述这次调用做了什么。
- 同一天多次调用:在 `.md` 前加 `-2`、`-3` 等。
- 历史文件(老的 `YYYY-MM-DD_<topic-slug>.md`)append-only,**禁止改名**。

## 必填 frontmatter

```markdown
---
date: YYYY-MM-DD
agent: plant-simulation-expert
skill: local-simtalk-write-simtalk
target: <method path,如 .Models.Model.count_parts>
mode: replace  (本 skill 固定 replace 模式,通过 add_note.py --mode replace --confirm 委托)
source_size_chars: N
verdict: PASS | PARTIAL | FAIL
---
```

## 必填段落(按顺序)

1. `## Goal` — 一句话:这次调用想实现什么功能、写入哪个 Method。
2. `## Steps` — 编号列出动作(`write_simtalk.py --path X
   --code-file Y`,委托 `add_note.py --mode replace --confirm`)。
3. `## Result` — `verdict` 行 + 写后 readback + `obj.execute`
   smoke 结果。
4. `## What this run validated / learned` — 对 SKILL.md / Quirk 表
   的影响 + 下次调用注意(如 `chr(10)` newline / `result` 保留字 /
   装饰行块注释)。

## Verdict 判定

- **PASS** — 代码写入成功,readback 字节一致,`obj.execute` 不抛异常。
- **PARTIAL** — 写入成功但 readback 有偏差(如 `--restore` 后续
  触发残留)。
- **FAIL** — 写入失败(WS-1 payload > 2KB / 含 `\n` 文字 /
  `HasSyntaxError` 已为 true / 加密 Method 未解密)。

## 不做的事

- ❌ Append 到已有 log。
- ❌ 修改已写 log。
- ❌ 跨 skill 写 log。
- ❌ 写入 `.SimtalkClaude.*` 下的方法。
- ❌ 用本 skill 创建 Method 实例(那是
  `local-simtalk-create-method-object` 的职责)。

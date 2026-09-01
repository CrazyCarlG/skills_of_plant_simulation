---
last_updated: 2026-09-01
skill: local-simtalk-execution
audience: plant-simulation-expert (writer), skills-optimizer (consumer), verification (auditor)
---

# Contributing to `skills/local-simtalk-execution/log/`

每次调用产生一份新日志,**禁止 append 到已有日志**(append-only 仅适用于历史文件)。

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
skill: local-simtalk-execution
target: <PS 对象路径,如 .Models.Model.Line.init>
mode: ping | simtalk_syntax | simtalk_run | readlog
verdict: PASS | PARTIAL | FAIL
---
```

## 必填段落(按顺序)

1. `## Goal` — 一句话:这次调用想达成什么。
2. `## Steps` — 编号列出实际动作(`socket_client.py ...` /
   `simtalk_send.py ...`)。
3. `## Result` — `verdict` 行 + 关键 stdout / stderr / 回包片段。
4. `## What this run validated / learned` — 对 SKILL.md / Quirk 表的
   影响 + 下次调用注意事项。

## Verdict 判定

- **PASS** — 命令成功,无 silent fail,结果可被下游使用。
- **PARTIAL** — 命令执行成功但有意外行为(readlog 返回延迟 /
  数据不完整 / 模态 box 残留)。
- **FAIL** — 命令失败(连接超时 / 协议错 / 服务端 error /
  JSON 解析失败)。**特别注意 Quirk #7**:`simtalk_run` 即使抛运行
  时异常也返回 `result:"success"`,**必须双重检查 `log` 是否以
  `code execute failed` 开头**。

## 不做的事

- ❌ Append 到已有 log 文件。
- ❌ 修改已写 log(append-only)。
- ❌ 合并多个 session 到同一文件。
- ❌ 写到非本 skill 的 log/ 目录。
- ❌ 新 log 用旧文件名格式。

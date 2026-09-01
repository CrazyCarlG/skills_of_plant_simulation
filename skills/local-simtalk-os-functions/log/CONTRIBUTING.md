---
last_updated: 2026-09-01
skill: local-simtalk-os-functions
audience: plant-simulation-expert (writer), skills-optimizer (consumer), verification (auditor)
---

# Contributing to `skills/local-simtalk-os-functions/log/`

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
skill: local-simtalk-os-functions
target: <OS 函数名,如 getFilesOfFolder / system / sleep>
function_signature: <完整签名,如 getFilesOfFolder(folder: string, pattern: string) -> list[string]>
verdict: PASS | PARTIAL | FAIL
---
```

## 必填段落(按顺序)

1. `## Goal` — 一句话:这次想验证/参考哪个 OS 函数。
2. `## Steps` — 编号列出调用步骤(`simtalk_run` 载荷 / `readlog`)。
3. `## Result` — `verdict` 行 + 真实返回值片段 + 与
   `references/functions.md` v14 实测表的对比。
4. `## What this run validated / learned` — 对
   `references/functions.md` / `v14-findings.md` 的影响 + Quirk
   #6/#7/#8/#11/#12 状态。

## Verdict 判定

- **PASS** — 函数成功执行,返回值与文档/实测一致,可复现。
- **PARTIAL** — 执行成功但有意外行为(如 `print <list>` 行为、
  SHGetKnownFolderPath CLSID 格式异常)。
- **FAIL** — 连接超时 / 模态阻塞 / Method-only 限制(如 `sleep`
  在 `simtalk_run` 里跑不通,需 `Method.execute`)。

## 不做的事

- ❌ Append 到已有 log。
- ❌ 修改已写 log。
- ❌ 跨 skill 写 log。
- ❌ 新 log 用旧文件名格式。
- ❌ 在 headless 环境触发 `infoBox` / `prompt` /
  `browseForFolder` 等模态函数。

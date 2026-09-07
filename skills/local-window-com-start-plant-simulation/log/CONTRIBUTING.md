# Contributing to `skills/local-window-com-start-plant-simulation/log/`

## 本技能的日志分工 / Where logs come from

本技能本身**不写 `log/`**。它是一次性启动脚本,无 session 语义。

每次运行的 PS console 输出经 `OpenConsoleLogFile` 写到 `--log-dir/run_<时间戳>.txt`
(由调用方指定,默认 `C:\logs`)。这层是 PS 引擎的 console log,**不属于**本技能的
session log。

调用方 agent 在执行完整工作流(本技能启动 + 下游 `local-simtalk-execution` 探针)
后,若需在 `log/` 留一份**会话级**记录(用于复盘 / 跨会话沉淀),按下方约定写。

## 文件名 / Filename

```
<YYYY-MM-DD>-<agent>-<topic>.md
```

- `<agent>` 默认为 `plant-simulation-expert`(kebab-case)。
- `<topic>` kebab-case,≤ 5 个英文词,描述这次会话做了什么。本技能示例:
  `agv-factory-50007-launch`、`smoke-env-validate`。
- 同一天多次调用:在 `.md` 前加 `-2`、`-3` 等。

## 必填 frontmatter

```markdown
---
date: YYYY-MM-DD
agent: plant-simulation-expert
skill: local-window-com-start-plant-simulation
target: <.spp 模型路径 + SimtalkClaude 路径(如使用)>
mode: start_ps
verdict: PASS | PARTIAL | FAIL
---
```

`mode: start_ps` 是本技能专属值(区别于 `local-simtalk-execution` 的
`ping` / `simtalk_syntax` / `simtalk_run` / `readlog`)。

## 必填段落(按顺序)

1. `## Goal` — 一句话:这次调用想达成什么(启动哪个模型 / 哪个端口)。
2. `## Steps` — 编号列出实际动作(本技能脚本调用 + 下游探针)。
3. `## Result` — `verdict` 行 + 本脚本退出码 + 下游探针回包 + 关键 stderr。
4. `## What this run validated / learned` — 对 `lifelines.md` / `cli-args.md`
   的影响 + 下次调用注意事项。

## Verdict 判定

- **PASS** — 本脚本退出 0 + 下游 ping 回 `success`,全程无 silent fail。
- **PARTIAL** — 本脚本退出 0 但下游 ping 失败 / 超时;或 `--wait-ready`
  超时但仍能跑通下游(说明端口被别的进程占了)。
- **FAIL** — 本脚本非 0 退出(COMError / 文件不存在 / 端口越界等),
  工作流根本没起来。

## 不做的事

- ❌ Append 到已有 log 文件。
- ❌ 写到 `--log-dir`(那是 PS console log 的位置,本技能脚本管,不是 agent 管)。
- ❌ 把本技能的 session log 与 `local-simtalk-execution` 的 session log 合并——
  分开写,各自的 `mode` 字段区分。
- ❌ 把 `references/lifelines.md` / `references/cli-args.md` 已固化的内容复制
  到 log 里(写引用,不重复)。

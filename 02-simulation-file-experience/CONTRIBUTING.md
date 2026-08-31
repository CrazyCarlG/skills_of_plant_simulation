# 贡献指南 / CONTRIBUTING — `02-simulation-file-experience`

> 本目录是**经验沉淀**，不是 Plant Simulation 知识库。
>
> 经验沉淀的强约束是**多人增量写入**：每位工程师在跑任务时踩到坑 / 验证模式，都能在不打扰别人、不重写主体、不制造 git 冲突的前提下，把自己的发现追加进去。本文件定义的就是这个流程。

---

## 1. 三区结构（每个 `.md` 文件）

每篇 experience 文件由 3 个**物理上分开的区**组成，方便多人 merge：

```
┌─────────────────────────────────────────┐
│ YAML Frontmatter（顶部，不可变元数据）    │  ← 偶尔改（last_updated / contributors）
├─────────────────────────────────────────┤
│ 主体（讲解 / 决策表 / 代码片段）          │  ← 极少改（事实修正需带 issue 引用）
├─────────────────────────────────────────┤
│ ## 经验 Log（append-only 时间线）         │  ← 主战场，新 entry 只追加在末尾
└─────────────────────────────────────────┘
```

**为什么这样切**：

- 主体改 = 多人同时改 → 必然冲突
- Log 区 append = 多人各追加自己的 entry → 大概率 zero-conflict
- frontmatter 改 = 2 行以内 → 冲突可解

### 1.1 Frontmatter schema

```yaml
---
last_updated: 2026-08-28
contributors: [@alice, @bob, @charlie]
scope: 一句话说明本文件覆盖什么（什么时候来读它）
---
```

- `last_updated`：YYYY-MM-DD，任何一次写操作都要 bump
- `contributors`：写过的用户名列表（首次写时 append 自己）
- `scope`：用于 README 索引的反向查询（"想读 X 我应该来这"）

### 1.2 经验 Log 区入口格式（强制）

每条 entry 必须按以下结构：

```markdown
### YYYY-MM-DD by @username

- **症状**：（一句话，发生了什么 / 报了什么错）
- **根因**：（一句话，可选；如果未知就写"未明，需要更多数据"）
- **Workaround / 结论**：（代码 / 命令 / 决策 / 配置）
- **tags**：`simtalk, modal-trap, v2-only, ...`
- **see also**：`path/to/related.md §X` 或 `lifelines.md §Quirk #N`

> 这条经验教会我：
> - （1-2 句反思 / 心智模型沉淀）
```

**为什么这套字段**：

- **症状 + 根因** 是检索关键词（grep 时匹配）
- **Workaround** 是未来你（或别人）踩到同一坑时能直接抄的解
- **tags** 提供非层级分类（一篇文档可以挂多个 tag）
- **see also** 让关联经验互相索引，不丢失上下文
- 末尾的"教会我"是强制反思——避免日志变成"流水账"

---

## 2. 合并工作流

### 2.1 单工程师：触发点命中后的 30 秒动作

按 [`README.md` §经验沉淀协议](./README.md#经验沉淀协议) 的触发点（session 末尾 / 里程碑 / 新坑 / 跨 session 重复）：

1. **grep 现有文件**——`grep -r "<keyword>" 02-simulation-file-experience/` 确认是新坑
2. **选文件**——按 `README.md` §路径分配 5 条规则（skill bug → skills/<name>/log/；领域知识 → 01-；桥 → 02-；跨 skill 工作流 → 03-；模型特定 → 04-）
3. **追加 entry**——在该文件**末尾的"## 经验 Log"区**追加一条；不要改主体
4. **frontmatter bump**——更新 `last_updated`，在 `contributors` 里加自己（首次）
5. **git commit**——commit message 建议 `<file>: +<tag1>, <tag2> by @user`（例：`derived-methods-quirks: +strLen, v15-only by @bob`）
6. **开 PR**——如果走 code review 流程

### 2.2 多工程师：并发沉淀

- 两位工程师几乎同时追加 entry 到同一文件 → 通常**零冲突**（各自的 entry 在文件最末尾，互不重叠）
- 如果冲突（都改了 frontmatter 或主体）：
  - `git rebase` 同步
  - 主体冲突 → 必有一方要带 issue 引用；切勿"取并集"蒙混过关
  - frontmatter 冲突 → 取 union，按时间戳排序 `last_updated`

### 2.3 Supersede 模式（如何"修正"老 entry）

**铁律：老 entry 一旦写出来，永不删除、永不修改正文。** 如果发现老 entry 错了：

```markdown
### 2026-08-15 by @alice

> [superseded 2026-08-28 by @bob — 见下方新 entry]

- **症状**：...
- **结论**：... （原文保留，不改）
```

然后在下面写新 entry 解释 supersede 原因。这样历史可追溯，未来考古时能看到"这条认知是怎么演进的"。

---

## 3. 纪律红线

### ✅ 允许

- 在文件**末尾的"## 经验 Log"区** append 新 entry
- 更新 frontmatter 的 `last_updated` / `contributors`
- 修正主体里的**拼写 / 链接 / 错别字**（带 commit message 说明）
- 主体里的**事实修正**——必须带 issue 链接 / 错误 entry 引用
- 给 entry 加 supersede 标记

### ❌ 不允许

- 删 / 改老 entry 正文
- 不带 issue 引用就改主体区
- 粘贴整段 session 流水（session summary 归 `03-agent-memory/`，不归本目录）
- 新建 "X 发现汇总.md" / "踩坑日记.md" / 任何游离在 5 个子目录之外的 `.md`
- 把同一条 entry 同时写到多个文件（用 `see also` 字段交叉引用）

---

## 4. 自检清单（沉淀前 30 秒）

- [ ] **新坑 vs 已有坑？** `grep -r "<keyword>" 02-simulation-file-experience/` —— 已存在就 update 现有 entry（加 supersede 标记），不新建。
- [ ] **文件选对了吗？** 走 `README.md` §路径分配 5 条规则。skill bug 不归本目录。
- [ ] **写对区了吗？** 只在末尾的"## 经验 Log"区 append；不动主体。
- [ ] **frontmatter bump 了吗？** `last_updated` 更新 + `contributors` 加自己。
- [ ] **entry 字段齐全吗？** 症状 / 根因 / Workaround / tags / see all + 末尾反思。
- [ ] **写完 grep 一下关键词**，确认未来能搜到。

---

## 5. 完整 entry 示例

### 2026-08-28 by @alice

- **症状**：`simtalk_run` 返回 `result:"success"` 但 `log` 以 `"code execute failed"` 开头，看起来像 server bug。
- **根因**：服务端 `simtalk_run` 设计上 `result` 字段 = "代码是否编译并进入执行"，`log` 字段携带错误信息。这是软失败契约，不是 bug。
- **Workaround / 结论**：判断成功 = `result == "success" AND log` 不以 `"code execute failed"` 开头。两个条件都满足才是真成功。
- **tags**：`simtalk, soft-failure, design-not-bug, all-skills`
- **see also**：`references/lifelines.md §Quirk #7`

> 这条经验教会我：
> - 不要把 `result: "success"` 当作"代码一定跑通了"——读 `log` 字段是硬纪律。
> - 团队记忆 `memory/team/simtalk-run-soft-failure-design.md` 是源头，所有 `simtalk_run` 调用前应先读。

---

## 6. playbook per-entry file 约定（2026-08-31 起强制）

`03-workflow-playbook/skill-call-playbook.md` 的 §经验 Log 从 2026-08-31 起**不再内嵌 entry 正文**——每条 entry 单独成 `.md` 文件。

**为什么**：playbook 的 entry 越来越长（最长达 23 行 + 1 个决策表），内嵌导致：
- 单条 entry 的 git diff 被其他 6 节主体变更噪声淹没
- tag-based 检索必须 grep 整个 363 行文件
- per-entry supersede 标记无法精准定位

### 6.1 强制规则

1. **新 entry 必须独立成文件**：`03-workflow-playbook/<YYYY-MM-DD> by @<author> — <entry-title>.md`
2. **必须在 `03-workflow-playbook/INDEX.md` §经验 Log per-entry files 表格加一行**（Date / Author / tags）
3. **必须在 `skill-call-playbook.md §经验 Log` 末尾追加 1 行 pointer**（标题保留供反向 grep，正文改为"→ 详见 [file]..."）
4. **frontmatter 三处同时 bump**：`last_updated: 2026-08-31` + `contributors: [..., @your-handle]`（三个文件：playbook.md / INDEX.md / CONTRIBUTING.md 的 §6 提及）

### 6.2 命名 / URL 编码规则（与 `03-workflow-playbook/INDEX.md §经验 Log per-entry files` 同步）

| 字符 | 文件名 | URL 编码 |
|---|---|---|
| `→` space | 空格 | `%20` |
| `@` | at-sign | `%40` |
| `—` (em-dash) | em-dash | `%E2%80%94` |
| 其他 CJK / Latin | 保持原样 | 保持原样 |

### 6.3 范围（只覆盖 playbook）

`01-domain-concepts/` / `02-bridge-tool/` / `04-model-case-studies/` / `05-session-archives/` 的 §经验 Log **目前不强制**走 per-entry file——保留内嵌正文形式。如后续也想迁移，命名约定可复用，详见 `agents/curator-reports/2026-08-31-log-per-entry-files.md §Future migrations`。

---

> **历史**：
> - 2026-08-28 创建本文件（@z004bjuu + @plant-simulation-expert）；与 README §经验沉淀协议、agents/plant-simulation-expert.md §知识沉淀 配套落地。
> - 2026-08-31 新增 §6 playbook per-entry file 约定（@plant-simulation-experience-curator）；与 03-workflow-playbook/INDEX.md §经验 Log per-entry files 同步落地。

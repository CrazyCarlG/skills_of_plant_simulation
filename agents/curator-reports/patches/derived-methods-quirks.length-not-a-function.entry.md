### 2026-09-01 by @plant-simulation-experience-curator — `length()` 不是 SimTalk 函数(必须 `x.length` 属性);但 `.length` 在 string 上也有版本敏感问题 → 字符串永远走 `strLen`

- **症状**:
  - `print length("hello")` → "Unknown identifier 'length'"(function call 形式不存在)
  - `print str_to_obj(".Foo").length` → 0 或 "A 'string' cannot accept the method 'Length'"(取决于 object 类型 + PS 版本)
  - `print "hello".length` → "A 'string' cannot accept the method 'Length'"(v2606.0002 已知)
- **根因**:
  1. **SimTalk 没有 `length()` 顶层函数**——`length` 在 SimTalk 词法里**只作为 attribute** 存在(`str.length` / `list.dim`),不能作为函数调用
  2. **`.length` attribute 在 string 上不是 universal**:在某些 PS build / 版本上 string 不暴露 `Length` attribute → 报类型错误
  3. **list 的长度**走 `l.dim`(不是 `.length`)——已在 `derived-methods-quirks.md §二` 沉淀过
  4. **DataTable** 的"长度"语义不明确——行数走 `tab.YDim`、列数走 `tab.XDim`,**不**是 `tab.length`
- **Workaround / 结论**:

  | 类型 | 拿长度 | 不要用 |
  |---|---|---|
  | string | `strLen(s)` | `s.length`(可能 ERR)/ `length(s)`(永远 ERR) |
  | list | `l.dim` | `l.length`(不存在)/ `length(l)`(永远 ERR) |
  | DataTable | `tab.YDim` (rows) / `tab.XDim` (cols) | `tab.length`(无意义) |
  | Object (Frame) | `obj.NumChildren` / `obj.NumAttr` | 任何 `.length`(语义不对) |

  **强约束**:**字符串永远走 `strLen(s)`**——不要相信 "string `.length` works" 的旧记忆,跨版本不稳定。

- **tags**:`length`, `strLen`, `simtalk-attribute-not-function`, `version-sensitive`, `string-vs-list-vs-table`
- **see also**:`derived-methods-quirks.md §二 变量/属性名易错`(已有 `strLen` / `l.dim` 提示,但本 entry 是 P0 强化版);`03-agent-memory/plant-simulation-expert-memory/2026-09-01_session-summary_agv-claude-v2-wrap.md` §Key findings 第 4-5 条;`skills/local-simtalk-execution/log/2026-09-01_agv-v2-write-and-cache.md` Finding #4

> 这条经验教会我:
> - **`.length` 作为 attribute 跨版本不稳定**——v18 文档可能写 `.length`,v2606.0002 报错。**字符串长度 = `strLen` 这条铁律不动摇**;list / DataTable 用专属 attribute(`.dim` / `.YDim` / `.XDim`)。
> - **`length()` 作为函数永远不存在**——任何"试试看" 都不会编译通过,直接信"无此函数"。
> - **多源校验的胜利**:本 entry 是从 `derived-methods-quirks.md §二` 已有 "s.length is wrong, use strLen" 表格 + 09-01 新发现 "length() also wrong" + "string.length version-sensitive" 三方合成的——单独看任一 source 都不够,合并后才暴露完整的语义陷阱。
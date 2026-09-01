---
last_updated: 2026-09-01
contributors: [@plant-simulation-expert]
scope: SimTalk 语言层的字面契约与易踩小坑速查
---

# 03-modeling-know-how/02-simtalk — SimTalk 语言

本目录整合 **SimTalk 语言本身**的字面契约(literal contract)与跨文档反复出现的易踩小坑。

## 文件索引

| 文件 | 内容主题 |
|---|---|
| [`language-quirks-reference.md`](./language-quirks-reference.md) | **SimTalk 字面契约速查**:10 大类易踩坑(字面契约、变量名、模态陷阱、私有 API、log 锁、命名约定、2.0 vs 1.0、DataTable API、JSON 字段、Method-typed UDA) |

## 何时必须读本目录

任何 SimTalk 代码涉及以下情况**必读**:

- 用 `strLen(s)` vs `s.length` / `s.numCharacters` 取字符串长度
- 用 `l.dim` vs `l.length` 取 list 长度
- DataTable 行/列数取 `YDim` / `XDim`,不是 `.length`
- 调用 observer 回调,签名必须 `(valueName: string, oldValue: any)`,错则**静默不触发**
- `writeValue(attr, val)` **不自动转类型**,restore 时必须用 `str_to_length` / `str_to_time` 等转换
- 用 `infoBox(text, false)` 第二参数是模态标志,漏掉 → 服务端**永久阻塞**
- 给非 Frame 对象加 method:走 `createAttr(name, "Method")` + `getAttribute(name) → any`,**不是** `&Method.duplicate(<station>, ...)`
- 变量命名:遵循 `m_` / `v_` / `b_` / `l_` / `tab_` 前缀约定(P4_CTU 模型沉淀)

## 10 大分类速查

1. **SimTalk 字面契约**(远程调用必中:`action_result["result"]` 取小写 `"success"`/`"failed"`、log 前缀、模态陷阱)
2. **变量/属性名易错**(strLen vs length、`chr(10)` vs `\n`、`Method` 大写等)
3. **模态陷阱**(永久阻塞服务端的 5 种禁忌写法)
4. **Plant Simulation 私有 API 易踩字段**(`_3D.*`、`stat*Portion` 流体特殊化、`addObserver` 签名、`DataTable` 行复制)
5. **log 文件读取独占锁陷阱**(先 copy → read → delete)
6. **变量命名约定**(P4_CTU 模型沉淀的 8 种前缀)
7. **SimTalk 2.0 vs 1.0 语法混用**(per-method 选择,不是项目级开关)
8. **DataTable 运行时操作**(`MaxYDim/MaxXDim` 替代 `setSize` + `make2DimArray` 签名)
9. **JSON 字段处理**(SimtalkClaude 桥内部:`jsondata.asString(false)` 紧凑、`j.contains` 判存在)
10. **Method-typed UDA**(非 Frame 对象加 method 的 canonical 模式)

## 重构元数据

- 重构日期:2026-09-01
- 重构来源:`02-simulation-file-experience/01-domain-concepts/derived-methods-quirks.md`(1 篇,内容极丰富)
- 重构策略:从单一长文档中提取 10 大分类,组织为 1 篇主题导向参考(原文档的 append-only 经验 Log 暂未迁移,后续 curator 评估)
</content>
</invoke>
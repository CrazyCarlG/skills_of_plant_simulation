---
type: lesson-learned
date: 2026-09-02
session: 2026-09-02_session-summary_write-model-structure-comments.md
quorum: private
---

# Lesson: v15+ readlog 退化下,所有探测必须用 `print "PROBE_<purpose>: " + ...` 前缀

## 背景

`lifelines.md §5` 已记录 v15+ Plant Simulation TCP bridge (app version 2606.0002) **不再捕获 `print(...)` 输出到 readlog**——但这只说"不捕获",没说"会被误读为 echo"。

## 误判案例(2026-09-02 端口 50008)

```simtalk
print str_to_obj(".Models.Test")
```

readlog 输出:
```
15:34:13: execute sim-code: 'print str_to_obj(".M......'    <- code echo
15:34:13: .Models.Test                                       <- 看起来像 echo,实际是 print 实际输出(因 to_str 返回路径)
```

**没有前缀时,无法一眼区分 echo 行与 print 行**——尤其 `to_str` 返回路径字符串时,它长得跟 echo 一样。我第一波探测因此误判 `.Models.Test` 是 VOID,绕到 AskUserQuestion 浪费 ~2 min。

## 正确模板

```simtalk
print "PROBE_<purpose>: " + <expr>
```

例:
- `print "PROBE_existence: " + to_str(str_to_obj(".Models.Test"))`
- `print "PROBE_class: " + typeof(str_to_obj(...))`
- `print "PROBE_count: " + str_to_obj(...).children.dim`
- `print "PROBE_program: " + str_to_obj(...).Program`

readlog 输出形如:
```
15:34:13: execute sim-code: 'print "PROBE_existence: " + to_...'   <- code echo(可忽略)
15:34:13: PROBE_existence: .Models.Test                              <- print 实际输出(可信)
```

## 应用场景

任何 simtalk_run 探测,只要 print 一个会返回字符串字面量 / 路径 / echo-like 输出的值,**第一行 print 必须带 PROBE 前缀**。不带的 print 不作为存在性 / 值的判定依据。

## 例外

- `print 1+1` / `print 2*3` 等纯数字输出(数字不可能与 echo 撞色)可省前缀
- `print "literal"` 字面量(必须带前缀,否则完全无法区分 echo)
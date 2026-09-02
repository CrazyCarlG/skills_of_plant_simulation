---
type: lesson-learned
date: 2026-09-02
session: 2026-09-02_session-summary_write-astar-graph-method.md
quorum: private
---

# Lesson: readlog v15+ 退化下,method write-readback 必须用"三重 proxy"——`simtalk_syntax --target-path` + `m.execute()`(无参) soft-fail + functional `m.execute(args)`

## 唯一正确路径 / 反例表
| 写法 | 错误信息 / 后果 |
|---|---|
| ✅ 三重 proxy 链路(详见配套纪律) | 23 chunk rc=0 + syntax check `has no Error` + execute(0 args) 报 `"0 passed, N expected"`(N = 真实 param count)+ functional execute(N args) `execute success` → 写入 100% 确认 |
| ❌ 只信 `simtalk_run result=success` | silent fail:m.Program 写入失败但 server 返 success,program 仍空,**没有任何信号**(lesson `2026-09-01` AGV_Claude recovery 7 method 全 `program_len:0` 即此陷阱) |
| ❌ 依赖 `readlog` 捕获 print | v15+ 已回归,readlog 不再 capture GUI Console 的 `print(...)`,stdout 里看不到任何 marker(lesson `2026-09-02_lesson-probe-prefix.md` 已记录) |
| ❌ 依赖 `--return-value` 拿 print / 拿 m.Program | Quirk #6 实测无效,`data` 字段永远不出现 |

## 官方依据 (引用 01-plantsimulation-knowledge/<path>.md 路径 + 段标题)
- 无单一文档;组合自:
  - `skills/local-simtalk-execution/SKILL.md` Troubleshooting 表(readlog v15+ 回归)
  - `skills/local-simtalk-execution/scripts/simtalk_send.py` line 166-169(`hasError` 判据)+ line 205-209(result == "success" 软失败双重判据)
  - 2026-09-01 AGV_Claude recovery session:silent fail 模式复现

## 配套纪律
**三重 proxy 链路**(顺序不换):

1. **语法 check proxy**(写入后必做):
   ```bash
   simtalk_send.py --port <port> syntax --target-path <METHOD_PATH> '<任意 short code>'
   ```
   期望:`result: "has no Error"`,log `execute success`。空 program 也通过,所以这步只证 method body 语法 OK,**不**证明内容。

2. **signature 探测**(写后必做):
   ```simtalk
   var m: object := str_to_obj("<METHOD_PATH>")
   m.execute()
   ```
   期望:soft-fail RC=11,log `"code execute failed. error msg:Wrong number of parameters in Method: 0 passed, N expected."`(N = 真实 param count)。**这步是写入成功的最强信号**:server 把 method 源码加载到 model 并按 signature invoke,报 param count 即源码真的被加载。如果 program 空,server 拿 0-arg method,invoke 应该 "no error",看不到 "N expected"。**N 与源码 `param` 行一致 = 100% 写入成功**。

3. **functional smoke test**(可选但推荐):
   ```simtalk
   var m: object := str_to_obj("<METHOD_PATH>")
   var r: <ret type> := m.execute(<所有 param>)
   ```
   期望:RC=0,result=success,log `execute success`。验证运行时无 crash(包括 subscript / type cast / runtime exception)。readlog v15+ 退化下,**`result=success AND log="execute success"` 是 functional pass 的唯一判据**(看不到 r 的具体值)。

## 反例触发场景(本 session)
- Step 12 全部 23 chunk rc=0 → 但仍不确定 server 是否真的把 source 写到了 method
- Step 13 `simtalk_syntax --target-path` → `has no Error`(但空 method 也通过,不足)
- Step 14 `m.execute()` 无参 → soft-fail `"0 passed, 7 expected"`(7-param signature 完整识别,**最强 readback 信号**)
- Step 15 functional `m.execute(ef, et, ec, hk, hv, "A", "C")` → execute success(no subscript error 即 r 至少 3 个节点,path 正确)

## 例外
- method 是 `->void` 无 return type → functional smoke test 仍可做,只是不能断言 return 值
- method 有 `param Start: string := ""` 默认值 → signature 探测可能不报 param count error(全 optional);退化为只信 syntax check + functional test
- method 写入后立即被用户 GUI 调用 → functional smoke test 跳过,只走 syntax + signature 探测(避免 side effect)
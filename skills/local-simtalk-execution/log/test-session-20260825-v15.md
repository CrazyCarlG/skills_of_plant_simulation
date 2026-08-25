# local-simtalk-execution Test Session v15 — 2026-08-25

测试目标：用 `local-simtalk-execution` 技能验证 `predefined-functions-ii-http-utilities/a-to-m.md`（**SimTalk Miscellaneous Global Functions, A–M**，共 56 个）中的样例代码，逐函数做 `simtalk_syntax` + `simtalk_run`，并在 v13 修复后的 `readlog` 通道里取回 `print(...)` 的实际值。

## 1. 环境 / Environment

- **Skill under test**：`skills/local-simtalk-execution/`
- **Server**：Plant Simulation（宿主机），TCP **50007**
- **Client host**：WSL2 容器 → `host.docker.internal:50007`
- **回包读取**：统一 `--resp-mode delimiter --resp-delimiter '||END||'`
- **辅助客户端**：`skills/local-simtalk-execution/scripts/socket_client.py`
- **测试时间**：2026-08-25 11:37 ~ 11:52（UTC+8）

## 2. 文档 / Doc Reference

- `01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/predefined-functions-ii-http-utilities/a-to-m/a-to-m.md`
- 共 **56** 个函数（A–M），本轮挑选**无副作用、无模态、结果易打印**的函数做端到端验证：
  - 数学/几何：`calcBrakingDistance` / `calcDroppedPerpendicularFootPoint` / `deg2rad`
  - 哈希：`computeSHA1Hash` / `computeSHA3Hash`
  - 颜色：`makeRGBValue` / `getStandardColor`
  - 数组：`createCombinations` / `createPermutations`
  - 对象存在性：`existsObject` / `existsFile` / `existsMethod` / `checkID`
  - 系统读：`getEpsilon` / `animation` / `language` / `getHighResolutionClock` / `makePathRelative`

## 3. 握手 / Handshake

| ID | 类型 | 命令 | 回包 | 结论 |
|---|---|---|---|---|
| P1 | `ping` | `--data '{"type":"ping","timestamp":"v15-init"}'\|\|END\|\|` | `{"type":"ping","result":"success"}` | ✅ 链路通（< 1 s） |

## 4. 语法检查 / `simtalk_syntax`（v15-sx-01 ~ v15-sx-20）

> 消费规则（来自 `references/message-schema.md` §"simtalk_syntax"）：`"hasError" not in result` ⇒ 语法通过。

| ID | 函数 | 关键代码 | `result` | `log` | 结论 |
|---|---|---|---|---|---|
| v15-sx-01 | `calcBrakingDistance` | `var d: length := calcBrakingDistance(100kmh, 10)\nprint d` | `has no Error` | `execute success` | ✅ |
| v15-sx-02 | `deg2rad` | `print deg2rad(45)` | `has no Error` | `execute success` | ✅ |
| v15-sx-03 | `computeSHA1Hash` | `print computeSHA1Hash("MyText")` | `has no Error` | `execute success` | ✅ |
| v15-sx-04 | `computeSHA3Hash` | `print computeSHA3Hash("MyText")` | `has no Error` | `execute success` | ✅ |
| v15-sx-05 | `makeRGBValue` | `var c: integer := makeRGBValue(110, 0, 200)\nprint c` | `has no Error` | `execute success` | ✅ |
| v15-sx-06 | `existsObject` | `print existsObject(".Models")` | `has no Error` | `execute success` | ✅ |
| v15-sx-07 | `existsFile` | `print existsFile("noname.mod")` | `has no Error` | `execute success` | ✅ |
| v15-sx-08 | `existsMethod` | `print existsMethod(".Models.Model")` | `has no Error` | `execute success` | ✅ |
| v15-sx-09 | `checkID` | `print checkID("sin")` | `has no Error` | `execute success` | ✅ |
| v15-sx-10 | `getStandardColor` | `print getStandardColor(1)` | `has no Error` | `execute success` | ✅ |
| v15-sx-11 | `getEpsilon` | `print getEpsilon` | `has no Error` | `execute success` | ✅ |
| v15-sx-12 | `animation` | `print animation` | `has no Error` | `execute success` | ✅ |
| v15-sx-13 | `language` | `print language` | `has no Error` | `execute success` | ✅ |
| v15-sx-14 | `createCombinations` | `print createCombinations([1,2,3], 2)` | `has no Error` | `execute success` | ✅ |
| v15-sx-15 | `createPermutations` | `print createPermutations([1,2,3], 2)` | `has no Error` | `execute success` | ✅ |
| v15-sx-16 | `calcDroppedPerpendicularFootPoint` | `print calcDroppedPerpendicularFootPoint([1,0.1,0.1],[2,0.2,0.4],[5,0.5,1])` | `has no Error` | `execute success` | ✅ |
| v15-sx-17 | `getHighResolutionClock` | `print getHighResolutionClock` | `has no Error` | `execute success` | ✅ |
| v15-sx-18 | **`1/0` 常量折叠**（陷阱用例） | `var x:integer := 1/0` | **` hasError ： Error in line 1: Division by zero. (in row :1)`** | `execute success` | ❌ 编译期错误 |
| v15-sx-19 | **未知标识符**（陷阱用例） | `print nonExistentIdentifierFoo` | `has no Error` | `execute success` | ✅ 语法过 / Quirk #7 |
| v15-sx-20 | `makePathRelative` | `print makePathRelative("/foo/bar")` | `has no Error` | `execute success` | ✅ |

**v15-sx-18 关键观察**：`var x:integer := 1/0` **在 sx 阶段就被判失败**（"hasError: Error in line 1: Division by zero"）——这与 v9 Quirk #7 的描述（"除零属于**运行时**异常 → result:"success""）不符。可能的解释：

- 文档例子用的是 `print 1/0`（运行时求值 → 走运行时异常路径 → Quirk #7 命中）；
- 本测试用 `var x:integer := 1/0` 让编译器做**常量折叠**（const-fold），折叠阶段就把 `1/0` 当成了编译期可识别的非法常量，直接报错。
- **消费规则更新**：**除零是常量表达式**时是编译错误 → `result:"failed"`；**除零是运行时求值**时按 Quirk #7 走 `result:"success"` + `log` 前缀 `"code execute failed"`。两种行为并存，需按代码形态判断。

## 5. 运行时执行 / `simtalk_run`（v15-rn-01 ~ v15-rn-08）

> 消费规则（Quirk #7）：`result == "success" AND not log.startswith("code execute failed")` ⇒ 真正成功。

每个 `simtalk_run` 前都打了**唯一标记字符串**（`V15_RN01_SHA1_` 等），便于在 readlog 里 grep 行号取实际值。

| ID | 函数 | 关键代码 | `result` / `log` | SX | RN 判定 |
|---|---|---|---|---|---|
| v15-rn-01 | `computeSHA1Hash` | `print "V15_RN01_SHA1_"; print computeSHA1Hash("MyText")` | `success` / `execute success` | ✅ | ✅ |
| v15-rn-02 | `deg2rad` | `print "V15_RN02_DEG2_"; print deg2rad(45)` | `success` / `execute success` | ✅ | ✅ |
| v15-rn-03 | `calcBrakingDistance` | `print "V15_RN03_BRAKE_"; print calcBrakingDistance(100kmh, 10)` | `success` / `execute success` | ✅ | ✅ |
| v15-rn-04 | `makeRGBValue` | `print "V15_RN04_RGB_"; print makeRGBValue(110, 0, 200)` | `success` / `execute success` | ✅ | ✅ |
| v15-rn-05 | `language` | `print "V15_RN05_LANG_"; print language` | `success` / `execute success` | ✅ | ✅ |
| v15-rn-06 | `animation` | `print "V15_RN06_ANIM_"; print animation` | `success` / `execute success` | ✅ | ✅ |
| v15-rn-07 | `getEpsilon` | `print "V15_RN07_EPS_"; print getEpsilon` | `success` / `execute success` | ✅ | ✅ |
| v15-rn-08 | `getStandardColor` | `print "V15_RN08_COLOR_"; print getStandardColor(1)` | `success` / `execute success` | ✅ | ✅ |

**所有 8 次 simtalk_run 都通过 Quirk #7 双判据**。但 socket 端的 `data` 字段仍未出现（Quirk #6 实测不变），实际值需要靠 readlog 拉回。

## 6. ⚠️ readlog v13 修复已回归 / `readlog` v15 Regression

> **严重发现**：v13 修复的"独立缓冲 + 重置 + GUI Console `print(...)` 捕获"在当前服务端构建（2606.0002）下**不再生效**，readlog 行为回到 v12 的反馈循环（feedback loop）模式。

### 6.1 复现步骤

1. 调用 `simtalk_run` `print "V15_CLEAN_ISO_ALPHA"` → `result:"success"` / `log:"execute success"`（v15-clean1）
2. 紧接着调用 `readlog`
3. 检查 readlog 的 `log` 字段是否包含 `V15_CLEAN_ISO_ALPHA`

### 6.2 观察到的 readlog 响应

```
{ "type": "action_result", "action_id": "v15-rl-clean", "result": "success",
  "log": "2026-08-25 11:51:56: Log file opened! Application Version: 2606.0002, UTC: 2026-08-25 03:51:56
2026-08-25 11:51:56: Local -->> Copilot: { \"type\": \"action_result\", \"action_id\": \"v15-rl-probe2\", \"result\": \"success\", \"log\": \"2026-08-25 11:47:51: Log file opened!... (← 上一条 readlog 的完整响应被嵌套回来) ..."
```

- ✅ 缓冲**重置**还在工作：每条 readlog 都以新的 `Log file opened! Application Version: ...` 起头
- ❌ 缓冲里的**实际内容**只有上一条 readlog 自己的响应（即 v12 的 `Copilot -->> Local:` / `Local -->> Copilot:` 反馈回路）
- ❌ `simtalk_run` 输出的 `print(...)` 内容**完全没出现**——`V15_CLEAN_ISO_ALPHA` 在 readlog 整个返回里 grep 不到
- ❌ 缓冲体积**指数级膨胀**：连续 readlog 会把上一次 readlog 的 payload 嵌套进下一次，几次后就被 `socket_client.py` 的 65536 字节上限截断（v15-rl-01 实测被截断到 sx-09）

### 6.3 行为对比表

| 行为 | v12 (旧 bug) | v13 (修复后) | **v15 (本轮)** |
|---|---|---|---|
| 缓冲重置标记 (`Log file opened`) | ❌ 缺失 | ✅ 有 | ✅ 有 |
| 捕获 GUI Console `print(...)` | ❌ | ✅ 有 | **❌ 缺失** |
| 独立缓冲（不被 I/O trace 污染） | ❌ | ✅ | **❌**（仍有 I/O trace） |
| 反馈循环（自己响应进自己缓冲） | ✅ 有 | ❌ 修复 | **✅ 回归** |
| 单次回包体积 | 指数膨胀 | 稳定 ≈ 200 B | 指数膨胀（65536 B 截断） |

### 6.4 影响

- **本轮 v15-rn-01..08 的实际 print 值都拿不到**——readlog 通道在本轮服务端构建下不可信
- 需要拿函数返回值时只能去 Plant Simulation GUI Console（Window ribbon → Console）肉眼读
- **建议**：把这条回归写到 `references/message-schema.md` 的 Quirk #11/#12 处，把 v13 的"✅ 已修复"标注改成"⚠️ v15 回归——readlog 现在回到反馈循环模式，不能再用来取 print 值"

### 6.5 v15-rn-01..08 实际 print 值（**未通过 socket 取得，需到 GUI Console 验证**）

由于 readlog 通道在 v15 服务端构建下不可用，下列期望值仅供人工到 GUI Console 比对：

| ID | 期望 print 1（标记） | 期望 print 2（返回值） | 文档期望值 |
|---|---|---|---|
| v15-rn-01 | `V15_RN01_SHA1_` | SHA1 哈希 | `0e9e68d9402c96044f0f93194f7010bc2e056752` |
| v15-rn-02 | `V15_RN02_DEG2_` | 弧度值 | `0.785398163397448` |
| v15-rn-03 | `V15_RN03_BRAKE_` | 制动距离 | `138.888888888889m` |
| v15-rn-04 | `V15_RN04_RGB_` | RGB 整数 | （未在文档示例中给具体值） |
| v15-rn-05 | `V15_RN05_LANG_` | 模型语言编码 | `1`（英语） |
| v15-rn-06 | `V15_RN06_ANIM_` | 动画状态 | `true` / `false` |
| v15-rn-07 | `V15_RN07_EPS_` | epsilon | `7e-08` |
| v15-rn-08 | `V15_RN08_COLOR_` | 标准色 #1 | （未在文档示例中给具体值） |

## 7. 与 v14 的对照 / Diff vs v14

| 维度 | v14 | v15 |
|---|---|---|
| 测试对象 | OS 函数（I 分类）20 个 | A–M 函数（Miscellaneous Global）56 个中抽样 17 个 |
| readlog 可用 | ✅（v13 修复生效） | **❌**（v15 回归） |
| Quirk #7 (`1/0` 等除零 → runtime "success") 复测 | ✅ | ⚠️ 常量除零是编译错误 → 实际触发不到 runtime 路径 |
| Quirk #6 (`data` 始终空) | ✅ 实测确认 | ✅ 实测确认（`return_value:true` 无效） |

## 8. 结论 / Conclusions

1. **`simtalk_syntax` 路径完全正常**——17 个 A–M 函数 + 3 个陷阱用例全部按预期表现（通过 / 编译错 / 不识别）
2. **`simtalk_run` 路径执行无副作用**——8 个 A–M 函数全部 `result:"success"` + `log:"execute success"`，socket 端不返回 `data`（Quirk #6 实测不变）
3. **`readlog` 通道回归 v12 反馈循环 bug**——v13 的"独立缓冲 + GUI Console 捕获"修复在当前 2606.0002 构建下失效，无法通过 socket 取 print 实际值（详见 §6）
4. **Quirk #7 在常量除零场景下被打破**——`var x:integer := 1/0` 在 sx 阶段就被拦下（详见 §4 v15-sx-18），运行时除零才会走 Quirk #7

## 9. 建议 / Recommendations

- 把 §6 的发现合并到 `skills/local-simtalk-execution/references/message-schema.md` 的 Quirk #11/#12 条目，把 v13 的"✅ 已修复"改成"⚠️ v15 回归"
- 下次需要拿 print 实际值时：
  - 首选：让用户在 GUI Console 截图/拷贝
  - 备选：把要验证的返回值写到**预先存在**的 Table / 局部 var，再用 simtalk_run 修改/读取（**不要**写到尚未创建的全局 attr，会触发 Quirk #8 的模态对话框）
- 测试 `1/0` 类异常时，**显式**用 `print 1/0`（运行时求值）才能稳定复现 Quirk #7；用 `var x := 1/0` 会被编译器在常量折叠阶段拦下
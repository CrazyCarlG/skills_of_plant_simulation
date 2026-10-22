---
name: local-simtalk-action-writecode
description: 通过 TCP 将 SimTalk 源码写入 Plant Simulation 中指定的 Method。用户要求修改、覆盖或写入方法代码时使用；本技能只写入，不负责执行代码。
---

# local-simtalk-action-writecode

## Quick Start

```bash
python skills/local-simtalk-action-writecode/scripts/simtalk_writecode.py --targetmethodpath "Models.Line1.Method" --code "print('hello')"
```

`--targetmethodpath` 和 `--code` 必填。多行代码可作为 `--code` 参数传入。连接参数可选：

```bash
python skills/local-simtalk-action-writecode/scripts/simtalk_writecode.py --targetmethodpath "Models.Line1.Method" --code "print('hello')" --host 127.0.0.1 --port 50007 --timeout 30
```

默认连接：`127.0.0.1:50007`，超时 `30` 秒。

## 写入流程与常见陷阱

1. **先核对目标路径和现有源码。** 用 `local-simtalk-read-program` 读取目标 Method，确认模型实例、对象名和 Method 名完全一致。不要仅凭 GUI 名称选择路径；同名对象可能位于不同 Frame。读取技能通常要求绝对路径带前导点。虽然上面的简例未带点，但实际服务端可能要求带点；以当前模型回包为准，遇到 `target path is invalid` 时先核对路径，不要重复发送同一路径。
2. **PowerShell 中注意内嵌引号。** 将含有 SimTalk 字符串的源码直接放进传给 Python 的原生命令参数时，双引号可能被 PowerShell 去掉。例如源码意图为 `moveTo("init")`，但 Method 里可能变成 `moveTo(init)`。多行源码也应验证换行和引号都未改变。不要只看命令行输入或写入成功回包；必须回读 Method，逐字核对源码。

	在 Windows PowerShell 中，可先将源码 UTF-8 编码为 Base64，再由 Python 解码并调用本脚本的写入函数，避免把 SimTalk 内容直接作为 Python 原生命令参数传递：

	```powershell
	$code = @'
	?._3D.Poses.moveTo("init")
	waituntil ?._3D.Poses.EndPoseWasReached
	'@
	$encoded = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($code))
	$py = "import argparse,base64,importlib.util; p='skills/local-simtalk-action-writecode/scripts/simtalk_writecode.py'; s=importlib.util.spec_from_file_location('writecode',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); a=argparse.Namespace(targetmethodpath='.Models.Model.KUKA.m_moveToDefaultPosition',code=base64.b64decode('$encoded').decode('utf-8'),host='127.0.0.1',port=50007,timeout=60.0); raise SystemExit(m.cmd_writecode(a))"
	python -c $py
	```

	将示例中的 `targetmethodpath` 换成已经核实的 Method 绝对路径。此方式复用本脚本的 JSON/TCP 写入实现；它只写源码，不执行 Method。
3. **超时后先读回，不要盲目重试。** 退出码 `1` 仅表示客户端未及时收到回包，不能据此判断服务端是否已写入。先调用 read-program 检查目标源码；只有确认内容仍旧或为空后，才决定是否再次写入。
4. **检查完整结果。** 写入回包 `status == "success"` 只证明服务端接受了写入请求。随后必须回读确认目标 Method 内容，并用 `local-simtalk-checksyntax` 在目标对象命名空间检查最终回读的代码。语法检查不等于执行；本技能本身不运行仿真。只有用户明确要求运行时行为验证时，才调用执行技能。

### 建议判据

- 写入：服务端返回 `status == "success"`。
- 内容：read-program 回读与计划写入的源码（包括引号、换行）一致。
- 语法：对最终源码的 syntax check 返回不含 `hasError` 的结果。
- 行为：除非另行按用户请求执行并观察，否则标记为未验证。

## 退出码

| 退出码 | 含义 |
|---|---|
| `0` | 写入成功（回包 `status == "success"`） |
| `1` | 等待回包超时 |
| `2` | 无法连接服务器 |
| `3` | 收发期间连接出错 |
| `10` | 服务器返回失败状态 |
| `20` | 回包不是有效 JSON |

## 相关技能

- `local-simtalk-checksyntax` — 检查 SimTalk 语法
- `local-simtalk-runsimtalk` — 执行 SimTalk
- `local-simtalk-read-program` — 读取 Method 源码
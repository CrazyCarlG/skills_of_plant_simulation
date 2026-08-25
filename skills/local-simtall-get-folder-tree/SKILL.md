---
name: local-simtall-get-folder
description: 获取当前加载到 Plant Simulation 中的模型（.current）的对象层级结构（Frame / Folder / Material Flow / Method / Variable 等节点）。当用户希望「列出当前模型有哪些 Frame / 文件夹 / 子 Frame / 子文件夹」、「知道某个对象位于哪条路径下」、「判断某个嵌套 Frame 是否存在」时使用。输出是结构化的 JSON 树，便于二次处理（diff、写文档、批量操作）。所有执行都通过 sibling skill `local-simtalk-execution` 的 `simtalk_run` 通道完成，因此本技能继承它的全部铁律（连接目标、回复分帧、`type` 白名单、模态陷阱、v15 readlog 不可信、Quirk #6/#7 双重判据）。
---

# local-simtall-get-folder

> 命名说明：本 skill 名保留用户原始拼写 `local-simtall-get-folder`（与其它 `local-simtalk-*` 兄弟 skill 拼写略有不一致）。请勿重命名目录。

通过 sibling skill `local-simtalk-execution` 的 TCP 通道，**把当前加载到 Plant Simulation 中的模型（`.current`）的对象层级结构抽出为 JSON 树**，不依赖 GUI Console 肉眼读取，也不依赖用户手敲 SimTalk。

> **铁律**：本技能**不重复**列出 `local-simtalk-execution` 已记录的所有硬规则——所有"必须 / 禁止 / 会挂死"的铁律一律在 `local-simtalk-execution/references/lifelines.md` 维护；本技能遇到规则只给一行引用。
>
> 任何新发现的硬规则只在 `local-simtalk-execution` 那边登记，本文档只引用。

## 1. 硬性约束 / Hard Constraints

> 这些是从 `local-simtalk-execution` 直接搬来的"对本技能有致命影响"的子集。

| 约束 | 影响 | 引用 |
|---|---|---|
| `simtalk_run` 的 `data` 字段永远为空 | 服务端 `Run_Simutalk` 是 `-> void`，`return X` / `return_value:true` 都拿不回值 | `local-simtalk-execution/references/lifelines.md` §6 / Quirk #6 |
| `simtalk_run` 成功必须双重检查 | `result == "success" AND not log.startswith("code execute failed")` | `local-simtalk-execution/references/lifelines.md` §6 / Quirk #7 |
| `readlog` 在 v15+ **不可信** | 抓不到 GUI Console 的 `print` 输出，buffer 会指数膨胀 | `local-simtalk-execution/references/lifelines.md` §5 |
| 模态陷阱 | `prompt` / `infoBox` / 写未声明的全局 attribute → GUI 卡死 → socket 永远没回包 | `local-simtalk-execution/references/lifelines.md` §4 |
| `type` 字段白名单 | 必须为 `ping` / `simtalk_syntax` / `simtalk_run` / `readlog` 之一 | `local-simtalk-execution/references/lifelines.md` §3 / Quirk #13 |
| WSL2 → 主机 | `--host host.docker.internal --port 50007` | `local-simtalk-execution/references/lifelines.md` §1 |
| 回复分帧 | `--resp-mode delimiter --resp-delimiter '\|\|END\|\|'` | `local-simtalk-execution/references/lifelines.md` §2 |

**直接结论**：本技能**不能**依赖 `simtalk_run` 把结构化数据塞回 socket——必须走"**服务端写到本地磁盘文件 → 客户端读这个文件**"的迂回路径。

## 2. 任务流程 / Workflow

### 2.1 整体思路

1. 在 Plant Simulation 进程中执行 SimTalk，把 `.current`（或某个指定 Frame）的对象层级展开成 JSON 字符串。
2. 通过 SimTalk 内置的 `<json>.writeFile(path)` 把 JSON 写到本地磁盘（Windows 路径或容器内挂载的共享路径均可，Plant Simulation 主机必须能写）。
3. 客户端 Python 脚本读这个 JSON 文件、解析、呈现/二次处理。
4. 因为 `simtalk_run` 不能直接递归进入子 Frame，**子层遍历采用"外层驱动"模式**：脚本维护 BFS 队列，对每个 Frame 子节点发新的 `simtalk_run` 请求，把 `context_path` 指向该 Frame，反复迭代直到队列清空。

### 2.2 子任务 / Sub-steps

```
1. ping                                → 确认链路
2. simtalk_run (context_path=.current) → 顶层展开：collect {name, type, path, numNodes}[]，写到 JSON 文件
3. 客户端读 JSON，挑选 InternalClassType ∈ {"Frame","Folder"} 的子节点入 BFS 队列
4. 对每个 BFS 节点再发 simtalk_run（context_path=该节点 path）→ 同样写到独立 JSON（或追加）
5. 重复 3-4 直到 BFS 队列空
6. 汇总所有 JSON，呈现为一棵树
```

> **为什么不递归进 SimTalk 一次性出整棵树？** —— `simtalk_run` 在公式 eval 上下文里跑，没有 `self` 也没有用户自定义 Method 对象可调用，没办法声明一个"递归方法"。多次 `simtalk_run` 是当前协议下唯一可行的程序化遍历方式。

## 3. 关键 API / Key SimTalk APIs

> 详细文档位于 `01-plantsimulation-knowledge/01-plant-simulation-help/`。本节只挑本技能实际调用的子集。

| API | 用途 | 来源 |
|---|---|---|
| `<Frame>.numNodes → integer` | 当前 Frame 内的对象数（含嵌套 Frame 但不含 Frame 内部对象） | `objects/material-flow-objects/Frame/read-only-attributes/read-only-attributes.md` §"NumNodes |
| `<Frame>.node(i:integer) → object` | 取第 i 个对象（按插入顺序） | `objects/material-flow-objects/Frame/methods/methods.md` §"node |
| `<Folder>.numNodes → integer` | Folder 也有 numNodes（书签 `bookmarks.csv:1094`） | `scripts/bookmarks.csv` 行 1094 |
| `<Folder>.node(...) → object` | Folder 也有 node()（书签 `bookmarks.csv:1093`） | `scripts/bookmarks.csv` 行 1093 |
| `<obj>.InternalClassType → string` | 任意对象的内部类型名（`"Frame"` / `"Folder"` / `"Method"` / `"Table"` / `"Source"` ...）；`InternalClassName` 已弃用 | `simtalk/deprecated-unsupported-names/outdated/outdated.md` 行 154 |
| `<obj>.Name → string` | 对象短名 | 通用对象属性 |
| `obj_to_str(obj[, MakeAbsolute:boolean:=true]) → string` | 返回对象的绝对路径字符串 | `simtalk/predefined-functions-iii-type-query-inputoutput-conversion-debug/type-conversion-functions/type-conversion-functions.md` §"obj_to_str |
| `<json>.writeFile(FileName:string) → void` | 把 JSON 变量序列化到本地磁盘文件 | `simtalk/data-types-expressions/primitive-structured/primitive-structured.md` §"writeFile — JSON |
| `saveFolderModel(FileName:string[, CompactFormat:boolean:=false, UseGit:boolean:=false]) → void` | 把当前模型保存为 `.psfm` 文件夹结构（"模型即目录"）；走这条路就**直接读 .psfm 目录** | `simtalk/predefined-functions-ii-http-utilities/n-to-z/n-to-z.md` §"saveFolderModel |

### 3.1 InternalClassType 的取值约定

`InternalClassType` 返回的是 Plant Simulation **内部类标识符**（不是显示名）。常见值（按已验证用法）：

| 类别 | InternalClassType 例 |
|---|---|
| 容器 | `"Frame"`、`"Folder"` |
| 信息流 | `"Table"`、`"List"`、`"Method"`、`"Variable"`、`"Comment"` |
| 物料流 | `"Source"`、`"Drain"`、`"Buffer"`、`"Conveyor"`、`"Track"`、`"Station"`、`"ParallelStation"`、`"PlaceBuffer"`、`"PickAndPlace Robot"`、`"TwoLaneTrack"` ... |
| 资源 | `"WorkerPool"`、`"Broker"`、`"Transporter"` ... |
| 接口 | `"EventController"`、`"Importer"`、`"Exporter"`、`"Interface"` |

> 内部标识符大小写敏感，且对未文档化的自定义 Class 可能返回类名而非内置类型——遇到未知值时**不要硬编码假设**，把它原样塞进 JSON 树里即可。

## 4. 方法 A — 推荐：服务端遍历 + JSON 落盘（程序化）

### 4.1 原理

每次 `simtalk_run` 只展开"当前 Frame 一层"，写到独立 JSON 文件。Python 端读 JSON、判定哪些是 Frame/Folder、推入 BFS 队列、再发新 `simtalk_run`。

### 4.2 单次 simtalk_run 的 SimTalk 载荷模板

载荷字段（参考 `local-simtalk-execution/references/message-schema.md` §"simtalk_run"）：

```json
{
  "type": "simtalk_run",
  "action_id": "<uuid>",
  "context_path": "<绝对路径：当前要展开的 Frame / Folder>",
  "simtalk_code": "<下面的 SimTalk 脚本>"
}
```

`simtalk_code`（注意所有换行必须是 `\n`，JSON 字面量转义）：

```simtalk
-- 一次性展开 <context_path> 指向的对象的"一层子节点"
-- 写入 <output_file>（Windows 路径，服务端主机可达）
param outPath: string := "C:\\temp\\ps_folder_snapshot.json"
param rootPath: string := ""        -- 可选：用于在 JSON 里标注相对路径
param rootType: string := ""        -- 可选：标注 root 节点类型
var root: object := current
var j: json
var arr: json
var child: object
var cj: json
var n: integer
var i: integer
j["path"] := obj_to_str(root)
j["name"] := root.Name
j["type"] := root.InternalClassType
j["numNodes"] := root.numNodes
arr := j.getOrCreateJSON("children")
n := root.numNodes
for i := 1 to n
  child := root.node(i)
  cj["name"] := child.Name
  cj["type"] := child.InternalClassType
  cj["path"] := obj_to_str(child)
  cj["hasChildren"] := false
  if child.InternalClassType = "Frame" or child.InternalClassType = "Folder"
    cj["hasChildren"] := true
  end
  arr[i] := cj
next
j.writeFile(outPath)
```

**为什么这版能跑**（逐行验证）：

- `var j: json` —— JSON 是 local 变量，**不会**弹模态（lifelines.md §4 陷阱不触发）。
- `obj_to_str(root)` —— 文档化的内置函数（type-conversion-functions.md）。
- `root.numNodes` / `root.node(i)` —— Frame / Folder 都支持（read-only-attributes.md + bookmarks.csv 行 1094/1093）。
- `child.InternalClassType` —— 通用对象的 read-only 属性。
- `j.getOrCreateJSON("children")` —— JSON 对象的内置方法（primitive-structured.md §"Methods and Attributes of JSON）。
- `arr[i] := cj` —— JSON 数组按下标赋值；JSON 在 SimTalk 里是值类型，按下标写入是合法操作。
- `j.writeFile(outPath)` —— 把 JSON 变量写到磁盘（primitive-structured.md §"writeFile — JSON"）。**服务端走的就是这个文件 I/O**，不弹模态。

### 4.3 客户端 Python 编排脚本

参考实现 `scripts/get_folder_structure.py`：

```python
#!/usr/bin/env python3
"""通过 sibling skill local-simtalk-execution 拉取 Plant Simulation
模型的对象层级结构，写到一棵 JSON 树里。"""

import argparse, json, os, sys, uuid, subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOCKET_CLIENT = REPO_ROOT / "skills" / "local-simtalk-execution" / "scripts" / "socket_client.py"

# SimTalk 载荷（注意 \\u 转义只在 Python 源码里需要，
# 真正发到 socket 的 JSON 里是单反斜杠）
SIMTALK_TEMPLATE = r"""param outPath: string := "__OUT__"
var root: object := current
var j: json
var arr: json
var child: object
var cj: json
var n: integer
var i: integer
j["path"] := obj_to_str(root)
j["name"] := root.Name
j["type"] := root.InternalClassType
j["numNodes"] := root.numNodes
arr := j.getOrCreateJSON("children")
n := root.numNodes
for i := 1 to n
  child := root.node(i)
  cj["name"] := child.Name
  cj["type"] := child.InternalClassType
  cj["path"] := obj_to_str(child)
  cj["hasChildren"] := false
  if child.InternalClassType = "Frame" or child.InternalClassType = "Folder"
    cj["hasChildren"] := true
  end
  arr[i] := cj
next
j.writeFile(outPath)
"""


def send_simtalk_run(host, port, timeout, simtalk_code, context_path=None):
    """调底层 socket_client.py 发 simtalk_run，按 lifelines §6 双重判据判定。"""
    payload = {
        "type": "simtalk_run",
        "action_id": uuid.uuid4().hex,
        "simtalk_code": simtalk_code,
    }
    if context_path:
        payload["context_path"] = context_path

    proc = subprocess.run(
        [
            sys.executable, str(SOCKET_CLIENT),
            "--host", host, "--port", str(port), "--timeout", str(timeout),
            "--data", json.dumps(payload) + "||END||",
            "--resp-mode", "delimiter", "--resp-delimiter", "||END||",
        ],
        capture_output=True, text=True, timeout=timeout + 5,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"socket_client exit={proc.returncode}: {proc.stdout.strip()}")

    reply = proc.stdout.rstrip("\n")
    if reply.endswith("||END||"):
        reply = reply[:-7]
    resp = json.loads(reply)
    if resp.get("result") != "success":
        raise RuntimeError(f"simtalk_run failed: {resp}")
    if resp.get("log", "").startswith("code execute failed"):
        raise RuntimeError(f"simtalk_run soft-fail (Quirk #7): {resp}")
    return resp


def expand(host, port, timeout, path, out_file):
    code = SIMTALK_TEMPLATE.replace("__OUT__", out_file.replace("\\", "\\\\"))
    return send_simtalk_run(host, port, timeout, code, context_path=path)


def walk(host, port, timeout, root_path, out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    queue = [root_path]
    visited = set()
    nodes = {}  # path -> json snapshot

    while queue:
        path = queue.pop(0)
        if path in visited:
            continue
        visited.add(path)

        safe = path.replace(".", "_").replace("/", "_").replace("\\", "_") + ".json"
        snapshot = out_dir / safe
        expand(host, port, timeout, path, str(snapshot))
        with snapshot.open("r", encoding="utf-8") as f:
            snap = json.load(f)
        nodes[path] = snap
        for child in snap.get("children", []):
            if child.get("hasChildren"):
                queue.append(child["path"])

    return assemble_tree(nodes, root_path)


def assemble_tree(snapshots, root_path):
    """把所有 snapshot 拼成单棵树。"""
    root = snapshots[root_path]
    children_by_path = {}

    def fill(node):
        for child in node.get("children", []):
            child_path = child["path"]
            if child_path in snapshots:
                child.update(snapshots[child_path].get("meta", {}))
                children_by_path[child_path] = child
                fill(child)

    fill(root)
    return root


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="host.docker.internal")
    ap.add_argument("--port", type=int, default=50007)
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--root", default=".current",
                    help="要展开的根路径，默认 .current")
    ap.add_argument("--out", default="./ps_folder_structure.json",
                    help="最终 JSON 树的输出文件")
    ap.add_argument("--tmp", default="./ps_snapshots",
                    help="中间单层 snapshot 落盘目录")
    args = ap.parse_args()

    tree = walk(args.host, args.port, args.timeout, args.root, args.tmp)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f"✅ wrote {args.out}")


if __name__ == "__main__":
    main()
```

### 4.4 已知限制 / Known Limitations

- **服务端必须能写 `outPath`**：Windows 路径直接给 `C:\\temp\\xxx.json`；容器化部署要给挂载出来的共享路径，否则 `j.writeFile` 会抛 IO 异常（→ 走 Quirk #7 软失败：`result:"success" + log:"code execute failed..."`，Python 脚本会报"soft-fail"）。
- **不能进 Class Library**（`.Models` 之外的 `.UserObjects`、`.InternalObjects` 等）：`context_path` 接受任意绝对路径，**但** Plant Simulation GUI 进程内的 SimTalk 引擎对 Class Library 的写操作有额外权限限制。**如确认需要，请先在 GUI 里对目标 Frame 触发一次手动 saveFolderModel 看是否能写**。
- **每次 `simtalk_run` 只展开一层**：若模型有 N 层嵌套，最坏情况发 N 次请求。**这是当前协议下唯一可行的程序化遍历**，可接受。
- **`numNodes` 的子 Frame 不展开**：文档明确说明 `numNodes` 把每个嵌套 Frame 计为 1，**不会**累加子 Frame 内的对象（Frame/methods.md §"NumNodes）。我们用 `InternalClassType == "Frame"` 判定"是否需要再发请求"，而不是依赖 `numNodes`。

## 5. 方法 B — 备选：saveFolderModel + 目录遍历（最简单）

### 5.1 原理

`saveFolderModel` 把整个当前模型保存为 `.psfm` 目录结构：每个 Frame / Folder 一个子目录或一个 `$.yaml` 文件。**目录结构本身就是模型文件夹结构的完美镜像**——只要 walk 这个目录就行。

### 5.2 单次 simtalk_run 模板

```json
{
  "type": "simtalk_run",
  "action_id": "<uuid>",
  "simtalk_code": "saveFolderModel(\"D:\\\\temp\\\\model_dump.psfm\", true, false)"
}
```

**注意**：
- 路径里的 `\` 在 JSON 字符串里要双重转义。
- 第二个参数 `CompactFormat:=true` 让每个有原点的对象单独存为 `.yaml`（更细的目录粒度，便于目录 walk）；`false` 是把所有对象塞进 `$.yaml`（文件数少，大模型性能好）。
- 第三个参数 `UseGit:=false` 不要自动建 Git 仓库（避免注册表依赖、避免弹 TortoiseGit 对话框——`UseGit=true` 在某些环境会触发模态）。

### 5.3 客户端 Python 编排脚本

参考实现 `scripts/get_folder_tree_via_save.py`：

```python
#!/usr/bin/env python3
"""调用 saveFolderModel 落盘 .psfm，然后 walk 目录得到结构。"""

import argparse, json, subprocess, sys, uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOCKET_CLIENT = REPO_ROOT / "skills" / "local-simtalk-execution" / "scripts" / "socket_client.py"


def call_save_folder_model(host, port, timeout, out_path):
    payload = {
        "type": "simtalk_run",
        "action_id": uuid.uuid4().hex,
        "simtalk_code": f'saveFolderModel("{out_path.replace(chr(92), chr(92)*2)}", true, false)',
    }
    proc = subprocess.run(
        [sys.executable, str(SOCKET_CLIENT),
         "--host", host, "--port", str(port), "--timeout", str(timeout),
         "--data", json.dumps(payload) + "||END||",
         "--resp-mode", "delimiter", "--resp-delimiter", "||END||"],
        capture_output=True, text=True, timeout=timeout + 5,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"socket_client exit={proc.returncode}")
    reply = proc.stdout.rstrip("\n")
    if reply.endswith("||END||"):
        reply = reply[:-7]
    resp = json.loads(reply)
    if resp.get("result") != "success":
        raise RuntimeError(f"saveFolderModel failed: {resp}")
    if resp.get("log", "").startswith("code execute failed"):
        raise RuntimeError(f"saveFolderModel soft-fail: {resp}")


def walk_psfm(root: Path):
    """Walk .psfm 目录，把目录结构映射为模型结构。"""
    tree = {"name": root.name, "type": "FolderModel", "path": str(root), "children": []}

    def visit(node: Path, parent: dict):
        for entry in sorted(node.iterdir()):
            child = {"name": entry.name, "path": str(entry)}
            if entry.is_dir():
                child["type"] = "Folder"
                child["children"] = []
                parent["children"].append(child)
                visit(entry, child)
            elif entry.suffix == ".yaml":
                child["type"] = "Yaml"
                parent["children"].append(child)
            elif entry.suffix == ".spp":
                child["type"] = "ModelEntry"
                parent["children"].append(child)
            elif entry.suffix == ".py":
                child["type"] = "PythonModule"
                parent["children"].append(child)

    visit(root, tree)
    return tree


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="host.docker.internal")
    ap.add_argument("--port", type=int, default=50007)
    ap.add_argument("--timeout", type=float, default=60.0)
    ap.add_argument("--psfm", default="D:\\temp\\model_dump.psfm",
                    help="服务端要写出的 .psfm 路径")
    ap.add_argument("--out", default="./ps_folder_tree.json")
    args = ap.parse_args()

    call_save_folder_model(args.host, args.port, args.timeout, args.psfm)
    tree = walk_psfm(Path(args.psfm))
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(tree, f, ensure_ascii=False, indent=2)
    print(f"✅ wrote {args.out}")


if __name__ == "__main__":
    main()
```

### 5.4 优缺点对比

| | 方法 A（simtalk_run + JSON） | 方法 B（saveFolderModel + walk） |
|---|---|---|
| 适用场景 | 程序化遍历、增量更新、自定义 JSON 结构 | 一次性 dump、要看 .yaml 细节、目录直观 |
| 模型规模影响 | N 层 → 至少 N 次 simtalk_run | 一次 saveFolderModel 即可 |
| 是否写盘 | 仅写中间 snapshot（JSON） | 写整个 .psfm（含 $.yaml） |
| 是否需要预存在对象 | ❌ 全部用 local var + JSON（不触发模态） | ❌ saveFolderModel 是已有 API |
| 风险点 | 服务端写 JSON 文件的权限；路径要存在 | 服务端写 .psfm 的权限；**当前已加载模型所在目录的写权限**（saveFolderModel 会重新落盘） |

## 6. 失败排查 / Troubleshooting

| 现象 | 可能原因 | 处理 |
|---|---|---|
| `socket_client.py` 退出码 1（超时） | 服务端挂死（多数是模态陷阱）；或 readlog v15 反馈循环 | 检查 simtalk_code 是否含 `prompt` / `infoBox` / 未声明的全局 attr；检查是否进 readlog 循环（lifelines.md §5） |
| `result:"success"` 但 `log` 前缀 `code execute failed...` | Quirk #7 软失败（运行时异常：除零、未声明符号、`j.writeFile` 写盘失败等） | 看 `log` 的 `error msg:` 后字段；最常见是 `outPath` 服务端不可写 → 改路径 |
| `result:"failed"` + `log` 含 `hasError` | 编译错（语法错、类型不匹配） | 按 `log` 里的行号改 simtalk_code |
| 写盘后客户端读不到文件 | 路径在服务端主机（Windows），不在 WSL2 容器 | 把 Windows 路径映射进容器；或用 `host.docker.internal` 共享出来的路径 |
| `cj` 变量未声明 / `cj["name"]` 编译失败 | SimTalk JSON 下标要求变量先存在 | 用 `var cj: json` 显式声明 local var；JSON 是引用类型可复用 |
| 返回 `numNodes=0` 但 GUI 里能看到子对象 | `context_path` 路径错了——`current` 不是你以为的那个 Frame | 把 `context_path` 换成 `.Models.MyModel` 之类绝对路径再试 |

## 7. 知识库路径 / Knowledge Paths

- **SimTalk 语法**：`01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/`
- **Frame API**：`01-plantsimulation-knowledge/01-plant-simulation-help/objects/material-flow-objects/Frame/`
- **JSON writeFile**：`01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/data-types-expressions/primitive-structured/primitive-structured.md` §"writeFile — JSON
- **saveFolderModel**：`01-plantsimulation-knowledge/01-plant-simulation-help/simtalk/predefined-functions-ii-http-utilities/n-to-z/n-to-z.md` §"saveFolderModel
- **InternalClassType**：同上 §"InternalClassName 行（弃用映射表）
- **sibling skill `local-simtalk-execution` 硬规则**：`skills/local-simtalk-execution/references/lifelines.md`（全部铁律的唯一事实来源）

## 8. 与 sibling skill 的关系 / Relationship with sibling skill

```
local-simtall-get-folder (本技能)        ─┐
   │                                       │ 复用
   ▼                                       │
local-simtalk-execution (TCP 客户端)    ───┘
   │
   ▼
Plant Simulation GUI 进程的 TCP 服务端
```

本技能**不直接调 socket**——只调 `local-simtalk-execution/scripts/socket_client.py` 的命令行接口。所有 `lifelines.md` 维护的铁律都通过 sibling skill 自动继承，本技能不重复登记。

## 9. 变更日志 / Changelog

| 日期 | 变更 |
|---|---|
| 2026-08-25 | v1 起草：方法 A（程序化 BFS）+ 方法 B（saveFolderModel + walk）双路径 |
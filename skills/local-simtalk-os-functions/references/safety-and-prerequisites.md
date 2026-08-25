# Safety & Prerequisites — 安全设置与前置条件

> 部分 OS 函数受 Plant Simulation 模型设置 `File > Model Settings > General > Prohibit Access to the Computer` 约束。启用该设置后，下列函数会被限制或禁止执行并报错。

## 受约束的函数 / Restricted Functions

| 函数 | 约束 | v14 实测 |
|---|---|---|
| `copyFile` | ⚠️ 受约束 | ✅ 跑通（用户已关掉限制） |
| `setCurrentDirectory` | ⚠️ 受约束 | ✅ 跑通 |
| `setEnv` | ⚠️ 受约束 | ✅ 跑通 |
| `startExtProc` | ⚠️ 受约束 | ✅ 跑通 |
| `system` | ⚠️ 受约束 | ✅ 跑通 |

**官方文档原文**：

> **安全提示**：部分函数（`copyFile`、`setCurrentDirectory`、`setEnv`、`startExtProc`、`system`）受安全设置 *File > Model Settings > General > Prohibit Access to the Computer* 约束。启用该设置后，这些函数会被限制或禁止执行并报错。

**额外细节**（文档备注）：
- `copyFile`：启用时不能从模型文件夹往外拷，安全模式下仅允许向模型文件夹写入
- `setEnv` / `setCurrentDirectory`：启用时被禁止并报错
- `startExtProc` / `system`：启用时不执行并报错

## 关闭限制 / Disable the Restriction

GUI 操作：
1. **File** → **Model Settings**
2. 切到 **General** 标签页
3. 取消勾选 **Prohibit Access to the Computer**
4. 保存模型

模型启动选项：`-cwd dir` 等启动选项与该限制无关。

## 网络 / Network Prerequisites

> 默认 WSL2 容器 ↔ 宿主机 Plant Simulation。

| 场景 | host | port |
|---|---|---|
| WSL2 容器 → Windows 宿主机 | `host.docker.internal` | `50007` |
| 同主机直接调用 | `127.0.0.1` | `50007` |
| 局域网其它机器 | 宿主机 LAN IP | `50007` |

⚠️ **WSL2 容器内 `127.0.0.1` 指向容器自身，连不上服务端**——必须用 `host.docker.internal`（v1 T0 验证）。

## Plant Simulation 进程 / Server Side

- Plant Simulation 进程必须正在运行
- TCP `50007` 端口已暴露（用户侧已配置好）
- 服务端必须升级到 **v13+**（readlog 修复版）才能验证 print 输出（Quirk #11 / #12）

## 服务端消息协议 / Message Protocol

| 消息 | 用途 | OS 函数相关 |
|---|---|---|
| `ping` | 连通性检查 | 任何测试前先 ping |
| `simtalk_syntax` | 仅编译检查（不执行） | 调试 print 语句语法 |
| `simtalk_run` | 执行 SimTalk 代码 | 主要消息：触发 print |
| `readlog` | 拉取 GUI Console 输出（v13+） | **取 print 实际值的唯一通道** |

详细字段定义见 `local-simtalk-execution/references/message-schema.md`。

## 加载顺序 / Loading Order

```text
1. local-simtalk-execution  (提供 socket_client.py + readlog)
       │
       └──> simtalk-os-functions  (本技能：OS 函数参考 + 实测 recipe)
```

**没有 `local-simtalk-execution`，本技能就只是文档**——所有实测步骤都要通过 `local-simtalk-execution` 把消息送出去。
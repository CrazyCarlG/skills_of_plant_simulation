# `.ModelAssistants` 架构总览

> Siemens Plant Simulation 原厂顶层 basis bundle。本文件解析其架构分层，所有论断均
> 基于 `/tmp/modelassistants_sources/` 下的 42 份已读源码（2026-08-27 抓取）。

## 1. 顶层结构

```
.ModelAssistants                                    [Folder]
├── Internal/                          ← 生命周期 + 内置工具
│   ├── autoexec                       [Method]  启动入口
│   ├── autoexecLoadObj                [Method]  对象加载 hook
│   ├── onCloseModel                   [Method]  关闭 hook
│   ├── ExportIconToFile               [Method]  图标导出
│   └── Socket                         [Object]  原厂内置 socket（用途不明）
├── BasicObjects/                      ← 类模板库（与 UserObjects/ 对偶）
│   ├── MaterialFlow/      {Connector, Frame, TestRibbonFrame}
│   ├── InformationFlow/
│   └── UserInterface/
├── Templates                          [Method]  空 method 充当 copy-paste 模板（9 字段 doc header）
└── <11 个 Frame>                      ← 工具应用
```

## 2. 11 个 Frame 的职责分层

| Frame | 角色 | 关键 method | 核心职责 |
|---|---|---|---|
| **AIBot** | AI 客户端 | `M_SetPyEnv`, `M_SendRequest`, `M_Response` | Python DLL 加载 + LLM 请求 + JSON 响应分发 |
| **ClassAssistant** | 类库管理 UI | `AddNewLibrary`, `AddNewModel`, `AutoSorter`, `searchFolder` | 自动建库 / 自动排序 / 自动搜索 |
| **Assistants** | UI 注入器 | `M_AddUserMenu`, `M_CreateIcon`, `M_CallInternalMethod` | 向所有 Frame 注入右键菜单 + 图标 |
| **AutoSave** | 后台守护 | `AutoSaveModel`, `MSaveModel`, `endSaveModel` | 周期自动保存模型 |
| **Namer** | 命名助手 | `AssignName`, `transformObjects`, `exchangeTabRow` | 批量改名 + Tab ↔ List 互转 |
| **FrameReplacer** | 节点替换 | `replaceObject`, `findCandidate`, `setReplacementMode` | 在 Frame 内按类型替换节点实例 |
| **QuickArrayTool** | 阵列生成 | `ArrayObjects`, `exchangeListRow` | 按 X/Y/Z 序列生成 3D 阵列 |
| **FrameEncrypt** | 加密工具 | `EncryptFrame`, `EncryptMethod`, `EncryptCandidate` | 给 Frame/Method 加密码保护 |
| **ClassAttrDepulicator** | 属性去重 | `M_copyAttributes`, `transformObjects`, `M_DuplicateObjectAttributes` | 跨对象复制属性 |
| **Calculator3D** | 3D 计算器 | `M_Convert`, `M_RefreshResults`, `M_AutomaticRotate`, `M_Undo` | 3D 坐标 / 角度转换（带撤销） |
| **ModelSyncCopy** | **模型复制器**（重磅） | 17 个 method（M_Split, M_Decode, M_Encode, M_ApplyFrame, …） | 整棵 Frame 子树序列化 + 跨模型粘贴；自带 TCP 服务端/客户端 |

## 3. Lifecycle Triple（❶❷❸）

`.ModelAssistants.Internal` 的 `autoexec` + `autoexecLoadObj` + `onCloseModel`
三件套是 Siemens Frame bundle 的**标准生命周期模式**——所有被自动加载的 Frame 工具
都遵循它。

```simtalk
-- autoexec (model 加载后触发)
rootFolder.AutoSave.Dialog.Open        -- 弹 AutoSave 设置对话框
var dt_sys: datetime := sysDate        -- 顺便取个时间戳

-- autoexecLoadObj (每次对象被加载时触发)
switch MessageBox("Do you want to add Model Assistant into all frames?", 48, 2)
case 16                                -- Yes
    rootfolder.Assistants.M_AddAllUserMenu()
else                                   -- No / Cancel
    return
end

-- onCloseModel (model 关闭时触发，param onExitApplication: boolean)
rootFolder.AutoSave.Dialog.setCheckBox("OffAutoSave", True)
rootFolder.AutoSave.Dialog.callback("Apply")  -- 主动停 AutoSave
```

**关键细节**：
- `autoexec` 末尾的 `return` 是隐式的（method 跑完即结束），但 `autoexecLoadObj` 的
  `return` 必须显式——否则即便用户点 No 也会继续执行后面的逻辑。
- `onCloseModel` 用 `Dialog.callback("Apply")` 触发对话框 Apply 按钮，而非直接写
  Variable——**这是为了走对话框内部的副作用链**（写文件、广播事件等）。
- `autoexec` 顶部留了一段被 `/* … end */` 注释掉的旧代码，是历史版本演进的可读性痕迹。

**agent 启示**：如果你要在 SimTalk 中实现「Frame bundle 自动接入」，就照抄这三个 hook
的位置和命名规范——Plant Simulation 的 object loader 会按 `<frame>.<method>` 路径自动
调用它们。

## 4. 工具-数据二分

每个 Frame 都遵循**工具 vs 数据**的清晰分离：

```
.Frame
├── Dialog / DialogNavigator       [Object]  UI 数据
├── Tab* / DataTable*               [Table]   业务数据
├── Variable* (config flags)        [Variable] 配置数据
├── Method M_* (执行逻辑)           [Method]  ← 工具
└── sub-Frame 内的 Frame            [Frame]   嵌套
```

例 `AIBot`：
- 数据：`Dialog`, `DialogNavigator`, `InputText`, `Output`, `JsOutput`, `PythonDLLPath`
- 工具：`M_SetPyEnv`, `M_SendRequest`, `M_Response`
- 桥：`Py_SendRequest`（PythonModule 嵌入）

**启示**：method 应该是纯函数（输入参数 + current + 数据 Variable），不应在 method 内
随手创建对象——对象应该挂在 Frame 上当作持久数据。

## 5. 三种 Frame 接口模式

### 5.1 纯 UI 注入（`Assistants`）
- **输入**：调用方传一个 `o_frame`（要注入的 Frame）
- **行为**：在 `o_frame` 上加 `UserMenu` / `UserMenuTitle` / `ShowUserMenu` 属性 / 图标
- **特点**：完全无状态，跨模型可移植

### 5.2 后台守护（`AutoSave`）
- **输入**：在 `autoexec` 里启动 `while ... loop`
- **行为**：`sleep(SavePeriod, False)` 间隔触发 `MSaveModel`
- **特点**：用 `IsExecuting` flag 防重入

### 5.3 TCP 长连接（`ModelSyncCopy`）
- **输入**：用户的 `M_StartServer` / `M_StartClient`
- **行为**：内置 `Socket` 对象 + `M_Send` / `M_OnReceive` / `M_ApplyFrame`
- **特点**：完整的 client-server 协议实现（MSCF v2，详见 [mscf-v2-protocol.md](mscf-v2-protocol.md)）

## 6. 与「主模型」的边界

`.ModelAssistants` 与用户模型对象**完全隔离**——它不向 `UserObjects/` 写任何东西，
也不读取业务对象。**所有路径都以 `.ModelAssistants.X` 为根**，即便 `M_AddAllUserMenu`
也是向「rootfolder 下的所有 Frame」注入菜单，不是「用户的业务对象」。

这是**正确的边界设定**——一个工具箱不应该污染业务模型。

## 7. 数据流：MSCF v2 协议（简图）

```
[Source Model]
    │ M_Copy (collect)
    ▼
[MSCF v2 payload string]
    │ over TCP / clipboard
    ▼
[Dest Model]
    │ M_Paste / M_OnReceive
    ▼ M_Split → recs[]
    │ pass 1: Frame / pass 2: Object / pass 3: Attr / pass 4: Ref / pass 5: Connector
    ▼ M_ApplyFrame
[Rebuilt subtree under destParent]
```

详见 [mscf-v2-protocol.md](mscf-v2-protocol.md)。
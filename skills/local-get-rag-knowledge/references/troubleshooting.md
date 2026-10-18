# Troubleshooting

按"症状 → 排查 → 处置"组织。每条都对应一个具体的失败模式，不是 generic advice。

## A. 服务连不上

**症状**

```
[error] Cannot reach CoPilot at http://localhost:8002: <urlopen error [Errno 10061] ...>
```

**原因**：服务没启动，或端口被占用。

**处置**

1. 看服务是否在跑：
   ```bash
   powershell -NoProfile -Command "Get-Process pythonw -ErrorAction SilentlyContinue"
   ```
   没输出 → 没启动。
2. 启动它：
   ```bash
   # 双击最快
   C:\Users\z004bjuu\Documents\skills_of_plant_simulation\Copilot-using\start_copilot.bat
   ```
3. 看端口是否被别的进程占：
   ```bash
   netstat -ano | findstr :8002
   ```
   找到 PID，去任务管理器结束它，或换一个端口同时改 `ask_copilot.py` 里的 `BASE` 字段。

## B. `agent_ready: false`

**症状**

```json
{
  "status": "ok",
  "agent_ready": false,
  "reason": "LLM credentials not configured"
}
```

**原因**：CoPilot 启动时找不到 LLM API key。

**处置**

1. 去 CoPilot 服务目录查 `.env` / 配置文件：
   ```
   C:\ProgramFiles\Siemens\TecnomatixPlantSimulation2606\Copilot\
   ```
2. 配置 LLM 凭据（具体字段名以目录里的 README / 配置模板为准）。
3. 重启服务：`stop_copilot.bat` → `start_copilot.bat`。

## C. 答案泛泛而谈 / 完全没引文

**症状**

- `answer` 是一段很泛的描述，看不到具体的类名 / 方法签名
- `citations: []`

**原因**：

- 问题问得太抽象（"Plant Simulation 怎么用"）
- CoPilot 内部文档索引没命中，转用 LLM 先验回答
- 关键名词用了非标准写法

**处置**

1. 把问题改具体——加对象名 / 方法名 / 类名：
   - 差："buffer 怎么用"
   - 好："`Buffer.create` 方法的完整签名是什么？它接受哪些参数？"
2. 中英对照试一次——CoPilot 内部以英文文档为主：
   - "What is the difference between Buffer and PlaceBuffer?"
3. 看 `metrics.tool_calls_count`——如果为 0，CoPilot 没做文档检索，纯靠 LLM 答。

## D. 长时间无响应（> 2 min）

**症状**

脚本挂住，既不出 token 也不退出。

**原因**：

- LLM 推理慢（首次冷启动 30–60s 正常）
- 文档检索阻塞（网络问题）
- 服务端 hang

**处置**

1. 直接看服务日志：
   ```
   C:\ProgramFiles\Siemens\TecnomatixPlantSimulation2606\Copilot\logs\copilot.log
   ```
2. 看到具体错误按错误信息走。
3. 没明显错误 → 重启服务再试。
4. 持续这样 → 换问题问法（短一点、英文），或检查网络。

## E. `citations` 链接打不开

**症状**

`tDocLink` 是 `https://...`，浏览器打不开或 404。

**原因**：

- Plant Simulation 官方文档链接偶尔会变更
- CoPilot 内部索引用的是旧版本

**处置**

- 用 `title` 字段到 Plant Simulation Help 里手动搜
- 接受链接可能过时——引文至少给了"出处"信息

## F. `--json` 输出乱码

**症状**

中文字段变成 `??` 或乱码。

**原因**：Windows 默认 stdout 编码是 cp936，不是 utf-8。

**处置**

```bash
# 方案 1：环境变量
set PYTHONIOENCODING=utf-8
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py --json "..."

# 方案 2：Python -X utf8
python -X utf8 skills/local-get-rag-knowledge/scripts/rag_ask.py --json "..."

# 方案 3：管道到文件再用编辑器打开
python3 skills/local-get-rag-knowledge/scripts/rag_ask.py --json "..." > out.json
```

## G. "Connection broken: IncompleteRead" / 套接字提前断开

**症状**

`urllib.error.ProtocolError` 或 `http.client.IncompleteRead`。

**原因**：服务在 stream 中途崩了（多半是 LLM 端报错后没正确关闭 SSE 连接）。

**处置**

1. 看 `logs\copilot.log` 末尾几行
2. 如果是 LLM 端 timeout / rate limit → 换时间重试，或降低问题复杂度
3. 如果稳定复现 → 可能是 LLM 凭据欠费 / 配置错，去服务目录查

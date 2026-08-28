/* ============================================================
   Method path : .P4_CTU.AdvancedObject.Software.RCS.m_TaskExcuter
   类型        : Method (Class=.P4_CTU.BasicObjects.InformationFlow.Method,Origin 同上 — 无派生实例)
   作用        : 订单池顶层调度循环(Polling Excuter),把 tab_taskPool 中
                 State="not start" 的订单按 TaskType 分派给 AGV / CTU 两个
                 下层执行器(m_AGVExcuter / m_CTUExcuter)
   ============================================================ */

-- 直接调用方 (实际触发链):
--   m_appendStockInTask  ──┐
--                          ├──> m_TaskExcuter_triggerpoint (互斥门)
--   m_appendStockOutTask ──┘            │
--                                       └──> &m_TaskExcuter.executeNewCallChain
-- * 任意 append 路径都先经 triggerpoint,后者用 TaskExcuter_Running 布尔做互斥
-- * executeNewCallChain 启动 worker,本方法本身就是 worker 主循环

-- 关键约定 / 副作用:
-- * tab_taskPool.ydim = 0 时退出 while,把 TaskExcuter_Running 置回 false
-- * 每轮 wait 60 = 1 分钟,所以即使 append 后无人再触发,1 分钟内也会再轮询
-- * In 路径先 AGV 后 CTU,Out 路径先 CTU 后 AGV(顺序固定,反映"谁先到谁接单")
-- * AGV 表按 Priority 降序 + TaskTime 升序重排,确保高优先级 / 早到达优先派
-- * 任一 m_Create* 失败 → continue,行 State 保持 "not start",等下一轮重试
-- * "Move" 分支和 default 都是 debug 占位(后续会扩展为跨库位搬运)

-- 下游消费者:
-- * m_CreateTransTask_AGV_In / _Out           → 写 tab_TransportationTask_AGV
-- * m_CreateTransportationTask_CTU_In / _Out  → 写 tab_TransportationTask_CTU
-- * m_getFreeBin                              → 读 Tab_binState,写 tab_taskPool["BinID",i]
-- * 末尾 m_AGVExcuter_triggerpoint / m_CTUExcuter_triggerpoint 唤醒下层 worker

-- 实现细节 / Quirks:
-- * 方法名保留 "Excuter" 拼写(项目历史命名,非 Executor)
-- * 用 var bin:string(非 object)— binid 是 "framerack_col_j" 格式字符串
-- * 所有日志走 m_logger(type,msg),type 只用 "INFO" 一档
-- * `continue` 在 while-loop for-loop 嵌套下生效,行被跳过但循环继续
-- * 末行 TaskExcuter_Running := false 是关键 — 让下一次 append 能重新进入 worker

-- 死代码 / 已知 TODO:
-- * case "Move" → debug        (占位,待业务定义 Move 订单语义)
-- * default     → debug        (catch-all,捕获 TaskType 出现意外值时方便 debug)

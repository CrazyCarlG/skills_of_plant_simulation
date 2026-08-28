/*
============================================
-- Method path : .P4_CTU.AdvancedObject.Software.RCS.m_getBinNearbyCTUActivateMarker
-- Method type : Method (root class: .P4_CTU.BasicObjects.InformationFlow.Method)
-- 作用
--   在 Tab_binState 已存在的 (rack,col,j) 格子中,
--   反向查找 "最近" 的 CTURackMarker 前置标记,
--   并把该标记写入 tab_binstate["CTUMarker",binid]。
--   是 m_addBinStateInTable 之后的第二步:先建行,再补 CTUMarker。
-- 直接调用方
--   .P4_CTU.AdvancedObject.Software.RCS.m_InitBinState
--     └─ 在调用 m_addBinStateInTable 后,通常紧跟 m_getBinNearbyCTUActivateMarker
--   .P4_CTU.ctux1_agvx1.RCS.m_InitBinState (派生实例,行为同源;CLASS == ORIGIN)
-- 关键约定
--   - binid 格式: <framerack.name>_<col>_<j>
--     其中 col 来自 Tab_RackMarker["col",i],j ∈ [2, rack.YDim]
--     与 m_addBinStateInTable 产出的 binid 完全一致,所以可以反查
--   - framerack := rack.~
--     将 rack 引用转换为 framerack Method 对象,再用 .name 拿到外框名
--   - maxrow := rack.YDim  (而非 v_y;两者在此模型上等价)
--   - 筛选条件: rackmarker.pred(k).origin.name = "CTURackMarker"
--     即只看继承源类名,不看具体子类的 RackMarker
--   - 写入语义: 命中后 tab_binstate["CTUMarker",binid] := rackmarker.pred(k)
--     若同一个 binid 对应多个 CTU 标记,k 循环靠后的会覆盖靠前的
-- 副作用 / Tab_binState schema 写入
--   仅修改 CTUMarker 列 (string/object 字段),其余 8 列不动:
--     binid, ex_rack, depth_rack, RackRow, RackCol,
--     CTUMarker, Content_de, Binstate, NumMU
-- 下游读取 CTUMarker 的字段 (见 m_occupyBin / m_releaseBin 等)
--   - 决策逻辑用 CTUMarker 找到该 bin 归属哪个 CTU,进而选出口方向
-- 实现细节 / 小瑕疵
--   - 第 1 行起始有一个前导空格 (" var rack,..."),这是 obj.Program
--     真实内容,Plant Simulation 存储特性;不要当作注解者加的,改回会破坏字节相同
--   - 内层 k 循环的 "next" (line 18) 使用 tab 缩进,其余用空格 — 疑似旧版本残留
--   - 若 Tab_RackMarker 某行 col 字段缺值或类型不匹配,会触发 num_to_str 错误
-- 死代码 / 未声明变量
--   无:framerack, rackmarker, maxrow, col, binid 均在循环体内被使用
============================================
*/

/*
============================================
-- Method path : .P4_CTU.AdvancedObject.Software.RCS.m_addBinStateInTable
-- Method type : Method (root class: .P4_CTU.BasicObjects.InformationFlow.Method)
-- Param       : rack : object
-- 作用
--   在全局 TableFile Tab_binState 中,为单个 Rack 的每个 (i,j) 单元格
--   追加一行 "Available" 状态的 Bin 记录。
-- 直接调用方
--   .P4_CTU.AdvancedObject.Software.RCS.m_InitBinState
--     └─ for i in racklist.dim: m_addBinStateInTable(rack)
--   .P4_CTU.ctux1_agvx1.RCS.m_InitBinState (派生实例,行为同源)
-- 关键约定
--   - 行 binid 格式: <rack.name>_<i>_<j>,例如 "RackA_3_4"
--   - 列循环范围: i ∈ [1, rack.v_x],j ∈ [2, rack.v_y]
--     (j 从 2 起跳,留给 Rack 自身所在行;实际产出 v_x * (v_y-1) 行)
--   - 根据 rack.movementfrom_side 决定 depth_rack / ex_rack:
--       "left"  -> depth = rack1, ex = rack2
--       "right" -> depth = rack2, ex = rack1
--   - 仅处理以上两种 case,无 default;其他取值会直接跳过 appendrow
-- 副作用 / Tab_binState schema
--   appendrow 按以下 9 列顺序写入:
--     binid, ex_rack, depth_rack, RackRow, RackCol,
--     CTUMarker, Content_de, Binstate, NumMU
--   - binid     : string,行名
--   - ex_rack   : object,外侧 Rack 引用
--   - depth_rack: object,深度方向 Rack 引用
--   - RackRow   : int(j,取值 2..v_y)
--   - RackCol   : int(i,取值 1..v_x)
--   - CTUMarker : object,初始 void(由下游赋值)
--   - Content_de: object,初始 void(由下游赋值)
--   - Binstate  : string,初始 "Available"
--   - NumMU     : int,初始 0
-- 下游读取 Tab_binState 的字段(见 m_occupyBin / m_releaseBin 等)
--   Binstate / NumMU / Rack_de / Rack_ex / RackRow / RackCol
--   CTUMarker / Content_de / Content_ex
-- 死代码
--   var CTU_marker :object  声明但未使用,推测为早期版本残留
============================================
*/
/* ============================================================
   Method path : .Models.Model.Astart
   类型        : Method (Class=.InformationFlow.Method)
   作用        : A* (A-Star) 寻路算法,4 邻域移动,曼哈顿启发式
   ---------------------------------------------------------------------
   输入:
     iGrid          : table (int cells) — 通行图;iGrid[r,c]=0 通行,非 0 障碍 (1-indexed)
     iStartR,iStartC: integer           — 起点行/列 (1-indexed)
     iGoalR,iGoalC  : integer           — 终点行/列 (1-indexed)
   返回:
     string — 路径 "r1,c1;r2,c2;...;rn,cn"(包含起终点),找不到时返回 ""
   算法要点:
     * 4 邻域 (N/S/E/W),单步代价 = 1
     * 启发式 h = |Δr| + |Δc| (曼哈顿距离)
     * 开列表:1D 6 列表 (r,c,g,f,parentR,parentC),线性扫描取最小 f
     * 闭表 closed[r,c]:2D 表,1 = 已扩展
     * gScore[r,c]:2D 表,记录该格已知最优 g
     * parentR[r,c] / parentC[r,c]:2D 表,回溯父节点
     * 终止:命中目标 或 开列表耗尽 (无路径)
   时间复杂度:
     O(N²·log N),N = 可通行格子数
   调用示例:
     var path: string
     path := .Models.Model.Astart(myGrid, 1, 1, 10, 10)
     -- path = "1,1;1,2;1,3;...;10,10"
   ============================================================ */

param iGrid: table, iStartR: integer, iStartC: integer, iGoalR: integer, iGoalC: integer: string

-- 1) 边界与端点合法性检查
var nRows: integer := iGrid.ydim
var nCols: integer := iGrid.xdim
if nRows <= 0 or nCols <= 0
  return ""
end
if iStartR < 1 or iStartR > nRows or iStartC < 1 or iStartC > nCols
  return ""
end
if iGoalR < 1 or iGoalR > nRows or iGoalC < 1 or iGoalC > nCols
  return ""
end
if iGrid[iStartR, iStartC] <> 0
  return ""
end
if iGrid[iGoalR, iGoalC] <> 0
  return ""
end
if iStartR = iGoalR and iStartC = iGoalC
  return to_str(iStartR) + "," + to_str(iStartC)
end

-- 2) 数据结构 (按网格尺寸动态分配)
var closed: table
closed := make_table("closed", nRows, nCols)
var gScore: table
gScore := make_table("gScore", nRows, nCols)
var parentR: table
parentR := make_table("parentR", nRows, nCols)
var parentC: table
parentC := make_table("parentC", nRows, nCols)
var INF: integer := 999999
var ii: integer
var jj: integer
for ii := 1 to nRows
  for jj := 1 to nCols
    gScore[ii, jj] := INF
  next
next
gScore[iStartR, iStartC] := 0

-- 3) 开列表初始化 (放入起点)
var openList: table
openList := make_table("openList", 1, 6)
openList.writeRow(1, "row,6")
openList[1, 1] := iStartR
openList[1, 2] := iStartC
openList[1, 3] := 0
openList[1, 4] := abs(iStartR - iGoalR) + abs(iStartC - iGoalC)
openList[1, 5] := 0
openList[1, 6] := 0

-- 4) 邻域偏移 (N=1, S=2, W=3, E=4)
var dR: integer[4]
dR[1] := -1
dR[2] := 1
dR[3] := 0
dR[4] := 0
var dC: integer[4]
dC[1] := 0
dC[2] := 0
dC[3] := -1
dC[4] := 1

-- 5) 主循环
var found: boolean := false
var curR: integer := 0
var curC: integer := 0
var curG: integer := 0

while openList.ydim > 0
  -- 5a) 线性扫最小 f 行
  var bestRow: integer := 1
  var bestF: integer := openList[1, 4]
  var rr: integer
  for rr := 2 to openList.ydim
    if openList[rr, 4] < bestF
      bestF := openList[rr, 4]
      bestRow := rr
    end
  next
  curR := openList[bestRow, 1]
  curC := openList[bestRow, 2]
  curG := openList[bestRow, 3]
  -- 5b) 从开列表移除 (与最后一行 swap 后剪尾)
  var lastRow: integer := openList.ydim
  if bestRow <> lastRow
    openList[bestRow, 1] := openList[lastRow, 1]
    openList[bestRow, 2] := openList[lastRow, 2]
    openList[bestRow, 3] := openList[lastRow, 3]
    openList[bestRow, 4] := openList[lastRow, 4]
    openList[bestRow, 5] := openList[lastRow, 5]
    openList[bestRow, 6] := openList[lastRow, 6]
  end
  openList.deleteRow(lastRow)

  -- 5c) 已扩展? 跳过
  if closed[curR, curC] = 1
    continue
  end
  closed[curR, curC] := 1

  -- 5d) 命中目标?
  if curR = iGoalR and curC = iGoalC
    found := true
    exit
  end

  -- 5e) 扩展 4 邻域
  var k: integer
  for k := 1 to 4
    var nR: integer := curR + dR[k]
    var nC: integer := curC + dC[k]
    if nR < 1 or nR > nRows or nC < 1 or nC > nCols
      continue
    end
    if iGrid[nR, nC] <> 0
      continue
    end
    if closed[nR, nC] = 1
      continue
    end
    var tentG: integer := curG + 1
    if gScore[nR, nC] > tentG
      gScore[nR, nC] := tentG
      parentR[nR, nC] := curR
      parentC[nR, nC] := curC
      var h: integer := abs(nR - iGoalR) + abs(nC - iGoalC)
      var newRow: integer := openList.ydim + 1
      openList.writeRow(newRow, "row,6")
      openList[newRow, 1] := nR
      openList[newRow, 2] := nC
      openList[newRow, 3] := tentG
      openList[newRow, 4] := tentG + h
      openList[newRow, 5] := curR
      openList[newRow, 6] := curC
    end
  next
end

if not found
  return ""
end

-- 6) 回溯路径 (终点→起点)
var pathR: table
pathR := make_table("pathR", 1, 1)
pathR.writeRow(1, "row,1")
var pathC: table
pathC := make_table("pathC", 1, 1)
pathC.writeRow(1, "row,1")
var walkR: integer := iGoalR
var walkC: integer := iGoalC
while true
  var n: integer := pathR.ydim + 1
  pathR.writeRow(n, "row,1")
  pathR[n, 1] := walkR
  pathC.writeRow(n, "row,1")
  pathC[n, 1] := walkC
  if walkR = iStartR and walkC = iStartC
    exit
  end
  var nextR: integer := parentR[walkR, walkC]
  var nextC: integer := parentC[walkR, walkC]
  if nextR = 0 and nextC = 0
    return ""
  end
  walkR := nextR
  walkC := nextC
end

-- 7) 反转 (起点→终点 顺序)
var lo: integer := 1
var hi: integer := pathR.ydim
while lo < hi
  var tr: integer := pathR[lo, 1]
  var tc: integer := pathC[lo, 1]
  pathR[lo, 1] := pathR[hi, 1]
  pathC[lo, 1] := pathC[hi, 1]
  pathR[hi, 1] := tr
  pathC[hi, 1] := tc
  lo := lo + 1
  hi := hi - 1
end

-- 8) 拼接结果字符串
var result: string := ""
var p: integer
for p := 1 to pathR.ydim
  if p > 1
    result := result + ";"
  end
  result := result + to_str(pathR[p, 1]) + "," + to_str(pathC[p, 1])
next
return result
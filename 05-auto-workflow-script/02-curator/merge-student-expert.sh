#!/usr/bin/env bash
# merge-student-expert.sh
#
# 流程：
#   1) 校验当前分支必须是 fea/curator
#   2) git fetch origin
#   3) 检查 origin/fea/student 和 origin/fea/expert 是否存在：
#        - 任一不存在 → 打印 "no more memory" 并退出
#   4) 检查两个分支相对于当前分支是否存在 difference
#      （用 rev-list --count 看是否还有对方独占、当前没有的 commit）：
#        - 任一 origin/<src> 领先（ahead > 0）→ 把 student 和 expert 都 merge 进来（no-ff）
#        - 否则若本分支领先于所有 src（全部 behind > 0）→ 打印 "already summary to experience"
#        - 否则（两边完全同步）→ 打印 "no more memory" 并退出
#   5) 合并冲突时退出让用户手动解决
#
#
# 运行模式：
#   默认（交互式）：手动解决冲突 / 继续跑
#     $ ./merge-student-expert.sh
#   测试（非交互）：
#     $ PRINT_MODE=1 ./merge-student-expert.sh
#
#set -euo pipefail

# ---------------------------------------------------------------------------
# 宿主机自检：让脚本在 Windows bash (Git Bash / MSYS2 / Cygwin / WSL)
# 上跑得稳一点
# ---------------------------------------------------------------------------

# 1) 检测是否在 Windows bash 环境
uname_s=$(uname -s 2>/dev/null || echo "")
case "$uname_s" in
  MINGW*|MSYS*|CYGWIN*)
    IS_WINDOWS_BASH=1
    ;;
  *)
    IS_WINDOWS_BASH=0
    ;;
esac

# 2) Windows bash 下若有 CRLF 换行，先报清楚（不然会报 "\r: command not found"）
if [ "$IS_WINDOWS_BASH" -eq 1 ]; then
  if grep -l $'\r' "$0" >/dev/null 2>&1; then
    echo "❌ 检测到 CRLF 换行，bash 在 Windows 下会炸。请先执行："
    echo "     dos2unix \"$0\"   # 或"
    echo "     sed -i 's/\\r$//' \"$0\""
    echo "   然后重新运行。"
    exit 3
  fi
fi

# 3) git 版本自检（--prune-tags 需要 git >= 2.17）
git_version=$(git --version 2>/dev/null | awk '{print $3}')
if [ -n "$git_version" ]; then
  git_major=$(printf '%s' "$git_version" | cut -d. -f1)
  git_minor=$(printf '%s' "$git_version" | cut -d. -f2)
  if [ "$git_major" -lt 2 ] || { [ "$git_major" -eq 2 ] && [ "$git_minor" -lt 17 ]; }; then
    echo "❌ git 版本 $git_version 过旧，--prune-tags 需要 >= 2.17。"
    echo "   请先升级 git：https://git-scm.com/downloads"
    exit 4
  fi
fi

# ---------------------------------------------------------------------------

REPO_DIR="/root/skills_of_plant_simulation"
EXPECTED_BRANCH="fea/curator"
SOURCE_BRANCHES=("fea/student" "fea/expert")

cd "$REPO_DIR"

echo "==> 1/4 校验当前分支"
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$EXPECTED_BRANCH" ]; then
  echo "❌ 当前分支是 '$current_branch'，必须在 '$EXPECTED_BRANCH' 上。"
  echo "   请先执行: git checkout $EXPECTED_BRANCH"
  exit 1
fi
echo "✅ 当前分支: $current_branch"

echo "==> 2/4 git fetch origin"
git fetch origin --prune --prune-tags

echo "==> 3/4 检查远端 ${SOURCE_BRANCHES[*]} 是否存在"
missing=()
for src in "${SOURCE_BRANCHES[@]}"; do
  if ! git rev-parse --verify "origin/$src" >/dev/null 2>&1; then
    missing+=("$src")
  fi
done
if [ ${#missing[@]} -gt 0 ]; then
  echo "⚠️ 远端缺少分支: ${missing[*]}"
  echo "no more memory"
  exit 10
fi
echo "✅ 两个分支都存在"

echo "==> 4/4 检查 difference 并合并"
has_diff=0
all_curator_ahead=1
for src in "${SOURCE_BRANCHES[@]}"; do
  # ahead  = origin/$src 有、当前分支没有的 commit 数（src 比 curator 新）
  # behind = 当前分支有、origin/$src 没有的 commit 数（curator 比 src 新）
  ahead=$(git rev-list --count "$current_branch".."origin/$src" 2>/dev/null || echo 0)
  behind=$(git rev-list --count "origin/$src".."$current_branch" 2>/dev/null || echo 0)
  if [ "${ahead:-0}" -gt 0 ]; then
    echo "🔍 origin/$src 比 $current_branch 领先 $ahead 个 commit"
    has_diff=1
    all_curator_ahead=0
  elif [ "${behind:-0}" -gt 0 ]; then
    echo "🔍 $current_branch 比 origin/$src 领先 $behind 个 commit（curator 已沉淀）"
  else
    echo "✅ origin/$src 与 $current_branch 完全同步"
    all_curator_ahead=0
  fi
done

if [ "$has_diff" -eq 1 ]; then
  :  # 落到下面的 merge 流程
elif [ "$all_curator_ahead" -eq 1 ]; then
  echo "already summary to experience"
  exit 11
else
  echo "no more memory"
  exit 10
fi

# 任一有 diff，把两个源分支都合并进来（no-ff，便于追溯合并点）
for src in "${SOURCE_BRANCHES[@]}"; do
  echo "----"
  echo "==> 合并 origin/$src -> $current_branch"
  merge_msg="merge $src into $current_branch @ $(date +%Y-%m-%d)"
  if git merge --no-ff -m "$merge_msg" "origin/$src"; then
    echo "✅ $src 合并完成"
  else
    echo "❌ 合并 $src 时出现冲突，请手动解决后再继续"
    echo "   解决后执行: git add -A && git commit --no-edit"
    echo "   中途放弃合并: git merge --abort"
    exit 2
  fi
done

echo "----"
echo "✅ 全部合并完成"

# ---------------------------------------------------------------------------
# 5) PRINT_MODE 开关：PRINT_MODE=1 或带 --print 时只打印结果，不进 REPL
# ---------------------------------------------------------------------------
PRINT_FLAG=""
if [ "${PRINT_MODE:-0}" = "1" ] || { [ $# -gt 0 ] && [ "$1" = "--print" ]; }; then
  PRINT_FLAG="--print"
  echo "ℹ️  PRINT_MODE 开启，将以非交互模式结束"
  exit 0
fi

echo "ℹ️  合并完成。可继续在 REPL 里跑后续 curator 沉淀流程。"
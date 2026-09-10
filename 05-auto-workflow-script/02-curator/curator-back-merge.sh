#!/usr/bin/env bash
# curator-back-merge.sh
#
# 把 curator 沉淀的 commit 回流到 fea/expert 和 fea/student。
# (与 merge-student-expert.sh 方向相反)
#
# 流程：
#   1) 校验当前分支必须是 fea/curator
#   2) git fetch origin --prune --prune-tags
#   3) 检查 origin/fea/curator 是否存在（不存在就直接退出）
#   4) 检查 origin/fea/curator 相对于 当前 fea/curator 是否有新 commit
#        - 无差异 → 打印 "no more memory" 并退出
#   5) 遍历目标分支 TARGETS=("fea/expert" "fea/student")：
#        a) 检查 origin/$target 是否存在；不存在则跳过
#        b) checkout 到本地 $target（不存在就从 origin/$target 建）
#        c) merge origin/fea/curator （no-ff） → 合并 curator 的沉淀
#        d) push origin $target
#   6) 处理冲突时退出让用户手动解决
#   7) 结束后回到 fea/curator 分支
#
# 运行：
#   $ ./curator-back-merge.sh
#
# 可选：
#   $ ./curator-back-merge.sh --target fea/expert          # 只回流向 expert
#   $ ./curator-back-merge.sh --dry-run                    # 不真做 checkout/merge/push
#   $ PRINT_MODE=1 ./curator-back-merge.sh                  # 非交互
#
# 退出码：
#   1 = 当前分支不是 fea/curator
#   2 = git 不可用
#   3 = 检测到 CRLF 换行
#   4 = git 版本过旧
#   5 = 远端不可达 / 远端缺少 fea/curator
#   6 = 暂存区脏 / 工作区脏（不允许切分支）
#   7 = checkout 失败
#   8 = merge 冲突（让用户手动解决）
#   9 = push 失败
#  10 = no more memory（无回流内容，正常退出）
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

# 2) Windows bash 下若有 CRLF 换行，先报清楚
if [ "$IS_WINDOWS_BASH" -eq 1 ]; then
  if grep -l $'\r' "$0" >/dev/null 2>&1; then
    echo "❌ 检测到 CRLF 换行，bash 在 Windows 下会炸。请先执行："
    echo "     dos2unix \"\$0\"   # 或"
    echo "     sed -i 's/\\r\$//' \"\$0\""
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
SOURCE_BRANCH="fea/curator"   # 把这个分支的 commit 回流
DEFAULT_TARGETS=("fea/expert" "fea/student")

CURATOR_NAME="Curator"
CURATOR_EMAIL="plant-simulation-curator.md@agent.com"

# ---------------------------------------------------------------------------
# 解析参数
# ---------------------------------------------------------------------------
TARGETS=()
DRY_RUN=0
while [ $# -gt 0 ]; do
  case "$1" in
    --target)
      TARGETS+=("$2")
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      sed -n '2,55p' "$0"
      exit 0
      ;;
    *)
      echo "❌ 未知参数: $1"
      exit 1
      ;;
  esac
done

if [ "${#TARGETS[@]}" -eq 0 ]; then
  TARGETS=("${DEFAULT_TARGETS[@]}")
fi

cd "$REPO_DIR"

echo "==> 1.5/6 设置本地 git 身份（仅本仓库 local config）"
git config --local user.name  "$CURATOR_NAME"
git config --local user.email "$CURATOR_EMAIL"
echo "   user.name  = $(git config --local --get user.name)"
echo "   user.email = $(git config --local --get user.email)"

echo "==> 1/6 校验 git 可用"
if ! command -v git >/dev/null 2>&1; then
  echo "❌ 找不到 git 命令"
  exit 2
fi
echo "✅ git 可用: $(command -v git)"

echo "==> 2/6 校验当前分支"
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$SOURCE_BRANCH" ]; then
  echo "❌ 当前分支是 '$current_branch'，必须在 '$SOURCE_BRANCH' 上。"
  echo "   请先执行: git checkout $SOURCE_BRANCH"
  exit 1
fi
echo "✅ 当前分支: $current_branch"

echo "==> 3/6 git fetch origin"
git fetch origin --prune --prune-tags

echo "==> 4/6 校验远端 origin/$SOURCE_BRANCH"
if ! git rev-parse --verify "origin/$SOURCE_BRANCH" >/dev/null 2>&1; then
  echo "❌ 远端缺少 origin/$SOURCE_BRANCH"
  echo "   请先运行 commit-and-push-curator.sh 把 curator 沉淀推上去"
  exit 5
fi
echo "✅ origin/$SOURCE_BRANCH 存在"

echo "==> 5/6 校验工作区干净"
if ! git diff --quiet HEAD 2>/dev/null || ! git diff --cached --quiet HEAD 2>/dev/null; then
  echo "❌ 工作区或暂存区有未提交变更，不允许切分支。请先 commit/stash。"
  exit 6
fi
echo "✅ 工作区干净"

echo "==> 6/6 检查是否有可回流的 commit"
# 提前把本地 $SOURCE_BRANCH 同步到 origin/$SOURCE_BRANCH
git merge --ff-only "origin/$SOURCE_BRANCH" >/dev/null 2>&1 || true

# ahead  = origin/$SOURCE_BRANCH 领先 本地 $SOURCE_BRANCH 的 commit 数
# behind = 本地 $SOURCE_BRANCH 领先 origin/$SOURCE_BRANCH 的 commit 数
ahead=$(git rev-list --count "$SOURCE_BRANCH..origin/$SOURCE_BRANCH" 2>/dev/null || echo 0)
behind=$(git rev-list --count "origin/$SOURCE_BRANCH..$SOURCE_BRANCH" 2>/dev/null || echo 0)

if [ "${behind:-0}" -eq 0 ]; then
  echo "ℹ️  本地 $SOURCE_BRANCH 与 origin/$SOURCE_BRANCH 已同步，无需回流"
  echo "no more memory"
  exit 10
fi
echo "🔍 本地 $SOURCE_BRANCH 比 origin/$SOURCE_BRANCH 领先 $behind 个 commit，准备回流"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "ℹ️  --dry-run 已启用，仅打印计划："
  echo "   将把 origin/$SOURCE_BRANCH 的最新 $behind 个 commit merge 到下列分支："
  for t in "${TARGETS[@]}"; do
    echo "     - $t"
  done
  echo "   然后切回 $SOURCE_BRANCH"
  exit 0
fi

# ---------------------------------------------------------------------------
# 逐个 target 分支执行：checkout → merge → push
# ---------------------------------------------------------------------------
# 记录原始分支以便最后切回
ORIG_BRANCH="$current_branch"

failed_target=""
for target in "${TARGETS[@]}"; do
  echo "----"
  echo "==> 处理 target: $target"

  # 6.1 检查远端 target 是否存在
  if ! git rev-parse --verify "origin/$target" >/dev/null 2>&1; then
    echo "⚠️  远端缺少 origin/$target，跳过"
    continue
  fi

  # 6.2 checkout target（本地不存在就从 origin/$target 建）
  if git show-ref --verify --quiet "refs/heads/$target"; then
    if ! git checkout "$target"; then
      echo "❌ checkout $target 失败"
      failed_target="$target"
      exit 7
    fi
  else
    echo "ℹ️  本地 $target 不存在，从 origin/$target 建"
    if ! git checkout -b "$target" "origin/$target"; then
      echo "❌ 从 origin/$target 建本地 $target 失败"
      failed_target="$target"
      exit 7
    fi
  fi
  echo "✅ 已切换到 $target"

  # 6.3 merge origin/$SOURCE_BRANCH （no-ff）
  merge_msg="back-merge $SOURCE_BRANCH into $target @ $(date +%Y-%m-%d)"
  if git merge --no-ff -m "$merge_msg" "origin/$SOURCE_BRANCH"; then
    echo "✅ merge origin/$SOURCE_BRANCH 完成"
  else
    echo "❌ merge 出现冲突，请手动解决："
    echo "     1) git status   # 看冲突文件"
    echo "     2) 解决冲突    # 编辑 -> git add"
    echo "     3) git commit  # 完成 merge"
    echo "     4) git push origin $target"
    echo "   解决后重新运行本脚本继续处理剩余 target"
    failed_target="$target"
    exit 8
  fi

  # 6.4 push origin
  if git push origin "$target"; then
    echo "✅ push origin/$target 完成"
  else
    echo "❌ push origin/$target 失败"
    echo "   排查建议:"
    echo "     1) 检查鉴权 / SSH key / credential helper"
    echo "     2) git fetch origin && git status 看是否需要 rebase"
    echo "     3) 必要时手动: git push origin $target"
    failed_target="$target"
    exit 9
  fi
done

# ---------------------------------------------------------------------------
# 收尾：回到原始分支
# ---------------------------------------------------------------------------
echo "----"
echo "==> 切回原始分支 $ORIG_BRANCH"
if [ "$ORIG_BRANCH" != "$(git rev-parse --abbrev-ref HEAD)" ]; then
  if ! git checkout "$ORIG_BRANCH"; then
    echo "⚠️  切回 $ORIG_BRANCH 失败，请手动: git checkout $ORIG_BRANCH"
  fi
fi

if [ -n "$failed_target" ]; then
  echo "❌ 部分 target 失败: $failed_target"
  exit 9
fi

echo "----"
echo "✅ curator 回流完成（$SOURCE_BRANCH → ${TARGETS[*]}）"

# ---------------------------------------------------------------------------
# PRINT_MODE 开关
# ---------------------------------------------------------------------------
if [ "${PRINT_MODE:-0}" = "1" ]; then
  echo "ℹ️  PRINT_MODE 开启，非交互结束"
  exit 0
fi
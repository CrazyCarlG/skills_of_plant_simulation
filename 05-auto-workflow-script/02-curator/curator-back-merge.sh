#!/usr/bin/env bash
# curator-back-merge.sh
#
# 把 curator 沉淀的 commit 回流到 fea/expert 和 fea/student，
# 并同时 push fea/expert / fea/student / fea/curator 三个分支。
# (与 merge-student-expert.sh 方向相反)
#
# 流程：
#   1) 校验当前分支必须是 fea/curator
#   2) git fetch origin --prune --prune-tags
#   3) 校验远端 origin/fea/curator 是否存在（不存在直接退出）
#   4) 校验工作区干净
#   5) 同步三个分支到最新：
#        - fea/curator ← origin/fea/curator (fast-forward)
#        - fea/expert  ← origin/fea/expert  (checkout + pull --ff-only + 回到 curator)
#        - fea/student ← origin/fea/student (checkout + pull --ff-only + 回到 curator)
#   6) 若 curator 相对 expert/student 没有新 commit：
#        打印 "no more memory"，但仍继续 push 三个分支
#   7) 遍历 TARGETS=("fea/expert" "fea/student")：
#        a) 检查 origin/$target 是否存在；不存在则跳过
#        b) checkout 本地 $target（不存在就从 origin/$target 建）
#        c) 若 $target 已有 $SOURCE_BRANCH 最新 commit → 跳过 merge
#        d) merge $SOURCE_BRANCH （no-ff） → 合并 curator 的沉淀
#        e) 冲突时退出让用户手动解决（merge 完成时不立即 push）
#   8) 三分支同时 push：git push origin fea/expert fea/student fea/curator
#   9) 收尾回到 fea/curator
#
# 运行：
#   $ ./curator-back-merge.sh
#
# 可选环境变量：
#   $ PRINT_MODE=1 ./curator-back-merge.sh                  # 非交互
#
# 退出码：
#   1 = 当前分支不是 fea/curator
#   2 = git 不可用
#   3 = 检测到 CRLF 换行
#   4 = git 版本过旧
#   5 = 远端不可达 / 远端缺少 fea/curator
#   6 = 暂存区脏 / 工作区脏（不允许切分支）
#   7 = checkout / pull 失败
#   8 = merge 冲突（让用户手动解决）
#   9 = push 失败
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
# 同时 push 的三个分支（顺序：先 expert/student，再 curator）
PUSH_BRANCHES=("fea/expert" "fea/student" "fea/curator")

CURATOR_NAME="Curator"
CURATOR_EMAIL="plant-simulation-curator.md@agent.com"

# ---------------------------------------------------------------------------
# 目标分支（固定，不接参数）
# ---------------------------------------------------------------------------
TARGETS=("${DEFAULT_TARGETS[@]}")

cd "$REPO_DIR"

echo "==> 1.5/8 设置本地 git 身份（仅本仓库 local config）"
git config --local user.name  "$CURATOR_NAME"
git config --local user.email "$CURATOR_EMAIL"
echo "   user.name  = $(git config --local --get user.name)"
echo "   user.email = $(git config --local --get user.email)"

echo "==> 1/8 校验 git 可用"
if ! command -v git >/dev/null 2>&1; then
  echo "❌ 找不到 git 命令"
  exit 2
fi
echo "✅ git 可用: $(command -v git)"

echo "==> 2/8 校验当前分支"
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$SOURCE_BRANCH" ]; then
  echo "❌ 当前分支是 '$current_branch'，必须在 '$SOURCE_BRANCH' 上。"
  echo "   请先执行: git checkout $SOURCE_BRANCH"
  exit 1
fi
echo "✅ 当前分支: $current_branch"

echo "==> 3/8 git fetch origin"
git fetch origin --prune --prune-tags

echo "==> 4/8 校验远端 origin/$SOURCE_BRANCH"
if ! git rev-parse --verify "origin/$SOURCE_BRANCH" >/dev/null 2>&1; then
  echo "❌ 远端缺少 origin/$SOURCE_BRANCH"
  echo "   请先运行 commit-and-push-curator.sh 把 curator 沉淀推上去"
  exit 5
fi
echo "✅ origin/$SOURCE_BRANCH 存在"

echo "==> 5/8 校验工作区干净"
if ! git diff --quiet HEAD 2>/dev/null || ! git diff --cached --quiet HEAD 2>/dev/null; then
  echo "❌ 工作区或暂存区有未提交变更，不允许切分支。请先 commit/stash。"
  exit 6
fi
echo "✅ 工作区干净"

# ---------------------------------------------------------------------------
# 6/8：把三个分支（curator/expert/student）都 pull 到最新
# ---------------------------------------------------------------------------
echo "==> 6/8 同步三个分支（fea/curator / fea/expert / fea/student → 最新）"

# 6.1 curator: ff-merge origin/fea/curator（容忍失败：若本地已 ff-diverged 留到后面处理）
git merge --ff-only "origin/$SOURCE_BRANCH" >/dev/null 2>&1 || true
echo "✅ fea/curator 已对齐 origin/$SOURCE_BRANCH（HEAD=$(git rev-parse --short HEAD)）"

# 6.2 / 6.3 expert & student：checkout → pull --ff-only → 回到 curator
# 用函数复用，避免大段重复代码
pull_one_branch() {
  local br="$1"
  if ! git rev-parse --verify "origin/$br" >/dev/null 2>&1; then
    echo "⚠️  远端缺少 origin/$br，跳过 pull"
    return 0
  fi

  # checkout 本地分支（不存在就从 origin/$br 建）
  if git show-ref --verify --quiet "refs/heads/$br"; then
    if ! git checkout "$br" >/dev/null 2>&1; then
      echo "❌ checkout $br 失败"
      return 7
    fi
  else
    echo "ℹ️  本地 $br 不存在，从 origin/$br 建"
    if ! git checkout -b "$br" "origin/$br" >/dev/null 2>&1; then
      echo "❌ 从 origin/$br 建本地分支失败"
      return 7
    fi
  fi

  # pull --ff-only（已对齐 origin 后应能 ff；如果本地有未推 commit 会失败）
  if git pull --ff-only origin "$br"; then
    echo "✅ pull origin/$br 完成（HEAD=$(git rev-parse --short HEAD)）"
  else
    echo "❌ pull origin/$br 失败（可能本地有未推 commit 或已 diverged）"
    echo "   排查: git log origin/$br..$br"
    return 7
  fi

  # 回到 curator
  if ! git checkout "$SOURCE_BRANCH" >/dev/null 2>&1; then
    echo "⚠️  切回 $SOURCE_BRANCH 失败，请手动: git checkout $SOURCE_BRANCH"
  fi
  return 0
}

pull_one_branch fea/expert || exit 7
pull_one_branch fea/student || exit 7

echo "✅ 三分支 pull 完毕，当前在 $SOURCE_BRANCH"

# ---------------------------------------------------------------------------
# 7/8：把 curator 的 commit 回流到 expert 和 student（不立即 push）
# ---------------------------------------------------------------------------
echo "==> 7/8 把 $SOURCE_BRANCH 合并到 ${TARGETS[*]}"

# 检查是否真有 curator 独有的 commit 需要回流
need_merge=0
for target in "${TARGETS[@]}"; do
  if git rev-parse --verify "origin/$target" >/dev/null 2>&1; then
    target_behind=$(git rev-list --count "$target..$SOURCE_BRANCH" 2>/dev/null || echo 0)
    if [ "${target_behind:-0}" -gt 0 ]; then
      echo "🔍 $target 落后 $SOURCE_BRANCH $target_behind 个 commit，将 merge"
      need_merge=1
    fi
  fi
done

if [ "$need_merge" -eq 0 ]; then
  echo "ℹ️  curator 无新 commit 待回流到 expert/student"
  echo "no more memory"
fi

ORIG_BRANCH="$current_branch"
failed_target=""

for target in "${TARGETS[@]}"; do
  echo "----"
  echo "==> 处理 target: $target"

  # 7.1 远端缺失则跳过 merge（也不能 push 这个分支）
  if ! git rev-parse --verify "origin/$target" >/dev/null 2>&1; then
    echo "⚠️  远端缺少 origin/$target，跳过 merge"
    continue
  fi

  # 7.2 checkout target（本地不存在就从 origin/$target 建）
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

  # 7.3 若 target 已经包含 curator 最新 commit（被 step 6 的 pull --ff-only 已经带回，
  #     # 或上一轮 back-merge 已经合并过），则跳过 merge
  target_behind=$(git rev-list --count "$target..$SOURCE_BRANCH" 2>/dev/null || echo 0)
  if [ "${target_behind:-0}" -eq 0 ]; then
    echo "ℹ️  $target 已包含 $SOURCE_BRANCH 最新 commit，跳过 merge"
    continue
  fi

  # 7.4 merge $SOURCE_BRANCH （no-ff）
  merge_msg="back-merge $SOURCE_BRANCH into $target @ $(date +%Y-%m-%d)"
  if git merge --no-ff -m "$merge_msg" "$SOURCE_BRANCH"; then
    echo "✅ merge $SOURCE_BRANCH → $target 完成（HEAD=$(git rev-parse --short HEAD)）"
  else
    echo "❌ merge 出现冲突，请手动解决："
    echo "     1) git status   # 看冲突文件"
    echo "     2) 解决冲突    # 编辑 -> git add"
    echo "     3) git commit  # 完成 merge（注意不要 push，等本脚本后续统一 push）"
    echo "     4) 重新运行本脚本，会先 pull 三分支再做 merge，最后统一 push"
    failed_target="$target"
    exit 8
  fi
done

# ---------------------------------------------------------------------------
# 8/8：三分支同时 push（一次网络连接推三个 ref）
# ---------------------------------------------------------------------------
echo "----"
echo "==> 三分支同时 push: ${PUSH_BRANCHES[*]}"

# 动态过滤掉远端不存在的分支（避免 push 一个 origin 上没有的 ref 报错）
push_args=()
for br in "${PUSH_BRANCHES[@]}"; do
  if git rev-parse --verify "origin/$br" >/dev/null 2>&1; then
    push_args+=("$br")
  else
    echo "⚠️  远端缺少 origin/$br，跳过 push 该分支"
  fi
done

if [ "${#push_args[@]}" -eq 0 ]; then
  echo "❌ 三个分支在远端都不存在，无法 push"
  exit 9
fi

if git push origin "${push_args[@]}"; then
  echo "✅ 三分支 push 完成: ${push_args[*]}"
else
  echo "❌ push 失败"
  echo "   排查建议:"
  echo "     1) 检查鉴权 / SSH key / credential helper"
  echo "     2) git fetch origin && git status 看是否需要 rebase"
  echo "     3) 必要时手动: git push origin ${push_args[*]}"
  failed_target="push"
  exit 9
fi

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
  echo "❌ 部分操作失败: $failed_target"
  exit 9
fi

echo "----"
echo "✅ curator 回流完成（$SOURCE_BRANCH → ${TARGETS[*]}，三分支已同时 push）"

# ---------------------------------------------------------------------------
# PRINT_MODE 开关
# ---------------------------------------------------------------------------
if [ "${PRINT_MODE:-0}" = "1" ]; then
  echo "ℹ️  PRINT_MODE 开启，非交互结束"
  exit 0
fi
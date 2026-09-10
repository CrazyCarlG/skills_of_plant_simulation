#!/usr/bin/env bash
# commit-and-push-curator.sh
#
# 流程：
#   1) 校验当前分支必须是 fea/curator
#   2) 校验 git 可用、远端可达
#   3) 设置本地 git 身份：
#        Name  : Curator
#        Email : plant-simulation-curator.md@agent.com
#        (仅在当前仓库 local config 内设置，不动全局 user.*)
#   4) git add .
#   5) 若暂存区为空 → 打印 "no more memory" 并退出（不产生空 commit）
#   6) git commit -m "<默认消息：curator:沉淀 N 个文件 @ 日期>"
#   7) git push origin fea/curator
#      - 失败时给出可操作的恢复提示
#
# 运行：
#   $ ./commit-and-push-curator.sh
#
# 可选：
#   $ ./commit-and-push-curator.sh --message "manual commit msg"   # 自定义 commit 文案
#   $ ./commit-and-push-curator.sh --dry-run                       # 只跑 add + status，不 commit/push
#   $ PRINT_MODE=1 ./commit-and-push-curator.sh                    # 非交互（保留 push）
#
# 退出码：
#   1 = 当前分支不是 fea/curator
#   2 = git 不可用
#   3 = 检测到 CRLF 换行
#   4 = git 版本过旧
#   5 = 远端不可达
#   6 = 暂存区为空（已打印 no more memory）
#   7 = commit 失败
#   8 = push 失败
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
    echo "     sed -i 's/\\r$//' \"\$0\""
    echo "   然后重新运行。"
    exit 3
  fi
fi

# 3) git 版本自检
git_version=$(git --version 2>/dev/null | awk '{print $3}')
if [ -n "$git_version" ]; then
  git_major=$(printf '%s' "$git_version" | cut -d. -f1)
  git_minor=$(printf '%s' "$git_version" | cut -d. -f2)
  if [ "$git_major" -lt 2 ] || { [ "$git_major" -eq 2 ] && [ "$git_minor" -lt 17 ]; }; then
    echo "❌ git 版本 $git_version 过旧。"
    echo "   请先升级 git：https://git-scm.com/downloads"
    exit 4
  fi
fi

# ---------------------------------------------------------------------------

REPO_DIR="/root/skills_of_plant_simulation"
EXPECTED_BRANCH="fea/curator"
REMOTE_NAME="origin"

CURATOR_NAME="Curator"
CURATOR_EMAIL="plant-simulation-curator.md@agent.com"

# ---------------------------------------------------------------------------
# 解析参数
# ---------------------------------------------------------------------------
CUSTOM_MSG=""
DRY_RUN=0
while [ $# -gt 0 ]; do
  case "$1" in
    -m|--message)
      CUSTOM_MSG="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      sed -n '2,40p' "$0"
      exit 0
      ;;
    *)
      echo "❌ 未知参数: $1"
      exit 1
      ;;
  esac
done

# ---------------------------------------------------------------------------
# 主流程
# ---------------------------------------------------------------------------

cd "$REPO_DIR"

echo "==> 1/6 校验 git"
if ! command -v git >/dev/null 2>&1; then
  echo "❌ 找不到 git 命令"
  exit 2
fi
echo "✅ git 可用: $(command -v git)"

echo "==> 2/6 校验当前分支"
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$EXPECTED_BRANCH" ]; then
  echo "❌ 当前分支是 '$current_branch'，必须在 '$EXPECTED_BRANCH' 上。"
  echo "   请先执行: git checkout $EXPECTED_BRANCH"
  exit 1
fi
echo "✅ 当前分支: $current_branch"

echo "==> 3/6 校验远端 $REMOTE_NAME 可达"
if ! git ls-remote --heads "$REMOTE_NAME" "$EXPECTED_BRANCH" >/dev/null 2>&1; then
  echo "❌ 远端 $REMOTE_NAME 上的 $EXPECTED_BRANCH 不可达"
  echo "   请先检查: git remote -v && git fetch $REMOTE_NAME"
  exit 5
fi
echo "✅ 远端 $REMOTE_NAME/$EXPECTED_BRANCH 可达"

echo "==> 4/6 设置本地 git 身份（仅本仓库 local config）"
git config --local user.name  "$CURATOR_NAME"
git config --local user.email "$CURATOR_EMAIL"
echo "   user.name  = $(git config --local --get user.name)"
echo "   user.email = $(git config --local --get user.email)"

echo "==> 5/6 git add ."
git add .
if [ "$DRY_RUN" -eq 1 ]; then
  echo "ℹ️  --dry-run 已启用，仅打印 status 后退出"
  git status --short
  exit 0
fi

# 暂存区是否为空
staged_count=$(git diff --cached --name-only | wc -l | tr -d ' ')
if [ "${staged_count:-0}" -eq 0 ]; then
  echo "no more memory"
  exit 6
fi

echo "==> 6/6 commit + push"
if [ -n "$CUSTOM_MSG" ]; then
  commit_msg="$CUSTOM_MSG"
else
  commit_msg="curator:沉淀 ${staged_count} 个文件 @ $(date +%Y-%m-%d)"
fi

if git commit -m "$commit_msg"; then
  echo "✅ commit 完成: $commit_msg"
else
  echo "❌ commit 失败"
  exit 7
fi

if git push "$REMOTE_NAME" "$EXPECTED_BRANCH"; then
  echo "✅ push 完成: $REMOTE_NAME/$EXPECTED_BRANCH"
else
  echo "❌ push 失败"
  echo "   排查建议:"
  echo "     1) 检查鉴权 / SSH key / credential helper"
  echo "     2) git fetch $REMOTE_NAME && git status 看是否需要 rebase"
  echo "     3) 必要时手动: git push $REMOTE_NAME $EXPECTED_BRANCH"
  exit 8
fi

echo "----"
echo "✅ 全部完成"

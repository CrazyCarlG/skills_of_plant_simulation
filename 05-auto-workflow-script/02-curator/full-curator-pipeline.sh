#!/usr/bin/env bash
# full-curator-pipeline.sh
#
# 一键串起 curator 的完整三段流水：
#   1) merge-student-expert.sh   把 origin/fea/student 和 origin/fea/expert 合到 fea/curator
#   2) run-curator-session.sh    启动 plant-simulation-experience-curator agent
#                                 （默认 --print 非交互，便于串接；可用 --interactive 切回交互）
#   3) commit-and-push-curator.sh 提交并推送 fea/curator
#
# 之所以是 wrapper 而不是把三段逻辑塞进一个文件：
#   - 三个脚本各自独立、签名清晰，便于单独跑、单独调试
#   - "no more memory"（暂存区为空 / 远端没有新 commit）在这里不是失败，
#     而是流水线正常出口
#
# 运行：
#   $ ./full-curator-pipeline.sh                    # 默认全跑 + session 非交互
#   $ ./full-curator-pipeline.sh --interactive      # 让 session 走交互模式
#   $ ./full-curator-pipeline.sh --dry-run-push     # 最后一步只跑 add + status，不 commit/push
#   $ ./full-curator-pipeline.sh --skip-merge       # 跳过 merge 步骤
#   $ ./full-curator-pipeline.sh --skip-session     # 跳过 session 步骤
#   $ ./full-curator-pipeline.sh --skip-push        # 跳过 commit+push 步骤
#   $ ./full-curator-pipeline.sh --message "..."    # 透传 commit 文案
#
# 退出码：透传被调用脚本的非"no more memory"退出码
#        merge   退出 10（no more memory）/ 11（already summary）→ 继续
#        push    退出 6（no more memory）→ 正常退出 0
#
#set -euo pipefail

# ---------------------------------------------------------------------------
# 宿主机自检：让脚本在 Windows bash (Git Bash / MSYS2 / Cygwin / WSL)
# 上跑得稳一点（沿用 02-curator 同款的 CRLF + git 版本检测）
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

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="/root/skills_of_plant_simulation"
EXPECTED_BRANCH="fea/curator"

cd "$REPO_DIR"

# ---------------------------------------------------------------------------
# 解析参数
# ---------------------------------------------------------------------------
INTERACTIVE=0
DRY_RUN_PUSH=0
SKIP_MERGE=0
SKIP_SESSION=0
SKIP_PUSH=0
CUSTOM_MSG=""
EXTRA_ARGS=()

while [ $# -gt 0 ]; do
  case "$1" in
    --interactive)
      INTERACTIVE=1
      shift
      ;;
    --dry-run-push)
      DRY_RUN_PUSH=1
      shift
      ;;
    --skip-merge)
      SKIP_MERGE=1
      shift
      ;;
    --skip-session)
      SKIP_SESSION=1
      shift
      ;;
    --skip-push)
      SKIP_PUSH=1
      shift
      ;;
    -m|--message)
      CUSTOM_MSG="$2"
      shift 2
      ;;
    -h|--help)
      sed -n '2,45p' "$0"
      exit 0
      ;;
    *)
      EXTRA_ARGS+=("$1")
      shift
      ;;
  esac
done

# ---------------------------------------------------------------------------
# Step 0：分支校验
# ---------------------------------------------------------------------------
echo "==> 0/4 校验当前分支"
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$EXPECTED_BRANCH" ]; then
  echo "❌ 当前分支是 '$current_branch'，必须在 '$EXPECTED_BRANCH' 上。"
  echo "   请先执行: git checkout $EXPECTED_BRANCH"
  exit 1
fi
echo "✅ 当前分支: $current_branch"

# ---------------------------------------------------------------------------
# Step 1：merge-student-expert
# ---------------------------------------------------------------------------
if [ "$SKIP_MERGE" -eq 0 ]; then
  echo "----"
  echo "==> 1/4 merge-student-expert"
  if "$SCRIPT_DIR/merge-student-expert.sh" "${EXTRA_ARGS[@]}"; then
    echo "✅ merge 完成"
  else
    rc=$?
    if [ "$rc" -eq 10 ]; then
      echo "ℹ️  merge 返回 10（no more memory），继续"
    elif [ "$rc" -eq 11 ]; then
      echo "ℹ️  merge 返回 11（already summary to experience），继续"
    else
      echo "❌ merge 失败 (exit $rc)，流水线中止"
      echo "   如果是合并冲突，请手动解决后重跑"
      exit "$rc"
    fi
  fi
else
  echo "⏭️  跳过 merge-student-expert"
fi

# ---------------------------------------------------------------------------
# Step 2：run-curator-session
# ---------------------------------------------------------------------------
if [ "$SKIP_SESSION" -eq 0 ]; then
  echo "----"
  echo "==> 2/4 run-curator-session"
  session_args=()
  if [ "$INTERACTIVE" -eq 0 ]; then
    session_args+=(--print)
    echo "   mode  : 非交互（--print）"
  else
    echo "   mode  : 交互（REPL）"
  fi

  # 透传额外参数（除掉已消费的开关），便于临时切模型等
  if [ "${#EXTRA_ARGS[@]}" -gt 0 ]; then
    echo "   extra : ${EXTRA_ARGS[*]}"
  fi

  if "$SCRIPT_DIR/run-curator-session.sh" "${session_args[@]}" "${EXTRA_ARGS[@]}"; then
    echo "✅ session 完成"
  else
    rc=$?
    echo "❌ session 失败 (exit $rc)，流水线中止"
    exit "$rc"
  fi
else
  echo "⏭️  跳过 run-curator-session"
fi

# ---------------------------------------------------------------------------
# Step 3：commit-and-push-curator
# ---------------------------------------------------------------------------
if [ "$SKIP_PUSH" -eq 0 ]; then
  echo "----"
  echo "==> 3/4 commit-and-push-curator"
  push_args=()
  if [ "$DRY_RUN_PUSH" -eq 1 ]; then
    push_args+=(--dry-run)
    echo "   mode  : dry-run"
  fi
  if [ -n "$CUSTOM_MSG" ]; then
    push_args+=(-m "$CUSTOM_MSG")
    echo "   msg   : $CUSTOM_MSG"
  fi

  if "$SCRIPT_DIR/commit-and-push-curator.sh" "${push_args[@]}"; then
    echo "✅ commit + push 完成"
  else
    rc=$?
    if [ "$rc" -eq 6 ]; then
      echo "ℹ️  push 返回 6（no more memory），流水线正常结束"
      exit 0
    else
      echo "❌ commit-and-push 失败 (exit $rc)，流水线中止"
      exit "$rc"
    fi
  fi
else
  echo "⏭️  跳过 commit-and-push-curator"
fi

# ---------------------------------------------------------------------------
echo "----"
echo "✅ 完整 curator 流水线完成（merge → session → commit+push）"

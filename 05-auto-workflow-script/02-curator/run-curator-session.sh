#!/usr/bin/env bash
# run-curator-session.sh
#
# 流程：
#   1) 校验当前分支必须是 fea/curator
#   2) 校验 openclaude CLI 可用
#   3) 启动 OpenClaude REPL 会话：
#        - agent : plant-simulation-experience-curator
#        - prompt: 请总结student和expert新的memory为经验到03-modeling-experience文件夹内
#        - 权限 : 本仓库（/root/skills_of_plant_simulation）内
#                 读 / 编辑 / 执行命令 全部允许
#                 (Read Edit Write Glob Grep Bash 白名单；
#                  其它工具如 Agent / Skill / NotebookEdit 等仍禁用)
#        - 作用域 : 通过 --add-dir 把可读写范围限定到本仓库根目录
#
# 运行：
#   $ ./run-curator-session.sh
#
# 可选：透传额外 openclaude 参数
#   $ ./run-curator-session.sh --print              # 走非交互模式
#   $ ./run-curator-session.sh --model sonnet       # 临时切模型
#
# 退出码：
#   1 = 当前分支不是 fea/curator
#   2 = openclaude CLI 不可用
#   3 = 检测到 CRLF 换行
#   4 = git 版本过旧
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
AGENT_NAME="plant-simulation-experience-curator"
PROMPT="请总结student和expert新的memory为经验到03-modeling-experience文件夹内"

cd "$REPO_DIR"

echo "==> 1/3 校验当前分支"
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$EXPECTED_BRANCH" ]; then
  echo "❌ 当前分支是 '$current_branch'，必须在 '$EXPECTED_BRANCH' 上。"
  echo "   请先执行: git checkout $EXPECTED_BRANCH"
  exit 1
fi
echo "✅ 当前分支: $current_branch"

echo "==> 2/3 校验 openclaude CLI"
if ! command -v openclaude >/dev/null 2>&1; then
  echo "❌ 找不到 openclaude 命令"
  exit 2
fi
echo "✅ openclaude 可用: $(command -v openclaude)"

echo "==> 3/3 启动 curator 会话"
echo "   repo  : $REPO_DIR"
echo "   agent : $AGENT_NAME"
echo "   prompt: $PROMPT"
echo "   scope : $REPO_DIR（通过 --add-dir 限定可读写范围）"
echo "   tools : Read Edit Write Glob Grep Bash（白名单）"
echo "   mode  : acceptEdits"
echo "----"

exec openclaude \
  --agent "$AGENT_NAME" \
  --add-dir "$REPO_DIR" \
  --allowedTools "Read Edit Write Glob Grep Bash" \
  --permission-mode acceptEdits \
  "$PROMPT" "$@"

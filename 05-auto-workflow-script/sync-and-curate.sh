#!/usr/bin/env bash
# sync-and-curate.sh
#
# 流程：
#   1) 校验当前分支必须是 fea/optimizer
#   2) git fetch 后若 fea/optimizer 落后 origin/fea/optimizer 则 git pull --ff-only
#   3) 将 origin/fea/Learning 合并到当前 fea/optimizer（no-ff，便于追溯合并点）
#   4) 启动一个 openclaude 会话，调用 plant-simulation-experience-curator，
#      让 curator 阅读 03-agent-memory/ 下 expert 的 session summary，
#      按 CONTRIBUTING.md 的格式沉淀到 02-simulation-file-experience/ 对应维度
#
# 该会话对 /root/skills_of_plant_simulation 拥有 读 / 增 / 改 权限（acceptEdits 模式）
#
# 运行模式：
#   默认（交互式）：合并完后进 REPL，用户继续和 curator 对话
#     $ ./sync-and-curate.sh
#   测试（非交互）：合并完后 openclaude 加 -p，跑完直接打印总结退出
#     $ PRINT_MODE=1 ./sync-and-curate.sh
#     或
#     $ ./sync-and-curate.sh --print
#
#   AUTO_APPLY（默认关）：curator 是否直接 Edit 02-simulation-file-experience/，还是只产 patch 等复核
#     默认（关）：保留审计链——patch 落 agents/curator-reports/patches/，等用户/verification 复核
#       $ ./sync-and-curate.sh
#     开：curator 直接 Edit 02（仍 append-only + 老 entry 不改 + bump frontmatter，详见 agent 铁律❷）
#       $ AUTO_APPLY=1 ./sync-and-curate.sh
#       $ ./sync-and-curate.sh --auto-apply
#     可与 PRINT_MODE 组合：
#       $ PRINT_MODE=1 AUTO_APPLY=1 ./sync-and-curate.sh
#       $ ./sync-and-curate.sh --auto-apply --print

set -euo pipefail

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
  # 用 grep 看末尾是否有 \r；不依赖 file 命令（部分环境没装）
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
  # 取主版本号 (例如 2.39.0 -> 2)
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
EXPECTED_BRANCH="fea/optimizer"
SOURCE_BRANCH="fea/Learning"
AGENT="plant-simulation-experience-curator"
SESSION_NAME="curator-sync-$(date +%Y%m%d-%H%M%S)"

cd "$REPO_DIR"

echo "==> 1/4 校验当前分支"
current_branch=$(git rev-parse --abbrev-ref HEAD)
if [ "$current_branch" != "$EXPECTED_BRANCH" ]; then
  echo "❌ 当前分支是 '$current_branch'，必须在 '$EXPECTED_BRANCH' 上。"
  echo "   请先执行: git checkout $EXPECTED_BRANCH"
  exit 1
fi
echo "✅ 当前分支: $current_branch"

echo "==> 2/4 fetch + 必要时 pull"
git fetch origin --prune --prune-tags

if git rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1; then
  upstream="origin/$EXPECTED_BRANCH"
  if git status -sb | grep -q "^## $upstream\.\.HEAD"; then
    echo "🔄 本地落后 $upstream，执行 git pull --ff-only"
    git pull --ff-only origin "$EXPECTED_BRANCH"
  elif git status -sb | grep -q "behind"; then
    echo "🔄 本地落后远端，执行 git pull --ff-only"
    git pull --ff-only
  else
    echo "✅ $EXPECTED_BRANCH 已与远端同步"
  fi
else
  echo "⚠️ 当前分支未设置上游，自动 git pull origin $EXPECTED_BRANCH"
  git pull --ff-only origin "$EXPECTED_BRANCH"
fi

echo "==> 3/4 合并 $SOURCE_BRANCH -> $EXPECTED_BRANCH"
git fetch origin "$SOURCE_BRANCH"
merge_msg="merge $SOURCE_BRANCH into $EXPECTED_BRANCH @ $(date +%Y-%m-%d)"
if git merge --no-ff -m "$merge_msg" "origin/$SOURCE_BRANCH"; then
  echo "✅ 合并完成"
else
  echo "❌ 合并冲突，请手动解决后再继续"
  echo "   解决后执行: git add -A && git commit --no-edit"
  exit 2
fi

echo "==> 4/4 启动 openclaude 会话 -> $AGENT"

# AUTO_APPLY 开关：AUTO_APPLY=1 或带 --auto-apply 时，curator 直接 Edit 02-simulation-file-experience/
# 默认 0：curator 只产出 patch + 报告，等用户/verification 复核（保留审计链）
AUTO_APPLY_DIRECTIVE=""
if [ "${AUTO_APPLY:-0}" = "1" ] || { [ $# -gt 0 ] && [ "$1" = "--auto-apply" ]; } \
   || { [ $# -gt 0 ] && [ "$1" = "--print" ] && [ "${2:-}" = "--auto-apply" ]; } \
   || { [ $# -gt 1 ] && [ "$1" = "--auto-apply" ] && [ "$2" = "--print" ]; }; then
  AUTO_APPLY=1
  echo "⚡ AUTO_APPLY 开启：curator 将直接 Edit 02-simulation-file-experience/（仍 append-only + 不改老 entry）"
else
  AUTO_APPLY=0
  echo "🔒 AUTO_APPLY 关闭：curator 仅产出 patch + 报告，等复核"
fi

PROMPT=$(cat <<EOF
请以 plant-simulation-experience-curator 的身份执行以下沉淀任务：

1) 阅读 $REPO_DIR/03-agent-memory/plant-simulation-expert-memory/ 下所有 *.md（session summary），
   重点识别 plant-simulation-expert 在会话中产出的可复用经验：
   - 新的 Quirk / 坑 / 软失败契约
   - 验证过的最佳实践 / 反模式
   - 跨 session 重复出现的模式
   - 已存在于 02 目录但需要 supersede / 补充的 entry

2) 按 $REPO_DIR/02-simulation-file-experience/CONTRIBUTING.md 的强约束沉淀：
   - 三区结构（YAML frontmatter / 主体 / 末尾的 ## 经验 Log）
   - 路径分配 5 条规则（领域 → 01-；桥 → 02-；工作流 → 03-；模型特定 → 04-；session 流水 → 05-）
   - entry 字段强制：症状 / 根因 / Workaround / tags / see also + 末尾反思
   - 03-workflow-playbook/ 下的新 entry 强制 per-entry file（详见 CONTRIBUTING §6）
   - 老 entry 不删不改；supersede 必须留指针

3) 工作目录与可写范围已限定在 $REPO_DIR 下。请按以下顺序产出：
   - 先在 agents/curator-reports/ 写一份本轮 curator 报告（INDEX + 单次报告）
   - 对 02-simulation-file-experience/ 的每处追加，输出候选 patch（diff 形态）
EOF
)

if [ "$AUTO_APPLY" = "1" ]; then
  PROMPT="$PROMPT"$(cat <<EOF

   - **本会话已开启 AUTO_APPLY**：你被授权直接 Edit 02-simulation-file-experience/ 对应文件的
     \`## 经验 Log\` 区末尾追加新 entry（仍须 append-only + 老 entry 不改 + bump frontmatter）。
     在报告里每条 direct-landed entry 旁标 ⚡ "direct-landed (AUTO_APPLY)" + 引用本 prompt 授权来源。
EOF
)
else
  PROMPT="$PROMPT"$(cat <<EOF

   - **本会话未开启 AUTO_APPLY**：不要直接 Edit 02 目录主体；patch 落到 agents/curator-reports/patches/ 即可。
     等用户或 verification agent 复核后再 Edit 落地。
EOF
)
fi

PROMPT="$PROMPT"$(cat <<EOF

4) 完成后请给出一段总结：本轮新沉淀 N 条 / supersede M 条 / 丢弃 K 条 + INDEX 增量行。
   如果走了 AUTO_APPLY，请额外说明 landed N 条（标 ⚡）/ 仍 pending M 条（标 🕐）。

权限说明：本会话已对 $REPO_DIR 授予读 / 增 / 改 权限（acceptEdits 模式）。Bash 可执行 git 操作与 grep 类只读命令。
EOF
)

# ---------------------------------------------------------------------------
# 5) PRINT_MODE 开关：PRINT_MODE=1 或带 --print 时走非交互模式（测试 / CI 友好）
# ---------------------------------------------------------------------------
PRINT_FLAG=""
if [ "${PRINT_MODE:-0}" = "1" ] || { [ $# -gt 0 ] && [ "$1" = "--print" ]; }; then
  PRINT_FLAG="-p"
  echo "ℹ️  PRINT_MODE 开启，将以非交互模式跑(openclaude -p)"
fi

# ---------------------------------------------------------------------------

exec openclaude \
  --agent "$AGENT" \
  --add-dir "$REPO_DIR" \
  --permission-mode "acceptEdits" \
  --name "$SESSION_NAME" \
  $PRINT_FLAG \
  "$PROMPT"
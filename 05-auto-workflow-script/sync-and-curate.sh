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

set -euo pipefail

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

3) 你的工作目录与可写范围已限定在 $REPO_DIR 下，请按以下顺序产出：
   - 先在 agents/curator-reports/ 写一份本轮 curator 报告（INDEX + 单次报告）
   - 对 02-simulation-file-experience/ 的每处追加，输出候选 patch（diff 形态）并等待人工/verification 复核
   - **不要**未经复核直接 Edit 02 目录主体；patch 落到 agents/curator-reports/ 即可

4) 完成后请给出一段总结：本轮新沉淀 N 条 / supersede M 条 / 丢弃 K 条 + INDEX 增量行。

权限说明：本会话已对 $REPO_DIR 授予读 / 增 / 改 权限（acceptEdits 模式）。Bash 可执行 git 操作与 grep 类只读命令。
EOF
)

exec openclaude \
  --agent "$AGENT" \
  --add-dir "$REPO_DIR" \
  --permission-mode "acceptEdits" \
  --name "$SESSION_NAME" \
  "$PROMPT"
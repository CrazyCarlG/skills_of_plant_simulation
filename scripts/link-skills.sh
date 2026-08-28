#!/usr/bin/env bash
# 把 skills/ 下的技能软链到用户技能目录 / Symlink skills into the user skills dir
#
# 默认目标目录（按查找顺序）：
#   1. $CLAUDE_SKILLS_DIR（环境变量覆盖）
#   2. $OPENCLAUDE_SKILLS_DIR（环境变量覆盖）
#   3. ~/.claude/skills/        —— Claude Code / OpenClaude 默认
#
# 用法：
#   bash scripts/link-skills.sh           # 默认链接
#   bash scripts/link-skills.sh --unlink  # 删除已建的符号链接
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_SRC="$REPO_ROOT/skills"

if [[ ! -d "$SKILLS_SRC" ]]; then
  echo "ERR: $SKILLS_SRC does not exist" >&2
  exit 1
fi

# 决定目标目录
pick_target() {
  if [[ -n "${CLAUDE_SKILLS_DIR:-}" ]]; then
    echo "$CLAUDE_SKILLS_DIR"
    return
  fi
  if [[ -n "${OPENCLAUDE_SKILLS_DIR:-}" ]]; then
    echo "$OPENCLAUDE_SKILLS_DIR"
    return
  fi
  echo "$HOME/.claude/skills"
}

TARGET_DIR="$(pick_target)"
mkdir -p "$TARGET_DIR"
echo "target dir: $TARGET_DIR"

mode="link"
if [[ "${1:-}" == "--unlink" ]]; then
  mode="unlink"
fi

unlink_one() {
  local name="$1"
  local target="$TARGET_DIR/$name"
  if [[ -L "$target" ]]; then
    rm "$target"
    echo "unlinked: $target"
  elif [[ -e "$target" ]]; then
    echo "skip (not a symlink, refusing to delete real dir): $target"
  else
    echo "skip (not present): $target"
  fi
}

link_one() {
  local name="$1"
  local src="$SKILLS_SRC/$name"
  local target="$TARGET_DIR/$name"
  if [[ ! -d "$src" ]]; then
    echo "skip (not a dir): $src"
    return
  fi
  if [[ -e "$target" || -L "$target" ]]; then
    echo "skip (exists): $target"
  else
    ln -s "$src" "$target"
    echo "linked: $target -> $src"
  fi
}

# skills/<name>/ —— 每个子目录是一个 skill
for skill_dir in "$SKILLS_SRC"/*/; do
  name="$(basename "$skill_dir")"
  if [[ "$mode" == "unlink" ]]; then
    unlink_one "$name"
  else
    link_one "$name"
  fi
done

echo
echo "done. mode=$mode, target=$TARGET_DIR"
echo "注意：技能通过仓库根相对路径引用知识库，请保持仓库目录结构完整。"

#!/usr/bin/env bash
# 把 skills/ 下的技能软链到用户技能目录 / Symlink skills into the user skills dir
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_SRC="$REPO_ROOT/skills"
SKILLS_DST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"

mkdir -p "$SKILLS_DST"

for skill_dir in "$SKILLS_SRC"/*/; do
  skill_name="$(basename "$skill_dir")"
  target="$SKILLS_DST/$skill_name"
  if [[ -e "$target" || -L "$target" ]]; then
    echo "skip (exists): $target"
  else
    ln -s "$skill_dir" "$target"
    echo "linked: $target -> $skill_dir"
  fi
done

echo "done. skills dir: $SKILLS_DST"
echo "注意：技能通过仓库根相对路径引用知识库，请保持仓库目录结构完整。"

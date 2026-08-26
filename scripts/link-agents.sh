#!/usr/bin/env bash
# 把 agents/ 下的 agent 定义软链到用户 agent 目录 / Symlink agents into the user agents dir
#
# 默认目标（按查找顺序，首个存在 / 可写的即用）：
#   1. $OPENCLAUDE_AGENTS_DIR（环境变量覆盖）
#   2. ~/.openclaude/agents/    —— OpenClaude 默认
#   3. ~/.claude/agents/        —— Claude Code 默认
#
# 用法：
#   bash scripts/link-agents.sh           # 默认链接
#   bash scripts/link-agents.sh --unlink  # 删除已建的符号链接
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENTS_SRC="$REPO_ROOT/agents"

if [[ ! -d "$AGENTS_SRC" ]]; then
  echo "ERR: $AGENTS_SRC does not exist" >&2
  exit 1
fi

# 决定目标目录
pick_target() {
  if [[ -n "${OPENCLAUDE_AGENTS_DIR:-}" ]]; then
    echo "$OPENCLAUDE_AGENTS_DIR"
    return
  fi
  if [[ -d "$HOME/.openclaude" ]]; then
    echo "$HOME/.openclaude/agents"
    return
  fi
  echo "$HOME/.claude/agents"
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
  local src="$AGENTS_SRC/$name"
  local target="$TARGET_DIR/$name"
  if [[ ! -f "$src" ]]; then
    echo "skip (not a file): $src"
    return
  fi
  if [[ -e "$target" || -L "$target" ]]; then
    echo "skip (exists): $target"
  else
    ln -s "$src" "$target"
    echo "linked: $target -> $src"
  fi
}

# agents/<name>.md —— 每个 .md 是一个 agent 定义
for agent_file in "$AGENTS_SRC"/*.md; do
  [[ "$(basename "$agent_file")" == "README.md" ]] && continue
  name="$(basename "$agent_file")"
  if [[ "$mode" == "unlink" ]]; then
    unlink_one "$name"
  else
    link_one "$name"
  fi
done

echo
echo "done. mode=$mode, target=$TARGET_DIR"
echo "注意：agent 内部通过仓库根相对路径引用知识库与 skills/，请保持仓库目录结构完整。"
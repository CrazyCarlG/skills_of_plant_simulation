#!/usr/bin/env bash
# 一键安装：把本仓库的 skills/ 和 agents/ 全部软链到用户级目录
# One-shot installer: symlink all skills + agents to user-level dirs
#
# 用法 / Usage
#   bash scripts/install.sh               # 安装
#   bash scripts/install.sh --unlink      # 卸载（删除符号链接）
#   bash scripts/install.sh --skills-only # 只装 skills
#   bash scripts/install.sh --agents-only # 只装 agents
#   bash scripts/install.sh --help        # 帮助
#
# 环境变量 / Env
#   OPENCLAUDE_SKILLS_DIR  覆盖 skills 目标目录（默认见 link-skills.sh）
#   OPENCLAUDE_AGENTS_DIR  覆盖 agents 目标目录（默认见 link-agents.sh）
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$REPO_ROOT/scripts"

# Initialize git submodules if any are declared but unpopulated.
# This makes a plain `git clone` + `bash scripts/install.sh` workflow
# work without requiring `git clone --recurse-submodules` up front.
if [[ -f "$REPO_ROOT/.gitmodules" ]]; then
  if ! git -C "$REPO_ROOT" submodule status --recursive >/dev/null 2>&1 \
     || git -C "$REPO_ROOT" submodule status --recursive 2>/dev/null \
        | grep -qE '^-'; then
    echo "--- initializing git submodules ---"
    git -C "$REPO_ROOT" submodule update --init --recursive
    echo
  fi
fi

do_skills=1
do_agents=1
mode="link"

usage() {
  sed -n '2,12p' "$0"
  exit 0
}

for arg in "$@"; do
  case "$arg" in
    --help|-h) usage ;;
    --unlink)  mode="unlink" ;;
    --skills-only) do_agents=0 ;;
    --agents-only) do_skills=0 ;;
    *) echo "unknown arg: $arg" >&2; exit 2 ;;
  esac
done

echo "=== skills_of_plant_simulation installer ==="
echo "repo : $REPO_ROOT"
echo "mode : $mode"
echo

if [[ "$do_skills" -eq 1 ]]; then
  echo "--- skills ---"
  if [[ "$mode" == "unlink" ]]; then
    bash "$SCRIPT_DIR/link-skills.sh" --unlink || true
  else
    bash "$SCRIPT_DIR/link-skills.sh"
  fi
  echo
fi

if [[ "$do_agents" -eq 1 ]]; then
  echo "--- agents ---"
  if [[ "$mode" == "unlink" ]]; then
    bash "$SCRIPT_DIR/link-agents.sh" --unlink || true
  else
    bash "$SCRIPT_DIR/link-agents.sh"
  fi
  echo
fi

echo "=== done ==="
echo "verify:"
echo "  ls -la \"${OPENCLAUDE_AGENTS_DIR:-~/.openclaude/agents}\" | grep plant-simulation"
echo "  ls -la \"${OPENCLAUDE_SKILLS_DIR:-~/.claude/skills}\" | grep local-simtalk"
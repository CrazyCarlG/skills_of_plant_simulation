#!/usr/bin/env bash
# 一键安装：把本仓库的 agents/ 和 skills/ 全部软链到 OpenClaude 用户级目录
# One-shot installer: symlink all agents + skills into the OpenClaude user-level dirs
#
# 用法 / Usage
#   bash scripts/install.sh                 # 链接 agents + skills
#   bash scripts/install.sh --unlink        # 卸载（只删符号链接，不动真实文件）
#   bash scripts/install.sh --skills-only   # 只装 skills
#   bash scripts/install.sh --agents-only   # 只装 agents
#   bash scripts/install.sh --help          # 帮助
#
# 环境变量 / Env
#   OPENCLAUDE_AGENTS_DIR  覆盖 agents 目标目录（默认 ~/.openclaude/agents）
#   OPENCLAUDE_SKILLS_DIR  覆盖 skills 目标目录（默认 ~/.openclaude/skills）
#
# 行为 / Behaviour
#   - 幂等：已正确链接的目标会被跳过
#   - 自愈：链接指向过期路径会自动重建
#   - 安全：非符号链接的真实文件/目录不会被删除
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENTS_SRC="$REPO_ROOT/agents"
SKILLS_SRC="$REPO_ROOT/skills"

# ---- arg parsing ----
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
    *) echo "ERR: unknown arg: $arg" >&2; exit 2 ;;
  esac
done

# ---- target dir resolution ----
# Priority: env var > ~/.openclaude/* > ~/.claude/*
pick_target() {
  local env_name="$1" subdir="$2"
  local env_val="${!env_name:-}"
  if [[ -n "$env_val" ]]; then
    echo "$env_val"; return
  fi
  if [[ -d "$HOME/.openclaude" ]]; then
    echo "$HOME/.openclaude/$subdir"; return
  fi
  if [[ -d "$HOME/.claude" ]]; then
    echo "$HOME/.claude/$subdir"; return
  fi
  # 都没建过 —— 默认放 openclaude 下，mkdir -p 会自动创建
  echo "$HOME/.openclaude/$subdir"
}

AGENTS_DST="$(pick_target OPENCLAUDE_AGENTS_DIR agents)"
SKILLS_DST="$(pick_target OPENCLAUDE_SKILLS_DIR skills)"

# ---- link / unlink helpers ----
# 删除一个符号链接：必须是符号链接，绝不碰真实文件/目录
safe_remove_symlink() {
  local target="$1"
  if [[ -L "$target" ]]; then
    rm -- "$target"
    return 0
  elif [[ -e "$target" ]]; then
    echo "skip (not a symlink, refusing to delete): $target" >&2
    return 1
  fi
  return 0
}

# 在目标处建立指向 src 的链接；若现有链接指向不同位置则先重建
link_into() {
  local src="$1" target="$2"
  if [[ -L "$target" ]]; then
    local cur; cur="$(readlink "$target" || true)"
    # 规范化：去掉尾部 / 后再比较，避免 "skills/x" vs "skills/x/" 误判为不同
    local cur_n="${cur%/}" src_n="${src%/}"
    if [[ "$cur_n" == "$src_n" ]]; then
      echo "ok      : $target"
      return 0
    fi
    echo "relink  : $target  (was -> $cur)"
    rm -- "$target"
  elif [[ -e "$target" ]]; then
    echo "skip (real path blocks link): $target" >&2
    return 1
  fi
  ln -s "$src" "$target"
  echo "linked  : $target -> $src"
}

unlink_into() {
  local src="$1" target="$2"
  if [[ -L "$target" ]]; then
    local cur; cur="$(readlink "$target" || true)"
    local cur_n="${cur%/}" src_n="${src%/}"
    if [[ "$cur_n" == "$src_n" ]]; then
      rm -- "$target"
      echo "unlinked: $target"
    else
      echo "skip (points elsewhere): $target -> $cur"
    fi
  elif [[ -e "$target" ]]; then
    echo "skip (not a symlink): $target" >&2
  else
    echo "skip (absent)   : $target"
  fi
}

# ---- agents ----
install_agents() {
  if [[ ! -d "$AGENTS_SRC" ]]; then
    echo "ERR: agents source not found: $AGENTS_SRC" >&2
    return 1
  fi
  mkdir -p "$AGENTS_DST"
  echo "agents dir: $AGENTS_SRC  ->  $AGENTS_DST"
  echo

  local linked=0 skipped=0
  shopt -s nullglob
  for src in "$AGENTS_SRC"/*.md; do
    local name; name="$(basename "$src")"
    [[ "$name" == "README.md" ]] && continue
    local target="$AGENTS_DST/$name"
    if [[ "$mode" == "unlink" ]]; then
      if unlink_into "$src" "$target"; then linked=$((linked + 1)); else skipped=$((skipped + 1)); fi
    else
      if link_into "$src" "$target"; then linked=$((linked + 1)); else skipped=$((skipped + 1)); fi
    fi
  done
  shopt -u nullglob

  echo
  echo "agents: $linked processed, $skipped skipped"
}

# ---- skills ----
install_skills() {
  if [[ ! -d "$SKILLS_SRC" ]]; then
    echo "ERR: skills source not found: $SKILLS_SRC" >&2
    return 1
  fi
  mkdir -p "$SKILLS_DST"
  echo "skills dir: $SKILLS_SRC  ->  $SKILLS_DST"
  echo

  local linked=0 skipped=0
  shopt -s nullglob
  for src in "$SKILLS_SRC"/*/; do
    [[ -d "$src" ]] || continue
    local name; name="$(basename "$src")"
    # 每个 skill 必须含 SKILL.md；否则不算合法 skill，跳过
    if [[ ! -f "$src/SKILL.md" ]]; then
      echo "skip (no SKILL.md): $src" >&2
      skipped=$((skipped + 1))
      continue
    fi
    local target="$SKILLS_DST/$name"
    if [[ "$mode" == "unlink" ]]; then
      if unlink_into "$src" "$target"; then linked=$((linked + 1)); else skipped=$((skipped + 1)); fi
    else
      if link_into "$src" "$target"; then linked=$((linked + 1)); else skipped=$((skipped + 1)); fi
    fi
  done
  shopt -u nullglob

  echo
  echo "skills: $linked processed, $skipped skipped"
}

# ---- main ----
echo "=== skills_of_plant_simulation installer ==="
echo "repo : $REPO_ROOT"
echo "mode : $mode"
echo
[[ "$do_agents" -eq 1 ]] && { echo "--- agents ---"; install_agents; echo; }
[[ "$do_skills" -eq 1 ]] && { echo "--- skills ---"; install_skills; echo; }

echo "=== done ==="
echo "verify:"
echo "  ls -la \"$AGENTS_DST\""
echo "  ls -la \"$SKILLS_DST\""
echo
echo "注意：agent 与 skill 内部多通过仓库根相对路径引用知识库与 skills/，请保持仓库目录结构完整。"
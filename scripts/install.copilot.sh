#!/usr/bin/env bash
# Copilot metadata block (YAML-like comments to help GitHub Copilot understand intent)
# ---
# name: install.copilot.sh
# description: "Copilot-friendly installer: symlink skills/ and agents/ into user OpenClaude/Claude dirs. Mirrors scripts/install.sh behavior with richer metadata and examples to help Copilot generate suggestions."
# inputs:
#   - args: [--unlink, --skills-only, --agents-only, --help]
# env:
#   - OPENCLAUDE_SKILLS_DIR: overrides skills target directory
#   - OPENCLAUDE_AGENTS_DIR: overrides agents target directory
# outputs:
#   - creates symlinks in: ~/.openclaude/skills or ~/.claude/skills and ~/.openclaude/agents or ~/.claude/agents
# examples:
#   - bash scripts/install.copilot.sh
#   - bash scripts/install.copilot.sh --unlink
# ---

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPT_DIR="$REPO_ROOT/scripts"

# Initialize git submodules if present but unpopulated.
# This mirrors the behavior of the original installer and makes
# a fresh `git clone` + installer flow work without requiring
# `--recurse-submodules` up front.
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
  sed -n '2,16p' "$0" || true
  echo
  echo "Usage: $0 [--unlink|--skills-only|--agents-only|--help]"
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

echo "=== skills_of_plant_simulation Copilot-friendly installer ==="
echo "repo : $REPO_ROOT"
echo "mode : $mode"
echo

# Pick target for skills. Copilot-friendly note: prefer OpenClaude paths when available.
pick_skills_target() {
  if [[ -n "${CLAUDE_SKILLS_DIR:-}" ]]; then
    echo "$CLAUDE_SKILLS_DIR"
    return
  fi
  if [[ -n "${OPENCLAUDE_SKILLS_DIR:-}" ]]; then
    echo "$OPENCLAUDE_SKILLS_DIR"
    return
  fi
  if [[ -d "$HOME/.openclaude" ]]; then
    echo "$HOME/.openclaude/skills"
    return
  fi
  echo "$HOME/.claude/skills"
}

# Pick target for agents (prefer OpenClaude then ~/.claude)
pick_agents_target() {
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

SKILLS_SRC="$REPO_ROOT/skills"
AGENTS_SRC="$REPO_ROOT/agents"

if [[ "$do_skills" -eq 1 ]]; then
  echo "--- skills ---"
  TARGET_DIR="$(pick_skills_target)"
  mkdir -p "$TARGET_DIR"
  echo "target dir: $TARGET_DIR"

  if [[ "$mode" == "unlink" ]]; then
    for skill_dir in "$SKILLS_SRC"/*/; do
      name="$(basename "$skill_dir")"
      target="$TARGET_DIR/$name"
      if [[ -L "$target" ]]; then
        rm "$target"
        echo "unlinked: $target"
      elif [[ -e "$target" ]]; then
        echo "skip (not a symlink, refusing to delete real dir): $target"
      else
        echo "skip (not present): $target"
      fi
    done
  else
    for skill_dir in "$SKILLS_SRC"/*/; do
      name="$(basename "$skill_dir")"
      src="$SKILLS_SRC/$name"
      target="$TARGET_DIR/$name"
      if [[ ! -d "$src" ]]; then
        echo "skip (not a dir): $src"
        continue
      fi
      if [[ -e "$target" || -L "$target" ]]; then
        echo "skip (exists): $target"
      else
        ln -s "$src" "$target"
        echo "linked: $target -> $src"
      fi
    done
  fi
  echo
fi

if [[ "$do_agents" -eq 1 ]]; then
  echo "--- agents ---"
  TARGET_DIR="$(pick_agents_target)"
  mkdir -p "$TARGET_DIR"
  echo "target dir: $TARGET_DIR"

  if [[ "$mode" == "unlink" ]]; then
    for agent_file in "$AGENTS_SRC"/*.md; do
      [[ "$(basename "$agent_file")" == "README.md" ]] && continue
      name="$(basename "$agent_file")"
      target="$TARGET_DIR/$name"
      if [[ -L "$target" ]]; then
        rm "$target"
        echo "unlinked: $target"
      elif [[ -e "$target" ]]; then
        echo "skip (not a symlink, refusing to delete real file): $target"
      else
        echo "skip (not present): $target"
      fi
    done
  else
    for agent_file in "$AGENTS_SRC"/*.md; do
      [[ "$(basename "$agent_file")" == "README.md" ]] && continue
      name="$(basename "$agent_file")"
      src="$AGENTS_SRC/$name"
      target="$TARGET_DIR/$name"
      if [[ ! -f "$src" ]]; then
        echo "skip (not a file): $src"
        continue
      fi
      if [[ -e "$target" || -L "$target" ]]; then
        echo "skip (exists): $target"
      else
        ln -s "$src" "$target"
        echo "linked: $target -> $src"
      fi
    done
  fi
  echo
fi

echo "=== done ==="
echo "verify:"
echo "  ls -la \"${OPENCLAUDE_AGENTS_DIR:-~/.openclaude/agents}\" | grep plant-simulation"
echo "  ls -la \"${OPENCLAUDE_SKILLS_DIR:-~/.openclaude/skills}\" | grep local-simtalk"

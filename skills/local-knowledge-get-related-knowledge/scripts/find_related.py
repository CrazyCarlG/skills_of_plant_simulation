#!/usr/bin/env python3
"""find_related.py — search the local Plant Simulation knowledge base.

Stateless, read-only. Scans ``01-plantsimulation-knowledge/01-plant-simulation-help/``
for files (``.md`` and ``.txtx``) that match a free-text query and prints a ranked
list with snippets.

Usage:
    python3 scripts/find_related.py --query "Buffer attributes"
    python3 scripts/find_related.py --query "if statement" --kind simtalk --top 5
    python3 scripts/find_related.py --query "Worker" --json

Exit codes:
    0  success, at least one match
    1  bad arguments (missing --query, unknown --kind, etc.)
    2  knowledge base root not found
    3  no matches (caller may broaden query or drop --kind)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Iterable

# ---- defaults ----------------------------------------------------------------

DEFAULT_ROOT = Path("01-plantsimulation-knowledge/01-plant-simulation-help").resolve()
SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT_CANDIDATE = SCRIPTS_DIR.parents[2]  # skills/<name>/scripts -> repo root

KINDS = {
    "objects": "objects/",
    "simtalk": "simtalk/",
    "step-by-step": "step-by-step/",
    "communication-interface": "communication-interface/",
    "getting-to-know": "getting-to-know-plant-simulation/",
}

# Files treated as pure indexes (no body scoring, only path/filename boost).
INDEX_FILES = {"readme.md"}

# Cap per-file body contribution so a single very long file cannot dominate.
MAX_BODY_HITS = 20
# Cap snippet width.
SNIPPET_WIDTH = 200
# Max file size to scan (skip body if larger, fall back to path+filename).
MAX_BODY_BYTES = 1_500_000  # ~1.5 MB
# Token length filter.
MIN_TOKEN_LEN = 2


# ---- tokenization -------------------------------------------------------------

_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]+")


def tokenize(text: str) -> list[str]:
    """Lowercase + split into alphanumeric / CJK runs."""
    return [t.lower() for t in _TOKEN_RE.findall(text) if len(t) >= MIN_TOKEN_LEN]


# ---- scoring -----------------------------------------------------------------

def filename_score(basename: str, tokens: list[str]) -> int:
    """Count how many tokens appear as substrings in the basename."""
    name = basename.lower()
    return sum(1 for tok in tokens if tok in name)


def path_score(rel_parts: list[str], tokens: list[str]) -> int:
    """Count how many tokens appear in any path segment (excluding basename)."""
    score = 0
    for seg in rel_parts[:-1]:
        seg_l = seg.lower()
        for tok in tokens:
            if tok in seg_l:
                score += 1
    return score


def body_score(content: str, tokens: list[str]) -> tuple[int, list[int]]:
    """Count total token occurrences in body; return (hits, line_indices)."""
    body_l = content.lower()
    total = 0
    for tok in tokens:
        total += body_l.count(tok)
    total = min(total, MAX_BODY_HITS)

    # find first line that contains any token (for snippet)
    line_idxs: list[int] = []
    for i, line in enumerate(content.splitlines()):
        line_l = line.lower()
        if any(tok in line_l for tok in tokens):
            line_idxs.append(i)
            if len(line_idxs) >= 3:
                break
    return total, line_idxs


def make_snippet(content: str, line_idxs: list[int], tokens: list[str]) -> str:
    """Return a short excerpt around the first matching line."""
    if not line_idxs:
        return ""
    lines = content.splitlines()
    i = line_idxs[0]
    start = max(0, i - 1)
    end = min(len(lines), i + 2)
    block = " ".join(lines[start:end]).strip()
    block = re.sub(r"\s+", " ", block)
    if len(block) > SNIPPET_WIDTH:
        block = block[: SNIPPET_WIDTH - 1] + "…"
    # highlight first token (cheap)
    first = next((t for t in tokens if t in block.lower()), None)
    if first:
        idx = block.lower().find(first)
        if idx >= 0:
            block = block[:idx] + "<<" + block[idx : idx + len(first)] + ">>" + block[idx + len(first) :]
    return block


# ---- walker ------------------------------------------------------------------

def iter_kb_files(root: Path, kind_filter: str | None) -> Iterable[Path]:
    """Yield .md / .txtx files under root, optionally restricted to a kind prefix."""
    if not root.is_dir():
        return
    if kind_filter and kind_filter != "any":
        prefix = KINDS.get(kind_filter)
        if prefix is None:
            return
        anchor = root / prefix
        if not anchor.is_dir():
            return
        for p in anchor.rglob("*"):
            if p.is_file() and p.suffix.lower() in (".md", ".txtx"):
                yield p
        return
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in (".md", ".txtx"):
            yield p


# ---- ranking -----------------------------------------------------------------

def score_file(path: Path, root: Path, tokens: list[str]) -> dict | None:
    rel = path.relative_to(root)
    rel_parts = list(rel.parts)
    basename = rel_parts[-1]

    f_score = filename_score(basename, tokens)
    p_score = path_score(rel_parts, tokens)

    is_index = basename.lower() in INDEX_FILES

    b_score = 0
    line_idxs: list[int] = []
    snippet = ""
    if not is_index:
        try:
            size = path.stat().st_size
        except OSError:
            size = 0
        if size <= MAX_BODY_BYTES:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                content = ""
            b_score, line_idxs = body_score(content, tokens)
            snippet = make_snippet(content, line_idxs, tokens)
        else:
            b_score = MAX_BODY_HITS // 2  # soft credit so giant files still rank

    total = f_score * 5 + p_score * 3 + b_score
    if total <= 0:
        return None

    # Breadcrumb: replace root prefix marker for human display.
    breadcrumb_parts = rel_parts[:-1]
    breadcrumb = " / ".join(breadcrumb_parts) if breadcrumb_parts else "(root)"

    return {
        "rank": 0,  # filled later
        "score": total,
        "filename_score": f_score,
        "path_score": p_score,
        "body_score": b_score,
        "is_index": is_index,
        "rel_path": str(rel).replace("\\", "/"),
        "breadcrumb": breadcrumb,
        "basename": basename,
        "snippet": snippet,
    }


# ---- main --------------------------------------------------------------------

def resolve_root(arg_root: str | None) -> Path:
    if arg_root:
        p = Path(arg_root).expanduser().resolve()
        return p
    # try sibling of repo root, then CWD
    candidate = REPO_ROOT_CANDIDATE / "01-plantsimulation-knowledge" / "01-plant-simulation-help"
    if candidate.is_dir():
        return candidate
    cwd_candidate = (Path.cwd() / "01-plantsimulation-knowledge" / "01-plant-simulation-help").resolve()
    return cwd_candidate


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="find_related.py",
        description="Search the local Plant Simulation knowledge base.",
    )
    p.add_argument("--query", required=True, help="free-text search query")
    p.add_argument(
        "--kind",
        choices=sorted(list(KINDS.keys()) + ["any"]),
        default="any",
        help="restrict search to a knowledge-base section",
    )
    p.add_argument("--top", type=int, default=10, help="max results (default 10)")
    p.add_argument("--root", default=None, help="override knowledge-base root path")
    p.add_argument("--json", action="store_true", help="emit JSON instead of a table")
    p.add_argument(
        "--include-index",
        action="store_true",
        help="include README.md index files (default: included but de-weighted)",
    )
    return p.parse_args(argv)


def _force_utf8_stdio() -> None:
    """Reconfigure stdout/stderr to UTF-8 so snippets with CJK / arrows print safely.

    On Windows the default code page (cp1252) crashes on characters like ``→``.
    Reconfigure is a no-op on streams that already support it.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def main(argv: list[str]) -> int:
    _force_utf8_stdio()
    args = parse_args(argv)
    if args.top <= 0:
        print("ERR: --top must be >= 1", file=sys.stderr)
        return 1

    tokens = tokenize(args.query)
    if not tokens:
        print("ERR: --query has no tokens of length >= 2", file=sys.stderr)
        return 1

    root = resolve_root(args.root)
    if not root.is_dir():
        print(f"ERR: knowledge base root not found: {root}", file=sys.stderr)
        print("hint: pass --root <absolute-path>", file=sys.stderr)
        return 2

    results: list[dict] = []
    for path in iter_kb_files(root, args.kind):
        # de-weight (but still allow) README.md unless --include-index
        basename = path.name.lower()
        is_index = basename in INDEX_FILES
        if is_index and not args.include_index:
            # still score it but cap body weight (already done in score_file)
            pass
        rec = score_file(path, root, tokens)
        if rec is None:
            continue
        results.append(rec)

    if not results:
        if args.json:
            print(json.dumps({"query": args.query, "tokens": tokens, "results": []}, ensure_ascii=False, indent=2))
        else:
            print(f"no matches for query: {args.query!r}")
            print("hint: drop --kind, broaden --query, or pass --include-index")
        return 3

    # sort: higher score first; indexes sink slightly so concrete docs surface
    results.sort(
        key=lambda r: (r["score"] - (3 if r["is_index"] and not args.include_index else 0)),
        reverse=True,
    )
    top = results[: args.top]
    for i, r in enumerate(top, start=1):
        r["rank"] = i

    if args.json:
        out = {
            "query": args.query,
            "tokens": tokens,
            "kind": args.kind,
            "root": str(root),
            "results": top,
        }
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0

    # human-readable table
    print(f"query: {args.query}")
    print(f"tokens: {', '.join(tokens)}")
    print(f"kind:   {args.kind}")
    print(f"root:   {root}")
    print(f"hits:   {len(results)} (showing top {len(top)})")
    print()
    for r in top:
        flag = "[INDEX]" if r["is_index"] else "       "
        print(f"#{r['rank']:<2} score={r['score']:<3} {flag} {r['rel_path']}")
        print(f"        breadcrumb: {r['breadcrumb']}")
        print(
            f"        breakdown:  filename={r['filename_score']} "
            f"path={r['path_score']} body={r['body_score']}"
        )
        if r["snippet"]:
            print(f"        snippet:    {r['snippet']}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
simtalk_string_utils.py — Build SimTalk RHS expressions from Python strings
without tripping the "no string escape sequences" trap.

Background
----------
Plant Simulation's SimTalk parser does NOT interpret escape sequences in
double-quoted strings. `\"`, `\\`, `\n` are literal 2-character sequences —
the backslash is preserved as data, NOT treated as a continuation or escape.
This means the obvious Python-side approach

    quote(s) = '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'

produces SimTalk source like

    "... regex_replace(message, \"\\|\\|END\\|\|\", \"\") ..."

which SimTalk sees as

    "... regex_replace(message, \"\\|\\|END\\|\|\", \"\") ..."

— the backslashes survive verbatim, the `"` is treated as a string-close,
and everything downstream is broken.

The fix is to assemble the RHS expression as a chain of `chr(N)` calls for
every special character, so SimTalk never sees a literal `"` / `\` / `|`
inside the string content — only inside the surrounding `chr()` call
syntax, which is its own well-defined grammar.

Public API
----------
    encode_for_simtalk(s: str) -> str
        Convert a Python string into a SimTalk expression that evaluates to
        the same string. e.g. encode_for_simtalk('hello "world"') returns
        '"hello " + chr(34) + "world" + chr(34)'.

    scan_note_lines(lines: list[str]) -> list[tuple[int, int, int, str]]
        Return [(line_idx, col_idx, codepoint, hex)] for every forbidden
        character found in `lines`. An empty list means the NOTE is safe
        to feed into encode_for_simtalk. Forbids:
          - chr(92)  (backslash)         — see encode_for_simtalk rationale
          - chr(124) (pipe)              — ||...|| is a SimTalk raw-string
                                            delimiter and gets stripped
          - chr(0)..chr(31) (control)    — except chr(10) (LF)
          - chr(0x200B), chr(0x00A0),
            chr(0xFEFF), chr(0x2028),
            chr(0x2029)                  — invisible Unicode that confuses
                                            the parser / corrupts round-trips
          - chr(0x80)..chr(0xFF)         — Latin-1 range, ONLY a warning
                                            (Chinese / em-dash / etc. above
                                            U+00FF are safe — they're
                                            emitted as chr() too, just no
                                            string-literal shortcut exists)

    chunk_lines(lines: list[str], chunk_size: int = 28) -> list[list[str]]
        Split a list of NOTE lines into roughly-equal chunks for the
        chunked-write pattern (Pitfall P-3). chunk_size default 28 keeps
        each chunk's encoded RHS below ~2 KB even with Chinese/em-dash
        characters expanding via chr().
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# encode_for_simtalk
# ---------------------------------------------------------------------------

# Characters that SimTalk handles cleanly inside `"..."` string literals.
# Anything outside this set must go through chr() to avoid the
# no-escape-sequences trap (SimTalk parser treats `\"`, `\\` as literal).
_SAFE_ASCII = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " !#$%&'()*+,-./:;<=>?@[]^_`{}~"
    "\t"  # tab — handled as chr(9) for safety in some shells
)


def _is_safe_in_simtalk_string_literal(ch: str) -> bool:
    """Return True if ch can sit inside a `"..."` literal without breaking
    SimTalk. Conservative — Chinese / em-dash / etc. are NOT safe (they
    fall through to the chr() path) even though they aren't themselves
    troublesome; this keeps the RHS ASCII-clean and easy to debug."""
    if ch in _SAFE_ASCII:
        return True
    return False


def encode_for_simtalk(s: str) -> str:
    """Convert a Python string into a SimTalk expression that evaluates to
    the same string. SimTalk has no string-escape sequences, so every
    special character must be emitted as chr(N) and concatenated with +.

    Consecutive safe ASCII chars are batched into a single "..." literal
    to keep the RHS compact (e.g. "hello" rather than "h" + "e" + "l"...).

    Examples:
        encode_for_simtalk("hello") -> '"hello"'
        encode_for_simtalk('a"b')   -> '"a" + chr(34) + "b"'
        encode_for_simtalk("中")     -> 'chr(20013)'
        encode_for_simtalk("a\\nb") -> '"a" + chr(92) + "nb"'
        encode_for_simtalk("")      -> '""'
    """
    if not s:
        return '""'
    parts: list[str] = []
    safe_run: list[str] = []
    safe_run_append = safe_run.append

    def flush_safe():
        if safe_run:
            parts.append('"' + "".join(safe_run) + '"')
            safe_run.clear()

    for ch in s:
        code = ord(ch)
        if ch == '"':
            flush_safe()
            parts.append("chr(34)")
        elif ch == "\\":
            flush_safe()
            parts.append("chr(92)")
        elif ch == "|":
            flush_safe()
            parts.append("chr(124)")
        elif ch == "\n":
            flush_safe()
            parts.append("chr(10)")
        elif ch == "\r":
            flush_safe()
            parts.append("chr(13)")
        elif ch == "\t":
            flush_safe()
            parts.append("chr(9)")
        elif _is_safe_in_simtalk_string_literal(ch):
            safe_run_append(ch)
        else:
            # any other non-ASCII (Chinese, em-dash, etc.) → chr()
            flush_safe()
            parts.append("chr(" + str(code) + ")")
    flush_safe()
    if not parts:
        return '""'
    return " + ".join(parts)


# ---------------------------------------------------------------------------
# scan_note_lines
# ---------------------------------------------------------------------------

# (codepoint, label) pairs. chr(10) is excluded — newlines are normal.
_FORBIDDEN_CODEPOINTS: dict[int, str] = {
    0x200B: "zero-width space (ZWSP)",
    0x00A0: "non-breaking space (NBSP)",
    0xFEFF: "byte-order mark (BOM)",
    0x2028: "line separator",
    0x2029: "paragraph separator",
}


def scan_note_lines(lines: list[str]) -> list[tuple[int, int, int, str]]:
    """Return a list of (line_idx, col_idx, codepoint, hex) for every
    forbidden character in `lines`. Empty list means the NOTE is safe.

    Latin-1 range (0x80..0xFF) is included as a *warning* — it's not a
    hard error (the encoder will route those chars through chr() anyway),
    but Chinese / em-dash / etc. typically sit ABOVE 0xFF, so anything
    in 0x80..0xFF is usually a copy-paste accident from a Latin-1 source.
    """
    findings: list[tuple[int, int, int, str]] = []
    for i, line in enumerate(lines):
        for j, ch in enumerate(line):
            code = ord(ch)
            if code == ord("\\"):
                findings.append((i, j, code, hex(code)))
            elif code == ord("|"):
                findings.append((i, j, code, hex(code)))
            elif code < 32 and code != 10:
                # control char (not LF)
                findings.append((i, j, code, hex(code)))
            elif code in _FORBIDDEN_CODEPOINTS:
                findings.append((i, j, code, hex(code)))
            elif 0x80 <= code <= 0xFF:
                # warning, not blocker — caller can decide to ignore
                findings.append((i, j, code, hex(code)))
    return findings


# ---------------------------------------------------------------------------
# chunk_lines
# ---------------------------------------------------------------------------


def chunk_lines(lines: list[str], chunk_size: int = 28) -> list[list[str]]:
    """Split `lines` into chunks of at most `chunk_size` lines each.
    chunk_size=28 keeps the encoded RHS of each chunk under ~2 KB even
    for Chinese-heavy NOTE blocks (Pitfall P-3)."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1, got " + str(chunk_size))
    if not lines:
        return []
    return [lines[i : i + chunk_size] for i in range(0, len(lines), chunk_size)]


# ---------------------------------------------------------------------------
# estimate_payload_bytes — quick sanity check before compose
# ---------------------------------------------------------------------------


def estimate_payload_bytes(note_lines: list[str], before: str) -> int:
    """Roughly estimate the total RHS payload size for the prepend case.

    Counts: sum(ord(c) for c in each line) + chr(10) + chr(124)+ markers +
    the original body length. This is a LOWER bound — actual size depends
    on how many chr() calls replace bare-quote-able ASCII chars.

    Rule of thumb from the 2026-08-26 sessions:
      - 2 KB ≈ 30 lines of English NOTE, or ~25 lines of Chinese NOTE
      - Above 2 KB → MUST use chunked-write (Pitfall P-3)
    """
    note_chars = sum(len(line) for line in note_lines)
    # Conservative: assume all Chinese (>127) takes 8 bytes via "chr(20992)"
    # vs 1 byte for ASCII-in-literal.
    chinese_count = 0
    for line in note_lines:
        for ch in line:
            if ord(ch) > 127:
                chinese_count += 1
    # rough expansion factor
    note_bytes = note_chars + chinese_count * 6
    before_bytes = len(before)
    # + " + chr(10) + " × (note_lines + 1)
    sep_bytes = (len(note_lines) + 2) * 16
    return note_bytes + before_bytes + sep_bytes

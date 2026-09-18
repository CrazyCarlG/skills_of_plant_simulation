#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast-hit quality tests for the local-window-com-start-plant-simulation SKILL.md.

These tests verify that the SKILL.md is *agent-friendly*: an agent reading
it should be able to decide in seconds whether to invoke this skill, what
inputs it needs, and what to do when the request doesn't apply.

Coverage:
    quality-001  SKILL.md exists and has a frontmatter
    quality-002  description has >= 8 trigger phrases (enables agent hit-rate)
    quality-003  SKILL.md has a "decision tree" / 决策树 section
    quality-004  decision tree has at least 1 hit-signal and 1 no-hit signal
    quality-005  decision tree lists required inputs (.spp / .pslib / port)
    quality-006  all references/ paths cited in SKILL.md exist on disk
    quality-007  description mentions the skill is a prerequisite for downstream
                 local-simtalk-* skills

Run from the eval root:
    python -m pytest tests/test_skill_quality.py -v
"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_HERE = Path(__file__).resolve()
_ROOT = _HERE.parent.parent
sys.path.insert(0, str(_ROOT))


SKILL_MD = (
    _ROOT.parent.parent
    / "skills"
    / "local-window-com-start-plant-simulation"
    / "SKILL.md"
)
SKILL_DIR = SKILL_MD.parent


def _read() -> str:
    assert SKILL_MD.exists(), f"SKILL.md missing at {SKILL_MD}"
    return SKILL_MD.read_text(encoding="utf-8")


def _frontmatter(text: str) -> tuple[str, str]:
    """Return (frontmatter body, rest of file)."""
    if not text.startswith("---"):
        return "", text
    end = text.find("\n---", 3)
    if end == -1:
        return "", text
    return text[3:end].strip(), text[end + 4 :].lstrip("\n")


def _description(text: str) -> str:
    fm, _ = _frontmatter(text)
    for line in fm.splitlines():
        if line.startswith("description:"):
            return line[len("description:") :].strip()
    return ""


def _extract_quoted_phrases(s: str) -> list[str]:
    """Pull Chinese/English trigger phrases inside Chinese quotes or backticks."""
    return re.findall(r"[“\"](.*?)[”\"]|`([^`]+)`", s)


class TestSkillQuality(unittest.TestCase):
    """SKILL.md fast-hit coverage — does the doc help an agent decide in <30s?"""

    # ------------------------------------------------------------------
    # quality-001: file + frontmatter present
    # ------------------------------------------------------------------
    def test_quality_001_skill_md_present(self):
        self.assertTrue(
            SKILL_MD.exists(),
            f"SKILL.md missing at {SKILL_MD} — skill cannot be loaded by agents",
        )
        text = _read()
        self.assertTrue(text.startswith("---"), "SKILL.md missing frontmatter")
        fm, _ = _frontmatter(text)
        self.assertIn("name:", fm)
        self.assertIn("description:", fm)

    # ------------------------------------------------------------------
    # quality-002: description trigger density
    # ------------------------------------------------------------------
    def test_quality_002_description_trigger_density(self):
        desc = _description(_read())
        # Count distinct quoted phrases in description
        quoted = []
        for m in re.finditer(r"[“\"](.*?)[”\"]|`([^`]+)`", desc):
            quoted.append((m.group(1) or m.group(2)).strip())
        # Also count English verbs as triggers (load / boot / start / launch / etc.)
        verbs = re.findall(
            r"\b(load|boot|start|launch|prepare|spin|warm|init|open|bring|preload)\b",
            desc,
            flags=re.IGNORECASE,
        )
        total_triggers = len(set(quoted)) + len(set(v.lower() for v in verbs))
        # Empirical minimum: 8 distinct trigger phrases for agent hit-rate
        self.assertGreaterEqual(
            total_triggers,
            8,
            f"description trigger density too low: {total_triggers} distinct "
            f"phrases. Agents won't hit this skill reliably. Quoted={quoted} "
            f"Verbs={list(set(verbs))}",
        )

    # ------------------------------------------------------------------
    # quality-003: decision tree section exists
    # ------------------------------------------------------------------
    def test_quality_003_decision_tree_section_present(self):
        body = _read()
        # Match section header — accept either 中文 "决策树" or English "decision tree"
        self.assertTrue(
            re.search(r"^#{1,4}.*(决策树|decision tree)", body, re.MULTILINE | re.IGNORECASE),
            "SKILL.md missing 'decision tree' / '决策树' section — agents can't "
            "decide fast whether to invoke",
        )

    # ------------------------------------------------------------------
    # quality-004: decision tree has hit + no-hit bullets
    # ------------------------------------------------------------------
    def test_quality_004_decision_tree_has_hit_and_nohit(self):
        body = _read()
        # Find the decision tree section. Stop at the next level-2 (`## `)
        # heading so we capture sub-sections (`### ✅ / ❌ / ⚠️`) inside.
        m = re.search(
            r"^#{1,4}.*(决策树|decision tree)(.*?)(?=^## |\Z)",
            body,
            re.MULTILINE | re.IGNORECASE | re.DOTALL,
        )
        self.assertIsNotNone(m, "no decision tree section found")
        section = m.group(2)
        # Hit signals: prefixed by ✅ / 命中 / yes markers
        hit_markers = re.findall(r"(✅|命中|hit|yes|trigger)", section, re.IGNORECASE)
        # No-hit signals: prefixed by ❌ / 不命中 / don't / no markers
        nohit_markers = re.findall(
            r"(❌|不命中|don't|不要|no-hit|negative)",
            section,
            re.IGNORECASE,
        )
        self.assertGreaterEqual(
            len(hit_markers),
            1,
            f"decision tree missing hit-signal marker; section:\n{section[:300]!r}",
        )
        self.assertGreaterEqual(
            len(nohit_markers),
            1,
            f"decision tree missing no-hit marker (avoiding false-positive "
            f"invocations); section:\n{section[:300]!r}",
        )

    # ------------------------------------------------------------------
    # quality-005: required inputs are explicit
    # ------------------------------------------------------------------
    def test_quality_005_required_inputs_listed(self):
        body = _read()
        # All three: .spp, .pslib / SimtalkClaude, port
        for needle, label in [
            (r"\.spp", ".spp model path"),
            (r"(SimtalkClaude|\.pslib)", "SimtalkClaude.pslib path"),
            (r"(?:端口|port)", "TCP port"),
        ]:
            self.assertRegex(
                body,
                needle,
                f"SKILL.md decision tree missing required input hint: {label}",
            )

    # ------------------------------------------------------------------
    # quality-006: every cited reference/ path exists
    # ------------------------------------------------------------------
    def test_quality_006_references_exist_on_disk(self):
        body = _read()
        # Find markdown link targets of form [text](path) where path is relative
        links = re.findall(r"\[[^\]]*\]\((?!https?://|#)([^)]+)\)", body)
        missing: list[str] = []
        for link in links:
            # Strip anchor / query
            rel = link.split("#", 1)[0].split("?", 1)[0]
            if not rel:
                continue
            abs_path = (SKILL_DIR / rel).resolve()
            if not abs_path.exists():
                missing.append(f"{link} → {abs_path}")
        self.assertEqual(
            missing,
            [],
            f"SKILL.md references non-existent files: {missing}",
        )

    # ------------------------------------------------------------------
    # quality-007: prerequisite relationship is explicit
    # ------------------------------------------------------------------
    def test_quality_007_prerequisite_relationship_explicit(self):
        text = _read()
        # Either description or body must mention this skill is a
        # prerequisite for local-simtalk-* downstream skills.
        self.assertRegex(
            text,
            r"前置|prerequisite|下游|local-simtalk-",
            "SKILL.md must declare itself a prerequisite for downstream "
            "local-simtalk-* skills — otherwise agents won't know to invoke "
            "it before those skills",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
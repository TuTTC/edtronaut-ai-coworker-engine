"""
Emotional state analysis and update logic.
Analyzes user messages to determine how NPC emotional states should change.
"""

from __future__ import annotations

import re


class EmotionalAnalyzer:
    """Analyzes user messages to compute emotional-state deltas (trust, patience, engagement)."""

    # ── Positive signals ────────────────────────────────────────────────
    POSITIVE_PATTERNS: dict[str, list[str]] = {
        "data_driven": [
            r"\d+%", r"\bdata\b", r"\bmetrics\b", r"\bstatistics\b",
            r"\bresearch\b", r"\banalysis\b", r"\bevidence\b", r"\bbenchmark\b",
        ],
        "prepared": [
            r"i'?ve drafted", r"i'?ve prepared", r"i'?ve mapped",
            r"i'?ve analyzed", r"my proposal", r"my recommendation",
            r"i'?ve identified", r"i'?ve designed", r"i'?ve outlined",
        ],
        "strategic": [
            r"\bstrategic\b", r"\bframework\b", r"\balignment\b",
            r"\bbalance\b", r"\bpilot\b", r"\bphased\b", r"\broadmap\b",
            r"\bstakeholder\b", r"\bROI\b",
        ],
        "engaged": [
            r"what do you think", r"can i get your", r"i'd like your feedback",
            r"how would you", r"what's your perspective", r"your opinion",
        ],
    }

    # ── Negative signals ────────────────────────────────────────────────
    NEGATIVE_PATTERNS: dict[str, list[str]] = {
        "lazy": [
            r"tell me about", r"what does .+ do", r"can you explain everything",
            r"what is gucci", r"i don't know anything",
        ],
        "dismissive": [
            r"just do it", r"doesn't matter", r"\bwhatever\b",
            r"just roll out", r"one size fits all", r"skip",
        ],
        "unfocused": [
            r"by the way", r"off topic", r"random question",
            r"unrelated", r"anyway",
        ],
        "confused": [
            r"i'm not sure", r"i don't understand", r"\bconfused\b",
            r"help me", r"what should i do", r"i'm lost",
        ],
    }

    @classmethod
    def analyze_message(
        cls,
        message: str,
        persona_id: str,
    ) -> dict[str, float]:
        """Return emotional-state deltas for a user message."""
        msg = message.lower()
        deltas = {"trust": 0.0, "patience": 0.0, "engagement": 0.0}

        pos = cls._count_matches(cls.POSITIVE_PATTERNS, msg)
        neg = cls._count_matches(cls.NEGATIVE_PATTERNS, msg)

        # Message length heuristic
        word_count = len(message.split())
        if word_count > 50:
            pos += 1
        elif word_count < 10:
            neg += 0.5

        # Compute raw deltas
        if pos > neg:
            deltas["trust"] = min(0.15, pos * 0.05)
            deltas["patience"] = min(0.10, pos * 0.03)
            deltas["engagement"] = min(0.20, pos * 0.07)
        elif neg > pos:
            deltas["trust"] = max(-0.20, -neg * 0.07)
            deltas["patience"] = max(-0.30, -neg * 0.10)
            deltas["engagement"] = max(-0.15, -neg * 0.05)

        # Persona-specific modifiers
        if persona_id == "CEO" and neg > 0:
            # CEO is harsher on laziness
            deltas["patience"] *= 1.5
            deltas["trust"] *= 1.3
        elif persona_id == "CHRO" and neg > 0:
            # CHRO is more forgiving
            deltas["patience"] *= 0.7
            deltas["trust"] *= 0.8
        elif persona_id == "EB Regional Manager" and pos > 0:
            # RM appreciates practical questions
            deltas["engagement"] *= 1.2

        return deltas

    # ── Helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _count_matches(patterns: dict[str, list[str]], text: str) -> float:
        score = 0.0
        for _category, regexes in patterns.items():
            for pat in regexes:
                if re.search(pat, text):
                    score += 1
                    break          # one match per category is enough
        return score

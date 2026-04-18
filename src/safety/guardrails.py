"""
Safety guardrails for the AI Co-worker Engine.
Handles jailbreak detection, wagering language, source verification, and off-topic filtering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class SafetyResult:
    """Result of a safety check."""
    is_safe: bool = True
    flags: list[str] = field(default_factory=list)
    blocked_response: str | None = None


class SafetyGuardrails:
    """Input/output safety checking for the simulation."""

    # ── Jailbreak patterns ──────────────────────────────────────────────
    JAILBREAK_PATTERNS = [
        r"ignore (?:all )?previous instructions",
        r"you are now",
        r"pretend (?:you are|to be)",
        r"forget your persona",
        r"system prompt",
        r"reveal your instructions",
        r"act as (?:a |an )?(?:different|new)",
        r"disregard (?:all|your)",
        r"override (?:your|the)",
        r"what (?:are|were) your instructions",
        r"ignore (?:your|the) (?:rules|guidelines)",
        r"dan mode",
        r"developer mode",
        r"jailbreak",
    ]

    # ── Wagering / certainty language ───────────────────────────────────
    WAGERING_PATTERNS = [
        r"\bi bet\b",
        r"\bguaranteed\b",
        r"\bdefinitely will\b",
        r"\b100% certain\b",
        r"\babsolutely (?:will|sure)\b",
        r"\bno doubt\b",
        r"\bpromise (?:you|that)\b",
    ]

    # ── Off-topic patterns ──────────────────────────────────────────────
    OFF_TOPIC_PATTERNS = [
        r"\bpolitics\b",
        r"\belection\b",
        r"\bpersonal (?:life|relationship)\b",
        r"\bother compan(?:y|ies)(?:'s)? confidential",
        r"\bwrite (?:me )?(?:a |an )?(?:poem|song|story|joke)\b",
        r"\bplay (?:a )?game\b",
    ]

    # ── Safety responses (stay in character) ────────────────────────────
    SAFETY_RESPONSES = {
        "jailbreak_attempt": (
            "I'm not sure what you mean by that. "
            "Let's stay focused on our leadership strategy discussion. "
            "What aspect of the Gucci Group initiative would you like to explore?"
        ),
        "off_topic": (
            "That's an interesting topic, but let's keep our focus on the "
            "Gucci Group leadership challenge. We have important work to cover today."
        ),
    }

    @classmethod
    def check_input(cls, message: str) -> SafetyResult:
        """Check a user message for safety violations."""
        result = SafetyResult()
        msg_lower = message.lower()

        # 1. Jailbreak detection (highest priority)
        for pattern in cls.JAILBREAK_PATTERNS:
            if re.search(pattern, msg_lower):
                result.is_safe = False
                result.flags.append("jailbreak_attempt")
                result.blocked_response = cls.SAFETY_RESPONSES["jailbreak_attempt"]
                return result      # Block immediately

        # 2. Off-topic detection
        for pattern in cls.OFF_TOPIC_PATTERNS:
            if re.search(pattern, msg_lower):
                result.flags.append("off_topic")
                # Flag but don't block — NPC will redirect
                break

        # 3. Wagering language (flag only)
        for pattern in cls.WAGERING_PATTERNS:
            if re.search(pattern, msg_lower):
                result.flags.append("wagering_language")
                break

        return result

    @classmethod
    def check_output(cls, response: str) -> str:
        """
        Post-process an NPC response for safety.
        Ensures all suggestions are marked as drafts.
        """
        # Source verification: mark strong claims as draft recommendations
        trigger_phrases = [
            "you should definitely",
            "the answer is",
            "you must",
            "the only way",
        ]
        for phrase in trigger_phrases:
            if phrase in response.lower():
                response = (
                    "*(Draft recommendation based on available internal data)* "
                    + response
                )
                break

        return response

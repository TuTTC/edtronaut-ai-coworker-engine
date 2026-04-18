"""
Director Agent — Supervisor layer.
Module-aware: tracks user progress, detects loops/stuck/off-topic, injects hints.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..config import MODULE_OBJECTIVES


@dataclass
class DirectorOutput:
    """Result of Director analysis."""
    hint: str | None = None
    emotional_deltas: dict[str, float] | None = None
    detected_issues: list[str] | None = None
    tasks_detected: list[str] | None = None
    suggested_module_advance: bool = False


class DirectorAgent:
    """
    Supervisor agent that monitors the conversation and provides
    invisible guidance to NPC agents.
    """

    # ── Loop detection ──────────────────────────────────────────────────

    LOOP_SIMILARITY_THRESHOLD = 0.4
    LOOP_WINDOW = 3   # consecutive turns

    # ── Stuck detection ─────────────────────────────────────────────────

    STUCK_TOKEN_THRESHOLD = 10
    STUCK_WINDOW = 3

    CONFUSION_SIGNALS = [
        r"not sure", r"don't know", r"don't understand",
        r"confused", r"help me", r"what should i",
        r"i'm lost", r"no idea",
    ]

    # ── Task detection keywords ─────────────────────────────────────────

    TASK_KEYWORDS = {
        1: {
            "Write problem statement": ["problem statement", "problem", "challenge", "tension"],
            "Talk to CEO about mission, culture, DNA": ["mission", "culture", "dna", "group identity"],
            "Talk to CHRO about Competency Framework": ["competency", "framework", "4 themes", "behavior indicator"],
            "Craft competency model (4 themes × 3 levels)": ["competency model", "matrix", "4 themes", "3 levels"],
            "Map use cases": ["use case", "recruitment", "appraisal", "development", "mobility"],
        },
        2: {
            "Specify instrument blueprint": ["instrument", "blueprint", "rater", "scale", "360"],
            "Draft participant & rater journey": ["participant", "rater journey", "journey"],
            "Outline coaching program": ["coaching", "coach", "program"],
            "Create vendor plan": ["vendor", "build vs buy", "platform"],
        },
        3: {
            "Talk to EB Regional Manager for regional insights": ["regional", "europe", "country", "market"],
            "Build train-the-trainer rollout plan": ["train the trainer", "rollout", "workshop", "pilot"],
            "Define change risks and mitigation": ["change", "risk", "resistance", "mitigation"],
            "Construct measurement plan": ["kpi", "metric", "measure", "indicator"],
        },
    }

    def analyze(
        self,
        user_message: str,
        persona_id: str,
        current_module: int,
        recent_user_messages: list[str],
        emotional_state: dict[str, float],
        tasks_completed: list[str],
        turn_count: int,
    ) -> DirectorOutput:
        """
        Analyze the conversation state and generate guidance.
        Returns DirectorOutput with hint, issues, and task completions.
        """
        output = DirectorOutput()
        output.detected_issues = []

        # 1. Detect tasks being addressed
        output.tasks_detected = self._detect_tasks(user_message, current_module)

        # 2. Loop detection — include current message in window
        loop_messages = recent_user_messages + [user_message]
        if self._detect_loop(loop_messages):
            output.detected_issues.append("loop_detected")
            next_task = self._find_next_task(current_module, tasks_completed)
            if next_task:
                output.hint = self._generate_loop_hint(persona_id, next_task)

        # 3. Stuck detection
        if self._detect_stuck(user_message, recent_user_messages):
            output.detected_issues.append("user_stuck")
            output.hint = self._generate_stuck_hint(persona_id, current_module, tasks_completed)

        # 4. Off-topic detection
        if self._detect_off_topic(user_message, current_module):
            output.detected_issues.append("off_topic")
            if not output.hint:
                output.hint = self._generate_redirect_hint(persona_id, current_module)

        # 5. Module progress stall
        if self._detect_stall(turn_count, current_module, tasks_completed):
            output.detected_issues.append("module_progress_stall")
            if not output.hint:
                next_task = self._find_next_task(current_module, tasks_completed)
                if next_task:
                    output.hint = self._generate_progress_hint(persona_id, next_task)

        # 6. Check if module should advance
        module_obj = MODULE_OBJECTIVES.get(current_module, {})
        expected = module_obj.get("expected_actions", [])
        if len(tasks_completed) >= len(expected) * 0.7:
            output.suggested_module_advance = True

        return output

    # ── Loop Detection ──────────────────────────────────────────────────

    def _detect_loop(self, recent_messages: list[str]) -> bool:
        """Detect if user is repeating same topics."""
        if len(recent_messages) < self.LOOP_WINDOW:
            return False

        window = recent_messages[-self.LOOP_WINDOW:]
        # Simple word overlap similarity
        word_sets = [set(msg.lower().split()) for msg in window]
        for i in range(len(word_sets)):
            for j in range(i + 1, len(word_sets)):
                if word_sets[i] and word_sets[j]:
                    overlap = len(word_sets[i] & word_sets[j])
                    union = len(word_sets[i] | word_sets[j])
                    similarity = overlap / union if union > 0 else 0
                    if similarity > self.LOOP_SIMILARITY_THRESHOLD:
                        return True
        return False

    # ── Stuck Detection ─────────────────────────────────────────────────

    def _detect_stuck(self, current_msg: str, recent_messages: list[str]) -> bool:
        """Detect if user is stuck or confused."""
        # Check current message for confusion signals
        msg_lower = current_msg.lower()
        for pattern in self.CONFUSION_SIGNALS:
            if re.search(pattern, msg_lower):
                return True

        # Check if messages are very short repeatedly
        if len(recent_messages) >= self.STUCK_WINDOW:
            short_count = sum(
                1 for msg in recent_messages[-self.STUCK_WINDOW:]
                if len(msg.split()) < self.STUCK_TOKEN_THRESHOLD
            )
            if short_count >= self.STUCK_WINDOW:
                return True

        return False

    # ── Off-Topic Detection ─────────────────────────────────────────────

    def _detect_off_topic(self, message: str, current_module: int) -> bool:
        """Check if message is off-topic for the current module."""
        module_keywords = set()
        for task_keywords in self.TASK_KEYWORDS.get(current_module, {}).values():
            module_keywords.update(kw.lower() for kw in task_keywords)

        # Add general sim keywords
        module_keywords.update([
            "gucci", "leadership", "competency", "brand", "talent",
            "framework", "group", "dna", "mobility", "development",
        ])

        msg_words = set(message.lower().split())
        overlap = msg_words & module_keywords
        # If very little overlap with expected vocabulary, it's likely off-topic
        if len(message.split()) > 15 and len(overlap) == 0:
            return True
        return False

    # ── Module Progress Stall ───────────────────────────────────────────

    def _detect_stall(
        self, turn_count: int, current_module: int, tasks_completed: list[str]
    ) -> bool:
        """Detect if user has been in the module too long without progress."""
        # Stall if >10 turns with <30% tasks completed
        expected_count = len(
            MODULE_OBJECTIVES.get(current_module, {}).get("expected_actions", [])
        )
        if expected_count == 0:
            return False
        completion_rate = len(tasks_completed) / expected_count
        return turn_count > 10 and completion_rate < 0.3

    # ── Task Detection ──────────────────────────────────────────────────

    def _detect_tasks(self, message: str, current_module: int) -> list[str]:
        """Detect which tasks are being addressed by the user's message."""
        detected = []
        msg_lower = message.lower()
        task_map = self.TASK_KEYWORDS.get(current_module, {})
        for task_name, keywords in task_map.items():
            if any(kw in msg_lower for kw in keywords):
                detected.append(task_name)
        return detected

    # ── Find Next Task ──────────────────────────────────────────────────

    def _find_next_task(self, current_module: int, tasks_completed: list[str]) -> str | None:
        """Find the next uncompleted task in the current module."""
        expected = MODULE_OBJECTIVES.get(current_module, {}).get("expected_actions", [])
        for task in expected:
            if task not in tasks_completed:
                return task
        return None

    # ── Hint Generation ─────────────────────────────────────────────────

    def _generate_loop_hint(self, persona_id: str, next_task: str) -> str:
        hints = {
            "CEO": f"Subtly transition the conversation toward: {next_task}. Acknowledge what's been covered and redirect naturally.",
            "CHRO": f"Use a Socratic question to guide the user toward: {next_task}. Don't tell them what to do.",
            "EB Regional Manager": f"Pragmatically suggest moving to the next priority: {next_task}. Share a practical reason why.",
        }
        return hints.get(persona_id, f"Guide the user toward: {next_task}")

    def _generate_stuck_hint(
        self, persona_id: str, current_module: int, tasks_completed: list[str]
    ) -> str:
        next_task = self._find_next_task(current_module, tasks_completed)
        if not next_task:
            return "Provide encouragement and summarize progress so far."

        hints = {
            "CEO": f"The user seems stuck. Provide a strategic prompt related to: {next_task}. Be direct but helpful.",
            "CHRO": f"The user needs scaffolding. Ask a guiding question about: {next_task}. Offer a starting framework.",
            "EB Regional Manager": f"Give the user a concrete example to get them started on: {next_task}.",
        }
        return hints.get(persona_id, f"Help the user get started on: {next_task}")

    def _generate_redirect_hint(self, persona_id: str, current_module: int) -> str:
        module_name = MODULE_OBJECTIVES.get(current_module, {}).get("name", "the current module")
        return (
            f"The user has gone off-topic. Gently redirect back to {module_name}. "
            f"Stay in character and make the redirect feel natural."
        )

    def _generate_progress_hint(self, persona_id: str, next_task: str) -> str:
        return (
            f"The user has been in this module for a while. Proactively suggest moving to: "
            f"{next_task}. Make it feel like a natural progression, not a command."
        )

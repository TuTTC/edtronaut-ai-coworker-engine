"""
NPC Agent — core class.
Composes persona, Director, mock LLM, tools, safety, and state
into a single handle_message() interface.
"""

from __future__ import annotations

import logging
from typing import Any

from ..config import MODULE_OBJECTIVES
from ..personas import get_persona, BasePersona
from ..state.conversation import ConversationState
from ..state.emotional import EmotionalAnalyzer
from ..safety.guardrails import SafetyGuardrails
from ..tools.data_lookup import DataLookup
from .director import DirectorAgent

logger = logging.getLogger(__name__)


class NPCAgent:
    """
    AI Co-worker NPC Agent.
    Interface: handle_message(state, user_message) → (response, state)
    """

    def __init__(
        self,
        data_lookup: DataLookup | None = None,
        llm = None,
    ):
        self.director = DirectorAgent()
        if llm is None:
            from .mock_llm import MockLLM
            llm = MockLLM()
        self.llm = llm
        self.data_lookup = data_lookup
        self._personas: dict[str, BasePersona] = {}

    def _get_persona(self, persona_id: str) -> BasePersona:
        if persona_id not in self._personas:
            self._personas[persona_id] = get_persona(persona_id)
        return self._personas[persona_id]

    def handle_message(
        self,
        state: ConversationState,
        user_message: str,
    ) -> tuple[str, ConversationState, list[str]]:
        """
        Process a user message and return (response, updated_state, safety_flags).
        """
        persona_id = state.current_persona
        persona = self._get_persona(persona_id)

        # ── 1. Safety check ─────────────────────────────────────────────
        safety_result = SafetyGuardrails.check_input(user_message)
        if not safety_result.is_safe:
            state.safety_flags.extend(safety_result.flags)
            state.add_message("user", user_message, persona_id)
            response = safety_result.blocked_response or (
                "Let's stay focused on our leadership discussion."
            )
            state.add_message("assistant", response, persona_id)
            state.turn_count += 1
            return response, state, safety_result.flags

        # ── 2. Emotional analysis ───────────────────────────────────────
        emotional_deltas = EmotionalAnalyzer.analyze_message(user_message, persona_id)
        state.update_emotional_state(persona_id, emotional_deltas)

        # ── 3. Director analysis ────────────────────────────────────────
        recent_msgs = state.get_recent_user_messages(5)
        tasks_completed = state.module_progress.get(
            str(state.current_module), {}
        ).get("tasks_completed", [])

        director_output = self.director.analyze(
            user_message=user_message,
            persona_id=persona_id,
            current_module=state.current_module,
            recent_user_messages=recent_msgs,
            emotional_state=state.current_emotional_state,
            tasks_completed=tasks_completed,
            turn_count=state.turn_count,
        )

        # Update state from Director
        state.loop_detected = "loop_detected" in (director_output.detected_issues or [])
        state.director_hint = director_output.hint

        # Track tasks
        if director_output.tasks_detected:
            for task in director_output.tasks_detected:
                state.complete_task(state.current_module, task)

        # ── 4. Tool execution ───────────────────────────────────────────
        tool_results = self._maybe_use_tools(user_message, persona_id)

        # ── 5. Build dynamic system prompt ──────────────────────────────
        module_context = MODULE_OBJECTIVES.get(state.current_module)
        system_prompt = persona.build_system_prompt(
            emotional_state=state.current_emotional_state,
            director_hint=director_output.hint,
            module_context=module_context,
        )

        # ── 6. LLM call ────────────────────────────────────────────────
        messages = [
            {"role": m.role, "content": m.content}
            for m in state.get_recent_messages(10)
        ]

        response = self.llm.generate(
            system_prompt=system_prompt,
            messages=messages,
            user_message=user_message,
            persona_id=persona_id,
            emotional_state=state.current_emotional_state,
            director_hint=director_output.hint,
            tool_results=tool_results,
        )

        # ── 7. Safety post-process ──────────────────────────────────────
        response = SafetyGuardrails.check_output(response)

        # ── 8. Update state ─────────────────────────────────────────────
        state.add_message("user", user_message, persona_id)
        state.add_message("assistant", response, persona_id)
        state.turn_count += 1
        state.safety_flags.extend(safety_result.flags)

        # Extract topics
        topics = self._extract_topics(user_message)
        for topic in topics:
            state.add_topic(topic)

        # Performance score update
        trust = state.current_emotional_state.get("trust", 0.5)
        engagement = state.current_emotional_state.get("engagement", 0.5)
        completion = len(tasks_completed) / max(
            len(MODULE_OBJECTIVES.get(state.current_module, {}).get("expected_actions", [])),
            1,
        )
        state.user_performance_score = round(
            0.4 * trust + 0.3 * engagement + 0.3 * completion, 2
        )

        logger.info(
            f"[{persona_id}] Turn {state.turn_count}: "
            f"trust={trust:.2f}, "
            f"issues={director_output.detected_issues}, "
            f"tasks={director_output.tasks_detected}"
        )

        return response, state, safety_result.flags

    # ── Tool Execution ──────────────────────────────────────────────────

    def _maybe_use_tools(self, message: str, persona_id: str) -> str | None:
        """Determine if tools should be invoked and return results."""
        if not self.data_lookup:
            return None

        msg_lower = message.lower()

        # Persona-specific tool routing
        tool_triggers = {
            "CEO": {
                "keywords": ["data", "metric", "number", "brand", "9 brands", "mission", "culture"],
                "tool": self.data_lookup.lookup_group_data,
            },
            "CHRO": {
                "keywords": ["framework", "competency", "indicator", "level", "turnover", "retention"],
                "tool": self.data_lookup.lookup_hr_framework,
            },
            "EB Regional Manager": {
                "keywords": ["region", "country", "europe", "france", "italy", "trainer", "rollout"],
                "tool": self.data_lookup.lookup_regional_data,
            },
        }

        config = tool_triggers.get(persona_id)
        if config:
            if any(kw in msg_lower for kw in config["keywords"]):
                try:
                    return config["tool"](message)
                except Exception as e:
                    logger.error(f"Tool error: {e}")
                    return None

        return None

    # ── Topic Extraction ────────────────────────────────────────────────

    @staticmethod
    def _extract_topics(message: str) -> list[str]:
        """Extract key topic keywords from user message."""
        topic_words = {
            "mission", "dna", "culture", "values", "competency", "framework",
            "vision", "entrepreneurship", "passion", "trust",
            "mobility", "turnover", "retention", "engagement",
            "360", "feedback", "coaching", "rollout", "cascade",
            "kpi", "metric", "trainer", "workshop", "raci",
            "problem statement", "ceo pack", "deliverable",
        }
        msg_lower = message.lower()
        return [t for t in topic_words if t in msg_lower]

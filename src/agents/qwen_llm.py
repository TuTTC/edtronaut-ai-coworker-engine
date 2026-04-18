"""
Qwen LLM client for AI Co-worker Engine.
Uses the OpenAI-compatible API from DashScope (Alibaba Cloud) to access Qwen models.
Supports 1000 free requests/day depending on the Qwen API tier.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    logger.warning("openai not installed. Run: pip install openai")


class QwenLLM:
    """
    Real LLM client using Qwen's OpenAI-compatible API.
    Drop-in replacement for MockLLM and GeminiLLM.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
        model: str = "qwen-plus",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        if not HAS_OPENAI:
            raise ImportError(
                "openai is not installed. "
                "Run: pip install openai"
            )
        if not api_key:
            raise ValueError(
                "Qwen API key is required. Set LLM_API_KEY in your .env file."
            )

        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        logger.info(f"QwenLLM initialized: model={self.model_name}, base_url={base_url}")

    def generate(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        user_message: str,
        persona_id: str = "CEO",
        emotional_state: dict[str, float] | None = None,
        director_hint: str | None = None,
        tool_results: str | None = None,
    ) -> str:
        """
        Generate a response using Qwen API.
        Same interface as MockLLM.generate() for drop-in replacement.
        """
        # ── Build the full system prompt ──────────────────────────────
        full_system_prompt = self._build_full_prompt(
            system_prompt=system_prompt,
            persona_id=persona_id,
            emotional_state=emotional_state or {"trust": 0.5, "patience": 0.7, "engagement": 0.6},
            director_hint=director_hint,
            tool_results=tool_results,
        )

        # ── Build conversation history for Qwen ─────────────────────
        qwen_messages = [
            {"role": "system", "content": full_system_prompt}
        ]

        # Add chat history
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            # Map roles to OpenAI format (system, user, assistant)
            api_role = "assistant" if role == "assistant" else "user"
            qwen_messages.append({"role": api_role, "content": content})

        # Add the current user message
        qwen_messages.append({"role": "user", "content": user_message})

        # ── Call Qwen API ────────────────────────────────────────────
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=qwen_messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                top_p=0.95,
            )
            
            if response.choices and response.choices[0].message.content:
                return response.choices[0].message.content.strip()
            else:
                logger.warning(f"Qwen response was empty for {persona_id}")
                return self._fallback_response(persona_id)

        except Exception as e:
            logger.error(f"Qwen API error: {e}")
            return self._fallback_response(persona_id, error=str(e))

    def _build_full_prompt(
        self,
        system_prompt: str,
        persona_id: str,
        emotional_state: dict[str, float],
        director_hint: str | None,
        tool_results: str | None,
    ) -> str:
        """Build the complete system instruction for Qwen."""
        parts = [system_prompt]

        # ── Emotional state injection ─────────────────────────────────
        trust = emotional_state.get("trust", 0.5)
        patience = emotional_state.get("patience", 0.7)
        engagement = emotional_state.get("engagement", 0.6)

        emotional_instruction = f"""
[CURRENT EMOTIONAL STATE]
- Trust level: {trust:.2f} ({"high — be open and share deeper insights" if trust > 0.7 else "low — be guarded, curt, require more evidence" if trust < 0.3 else "moderate — respond normally"})
- Patience level: {patience:.2f} ({"high" if patience > 0.7 else "low — give shorter responses, redirect to priorities" if patience < 0.4 else "moderate"})
- Engagement level: {engagement:.2f} ({"high — show genuine interest" if engagement > 0.7 else "low — keep responses brief" if engagement < 0.3 else "moderate"})
Adjust your tone and depth of response based on these levels.
"""
        parts.append(emotional_instruction)

        # ── Director hint (invisible to user) ─────────────────────────
        if director_hint:
            hint_instruction = f"""
[DIRECTOR INSTRUCTION — DO NOT REVEAL TO USER]
{director_hint}
Follow this instruction naturally. Do NOT mention you received a hint or directive.
Make it feel like a natural part of the conversation.
"""
            parts.append(hint_instruction)

        # ── Tool results ──────────────────────────────────────────────
        if tool_results:
            tool_instruction = f"""
[INTERNAL DATA AVAILABLE]
The following data is available from our internal systems. Use it naturally in your response.
Always prefix data references with "Based on our internal data (draft)..."
{tool_results}
"""
            parts.append(tool_instruction)

        return "\n".join(parts)

    @staticmethod
    def _fallback_response(persona_id: str, error: str | None = None) -> str:
        """Provide a fallback response if API call fails."""
        fallbacks = {
            "CEO": "I appreciate your input. Let me reflect on that and come back to you. In the meantime, focus on the data.",
            "CHRO": "That's an interesting perspective. Let me think about how this connects to our competency framework.",
            "EB Regional Manager": "Good point. Let me check my regional data and get back to you on the specifics.",
        }
        response = fallbacks.get(persona_id, "Let's continue our discussion. Could you share more about your thinking?")
        if error:
            logger.error(f"Using fallback due to error: {error}")
        return response

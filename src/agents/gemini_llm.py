"""
Gemini LLM client for AI Co-worker Engine.
Replaces MockLLM with real Google Gemini API calls.
Uses the google-genai SDK (google-generativeai).
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    logger.warning("google-generativeai not installed. Run: pip install google-generativeai")


class GeminiLLM:
    """
    Real LLM client using Google Gemini API.
    Drop-in replacement for MockLLM — same generate() interface.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ):
        if not HAS_GEMINI:
            raise ImportError(
                "google-generativeai is not installed. "
                "Run: pip install google-generativeai"
            )
        if not api_key:
            raise ValueError(
                "Gemini API key is required. Set LLM_API_KEY in your .env file. "
                "Get a free key at: https://aistudio.google.com/apikey"
            )

        genai.configure(api_key=api_key)

        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Create the generative model with safety settings to allow role-play
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=genai.types.GenerationConfig(
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
                top_p=0.95,
            ),
        )

        logger.info(f"GeminiLLM initialized: model={self.model_name}")

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
        Generate a response using Gemini API.
        Same interface as MockLLM.generate() for drop-in replacement.
        """
        # ── Build the full prompt ──────────────────────────────────────
        full_system_prompt = self._build_full_prompt(
            system_prompt=system_prompt,
            persona_id=persona_id,
            emotional_state=emotional_state or {"trust": 0.5, "patience": 0.7, "engagement": 0.6},
            director_hint=director_hint,
            tool_results=tool_results,
        )

        # ── Build conversation history for Gemini ─────────────────────
        gemini_contents = []

        # System instruction is passed separately in Gemini
        # Build chat history from messages
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "assistant":
                gemini_contents.append({"role": "model", "parts": [content]})
            elif role == "user":
                gemini_contents.append({"role": "user", "parts": [content]})

        # Add the current user message
        gemini_contents.append({"role": "user", "parts": [user_message]})

        # ── Call Gemini API ────────────────────────────────────────────
        try:
            # Create model with system instruction for this call
            model_with_system = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=self.max_tokens,
                    top_p=0.95,
                ),
                system_instruction=full_system_prompt,
            )

            response = model_with_system.generate_content(gemini_contents)

            if response and response.text:
                return response.text.strip()
            else:
                # Handle blocked responses
                logger.warning(f"Gemini response was empty or blocked for {persona_id}")
                return self._fallback_response(persona_id)

        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            return self._fallback_response(persona_id, error=str(e))

    def _build_full_prompt(
        self,
        system_prompt: str,
        persona_id: str,
        emotional_state: dict[str, float],
        director_hint: str | None,
        tool_results: str | None,
    ) -> str:
        """Build the complete system instruction for Gemini."""
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
            "CEO": "I appreciate your input. Let me reflect on that and come back to you. In the meantime, focus on the data — that's what will drive our decision.",
            "CHRO": "That's an interesting perspective. Let me think about how this connects to our competency framework. Could you elaborate on one specific aspect?",
            "EB Regional Manager": "Good point. Let me check my regional data and get back to you on the specifics. What's your most pressing concern for the rollout?",
        }
        response = fallbacks.get(persona_id, "Let's continue our discussion. Could you share more about your thinking?")
        if error:
            logger.error(f"Using fallback due to error: {error}")
        return response

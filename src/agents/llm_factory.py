"""
LLM Factory — creates the appropriate LLM client based on LLM_PROVIDER config.
Supports: mock, gemini
"""

from __future__ import annotations

import logging
from typing import Protocol

logger = logging.getLogger(__name__)


class LLMInterface(Protocol):
    """Common interface that both MockLLM and GeminiLLM implement."""
    def generate(
        self,
        system_prompt: str,
        messages: list[dict[str, str]],
        user_message: str,
        persona_id: str = "CEO",
        emotional_state: dict[str, float] | None = None,
        director_hint: str | None = None,
        tool_results: str | None = None,
    ) -> str: ...


def create_llm(
    provider: str = "mock",
    api_key: str = "",
    model: str = "",
    temperature: float = 0.7,
    max_tokens: int = 1024,
) -> LLMInterface:
    """
    Factory function to create the appropriate LLM client.
    
    Args:
        provider: "mock" or "gemini"
        api_key: API key (required for gemini)
        model: Model name (e.g., "gemini-2.0-flash")
        temperature: Sampling temperature
        max_tokens: Max output tokens
    
    Returns:
        An LLM client implementing generate()
    """
    provider = provider.lower().strip()

    if provider == "gemini":
        from .gemini_llm import GeminiLLM
        return GeminiLLM(
            api_key=api_key,
            model=model or "gemini-2.0-flash",
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider in ["qwen", "openai"]:
        from .qwen_llm import QwenLLM
        # Default Qwen API URL, allow override if using actual OpenAI
        base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1" if provider == "qwen" else "https://api.openai.com/v1"
        return QwenLLM(
            api_key=api_key,
            base_url=base_url,
            model=model or "qwen-plus",
            temperature=temperature,
            max_tokens=max_tokens,
        )
    elif provider == "mock":
        from .mock_llm import MockLLM
        logger.info("Using MockLLM (no API key needed)")
        return MockLLM()
    else:
        logger.warning(f"Unknown LLM provider '{provider}', falling back to MockLLM")
        from .mock_llm import MockLLM
        return MockLLM()

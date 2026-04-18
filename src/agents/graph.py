"""
LangGraph workflow for the AI Co-worker Engine.
Defines the stateful conversation graph: safety → director → npc → state_update.
"""

from __future__ import annotations

import logging
from typing import Any, TypedDict, Annotated

from ..state.conversation import ConversationState
from ..agents.npc_agent import NPCAgent
from ..tools.data_lookup import DataLookup
from ..agents.llm_factory import create_llm
from ..config import LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

logger = logging.getLogger(__name__)

# Try to import langgraph; fall back to simple pipeline
try:
    from langgraph.graph import StateGraph, START, END
    HAS_LANGGRAPH = True
except ImportError:
    HAS_LANGGRAPH = False
    logger.warning("langgraph not installed — using simple pipeline fallback")


# ── Graph State Schema ──────────────────────────────────────────────────

class GraphState(TypedDict):
    """State passed through the LangGraph workflow."""
    session_id: str
    user_message: str
    persona_id: str
    conversation_state: dict   # Serialized ConversationState
    response: str
    safety_flags: list[str]
    is_blocked: bool


# ── Workflow Engine ─────────────────────────────────────────────────────

class WorkflowEngine:
    """
    Manages the conversation workflow.
    Uses LangGraph if available, otherwise a simple sequential pipeline.
    """

    def __init__(self, data_lookup: DataLookup | None = None):
        self.data_lookup = data_lookup or DataLookup()
        self.llm = create_llm(
            provider=LLM_PROVIDER,
            api_key=LLM_API_KEY,
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            max_tokens=LLM_MAX_TOKENS,
        )
        logger.info(f"LLM provider: {LLM_PROVIDER} (model: {LLM_MODEL})")
        self.npc_agent = NPCAgent(
            data_lookup=self.data_lookup,
            llm=self.llm,
        )

        if HAS_LANGGRAPH:
            self._graph = self._build_langgraph()
            logger.info("Workflow engine initialized with LangGraph")
        else:
            self._graph = None
            logger.info("Workflow engine initialized with simple pipeline")

    def _build_langgraph(self):
        """Build the LangGraph state graph."""
        builder = StateGraph(GraphState)

        # Add nodes
        builder.add_node("process_message", self._process_message_node)

        # Wire edges
        builder.add_edge(START, "process_message")
        builder.add_edge("process_message", END)

        return builder.compile()

    def _process_message_node(self, state: GraphState) -> dict:
        """
        Main processing node.
        Handles the full pipeline: safety → director → NPC → state update.
        """
        conv_state = ConversationState.from_dict(state["conversation_state"])
        conv_state.current_persona = state["persona_id"]

        response, updated_state, flags = self.npc_agent.handle_message(
            state=conv_state,
            user_message=state["user_message"],
        )

        return {
            "response": response,
            "safety_flags": flags,
            "conversation_state": updated_state.to_dict(),
            "is_blocked": not all(f not in flags for f in ["jailbreak_attempt"]),
        }

    def invoke(
        self,
        session_id: str,
        user_message: str,
        persona_id: str,
        conversation_state: ConversationState,
    ) -> tuple[str, ConversationState, list[str]]:
        """
        Run the workflow.
        Returns (response, updated_state, safety_flags).
        """
        input_state: GraphState = {
            "session_id": session_id,
            "user_message": user_message,
            "persona_id": persona_id,
            "conversation_state": conversation_state.to_dict(),
            "response": "",
            "safety_flags": [],
            "is_blocked": False,
        }

        if self._graph is not None:
            # LangGraph path
            result = self._graph.invoke(input_state)
        else:
            # Simple pipeline fallback
            result = self._process_message_node(input_state)
            result = {**input_state, **result}

        updated_state = ConversationState.from_dict(result["conversation_state"])
        return result["response"], updated_state, result["safety_flags"]

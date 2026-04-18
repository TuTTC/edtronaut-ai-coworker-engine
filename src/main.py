"""
FastAPI backend for AI Co-worker Engine.
Provides REST API endpoints for chat, state management, and session handling.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .config import FASTAPI_HOST, FASTAPI_PORT, PERSONA_IDS, MODULE_OBJECTIVES, SESSIONS_DIR
from .state.conversation import ConversationState
from .tools.data_lookup import DataLookup
from .agents.graph import WorkflowEngine

# ── Logging ─────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("ai_coworker_engine")

# ── App Setup ───────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Co-worker Engine",
    description="Scalable AI Co-worker Engine for job simulations — Gucci Group HRM prototype",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global State ────────────────────────────────────────────────────────

_sessions: dict[str, ConversationState] = {}
_engine: WorkflowEngine | None = None


def get_engine() -> WorkflowEngine:
    global _engine
    if _engine is None:
        logger.info("Initializing WorkflowEngine...")
        data_lookup = DataLookup()
        _engine = WorkflowEngine(data_lookup=data_lookup)
        logger.info("WorkflowEngine ready.")
    return _engine


def get_or_create_session(session_id: str) -> ConversationState:
    if session_id not in _sessions:
        # Try loading from disk
        session_path = SESSIONS_DIR / f"{session_id}.json"
        if session_path.exists():
            _sessions[session_id] = ConversationState.load(session_path)
        else:
            _sessions[session_id] = ConversationState(session_id=session_id)
    return _sessions[session_id]


def save_session(state: ConversationState):
    session_path = SESSIONS_DIR / f"{state.session_id}.json"
    state.save(session_path)


# ── Request/Response Models ─────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    persona_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    persona_id: str
    emotional_state: dict[str, float]
    current_module: int
    module_progress: dict
    turn_count: int
    safety_flags: list[str]
    user_performance_score: float
    loop_detected: bool
    director_hint: str | None = None
    topics_discussed: list[str]


class SessionInfo(BaseModel):
    session_id: str
    current_persona: str
    current_module: int
    turn_count: int
    emotional_states: dict[str, dict[str, float]]
    module_progress: dict
    user_performance_score: float


class ModuleAdvanceRequest(BaseModel):
    session_id: str
    target_module: int


class ToolRequest(BaseModel):
    session_id: str
    tool_name: str
    params: dict = {}


# ── Endpoints ───────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "AI Co-worker Engine",
        "version": "1.0.0",
        "simulation": "Gucci Group — HRM Talent & Leadership Development",
        "personas": PERSONA_IDS,
        "modules": {k: v["name"] for k, v in MODULE_OBJECTIVES.items()},
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint — processes a user message through the full pipeline."""
    if request.persona_id not in PERSONA_IDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid persona_id. Must be one of: {PERSONA_IDS}",
        )

    engine = get_engine()
    state = get_or_create_session(request.session_id)

    # Run the workflow
    response, updated_state, safety_flags = engine.invoke(
        session_id=request.session_id,
        user_message=request.message,
        persona_id=request.persona_id,
        conversation_state=state,
    )

    # Persist updated state
    _sessions[request.session_id] = updated_state
    save_session(updated_state)

    return ChatResponse(
        response=response,
        persona_id=request.persona_id,
        emotional_state=updated_state.emotional_states.get(
            request.persona_id, {"trust": 0.5, "patience": 0.7, "engagement": 0.6}
        ),
        current_module=updated_state.current_module,
        module_progress=updated_state.module_progress,
        turn_count=updated_state.turn_count,
        safety_flags=safety_flags,
        user_performance_score=updated_state.user_performance_score,
        loop_detected=updated_state.loop_detected,
        director_hint=updated_state.director_hint,
        topics_discussed=updated_state.topics_discussed,
    )


@app.get("/session/{session_id}", response_model=SessionInfo)
async def get_session(session_id: str):
    """Get the current state of a session."""
    state = get_or_create_session(session_id)
    return SessionInfo(
        session_id=state.session_id,
        current_persona=state.current_persona,
        current_module=state.current_module,
        turn_count=state.turn_count,
        emotional_states=state.emotional_states,
        module_progress=state.module_progress,
        user_performance_score=state.user_performance_score,
    )


@app.post("/session/new")
async def create_session():
    """Create a new simulation session."""
    session_id = str(uuid.uuid4())[:8]
    state = ConversationState(session_id=session_id)
    _sessions[session_id] = state
    save_session(state)
    return {"session_id": session_id}


@app.post("/session/{session_id}/advance-module")
async def advance_module(session_id: str, request: ModuleAdvanceRequest):
    """Advance to a different module."""
    state = get_or_create_session(session_id)
    if request.target_module not in MODULE_OBJECTIVES:
        raise HTTPException(status_code=400, detail="Invalid module. Must be 1, 2, or 3.")
    state.current_module = request.target_module
    _sessions[session_id] = state
    save_session(state)
    return {
        "session_id": session_id,
        "current_module": state.current_module,
        "module_name": MODULE_OBJECTIVES[request.target_module]["name"],
    }


@app.post("/tools/kpi")
async def tool_kpi(request: ToolRequest):
    """Run the KPI calculator tool."""
    from .tools.kpi_calculator import KPICalculator
    kpi_name = request.params.get("kpi_name")
    if kpi_name:
        return KPICalculator.calculate(kpi_name, **request.params)
    return KPICalculator.get_dashboard()


@app.post("/tools/competency-draft")
async def tool_competency(request: ToolRequest):
    """Run the competency drafter tool."""
    from .tools.competency_drafter import CompetencyDrafter
    action = request.params.get("action", "matrix")
    if action == "indicator":
        theme = request.params.get("theme", "Vision")
        level = request.params.get("level", "Associate")
        return {"result": CompetencyDrafter.draft_indicator(theme, level)}
    elif action == "problem_statement":
        return {"result": CompetencyDrafter.draft_problem_statement()}
    return {"result": CompetencyDrafter.draft_competency_matrix()}


@app.post("/tools/feedback")
async def tool_feedback(request: ToolRequest):
    """Run the feedback synthesizer tool."""
    from .tools.feedback_synthesizer import FeedbackSynthesizer
    leader_id = request.params.get("leader_id", "sample_leader_1")
    return {"result": FeedbackSynthesizer.synthesize(leader_id)}


@app.post("/tools/rollout")
async def tool_rollout(request: ToolRequest):
    """Run the rollout planner tool."""
    from .tools.rollout_planner import RolloutPlanner
    action = request.params.get("action", "checklist")
    wave = request.params.get("wave", 1)
    if action == "raci":
        return {"result": RolloutPlanner.generate_raci()}
    return {"result": RolloutPlanner.generate_checklist(wave)}


@app.get("/health")
async def health():
    return {"status": "healthy", "engine_loaded": _engine is not None}


# ── Run with: uvicorn src.main:app --host 0.0.0.0 --port 8000 ──────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=FASTAPI_HOST, port=int(FASTAPI_PORT))

"""
Configuration for AI Co-worker Engine.
Loads settings from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.parent
SRC_DIR = Path(__file__).parent
DATA_DIR = SRC_DIR / "data"
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(exist_ok=True)

# ── LLM ────────────────────────────────────────────────────────────────
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "mock-v1")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

# ── Server ─────────────────────────────────────────────────────────────
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))

# ── Defaults ───────────────────────────────────────────────────────────
DEFAULT_EMOTIONAL_STATE = {
    "trust": 0.5,
    "patience": 0.7,
    "engagement": 0.6,
}

PERSONA_IDS = ["CEO", "CHRO", "EB Regional Manager"]

# ── Simulation Context ─────────────────────────────────────────────────
SIMULATION_CONTEXT = {
    "title": "Gucci Group: Designing a Group-Level Leadership System across Luxury Brands",
    "user_role": "Group Global Organization Development (OD) Director, newly joined Group HR",
    "company": "Gucci Group — 9 iconic luxury brands operating with high autonomy",
    "group_hr_mandate": (
        "Identify and develop talent, increase inter-brand mobility, "
        "support (not impose on) brand DNA"
    ),
}

# ── Module Objectives ──────────────────────────────────────────────────
MODULE_OBJECTIVES = {
    1: {
        "name": "Frame the leadership problem & define Group DNA",
        "expected_actions": [
            "Write problem statement balancing brand autonomy with Group needs",
            "Talk to CEO about mission, culture, DNA",
            "Talk to CHRO about Competency Framework",
            "Craft competency model (4 themes × 3 levels)",
            "Map use cases (recruitment, appraisal, development, mobility)",
        ],
        "deliverables": [
            "Problem statement",
            "Competency matrix CSV",
            "10-slide CEO pack",
        ],
        "relevant_npcs": ["CEO", "CHRO"],
    },
    2: {
        "name": "Design the 360° + coaching program",
        "expected_actions": [
            "Specify instrument blueprint (rater groups, scale, items, anonymity, languages)",
            "Draft participant & rater journey",
            "Outline coaching program",
            "Create vendor plan (build vs buy)",
        ],
        "deliverables": [
            "5-page program spec",
            "Comms templates",
            "Sample 360° questionnaire",
        ],
        "relevant_npcs": [],
    },
    3: {
        "name": "Cascade & measure adoption",
        "expected_actions": [
            "Talk to EB Regional Manager (Europe) for regional insights",
            "Build train-the-trainer rollout plan",
            "Define change risks and mitigation",
            "Construct measurement plan (leading + lagging KPIs)",
        ],
        "deliverables": [
            "Rollout playbook",
            "KPI table",
            "Sample exec insights page",
        ],
        "relevant_npcs": ["EB Regional Manager"],
    },
}

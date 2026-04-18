"""
Streamlit Chat UI for AI Co-worker Engine.
Features: NPC selection, module tracker, emotional state display, chat interface.
"""

import streamlit as st
import httpx
import uuid
import time

# ── Page Config ─────────────────────────────────────────────────────────

st.set_page_config(
    page_title="AI Co-worker Engine — Gucci Group Simulation",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global */
* { font-family: 'Inter', sans-serif; }

/* Header */
.main-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 1.2rem 1.5rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.main-header h1 {
    color: white !important;
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    padding: 0 !important;
}

.main-header p {
    color: rgba(255,255,255,0.85) !important;
    font-size: 0.85rem !important;
    margin: 0.3rem 0 0 0 !important;
}

.npc-name {
    font-weight: 600;
    font-size: 0.95rem;
    margin-bottom: 0.2rem;
}

.npc-role {
    font-size: 0.75rem;
    opacity: 0.7;
}

.emotion-bar-container {
    margin: 0.3rem 0;
}

.emotion-label {
    font-size: 0.7rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    opacity: 0.8;
}

.module-number {
    font-weight: 700;
    color: #667eea !important;
}

.chat-container {
    max-height: 500px;
    overflow-y: auto;
    padding: 1rem;
    border-radius: 12px;
}

.status-badge {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

.badge-safe { background: rgba(34, 197, 94, 0.2); color: #22c55e; }
.badge-warning { background: rgba(250, 204, 21, 0.2); color: #facc15; }
.badge-danger { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

.perf-score {
    font-size: 2rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Light Theme Variables & Specifics */
.stApp { background: linear-gradient(135deg, #f5f7fa 0%, #e4e8f0 50%, #d1d8e0 100%); }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f5f7fa 0%, #e4e8f0 100%);
    border-right: 1px solid rgba(0,0,0,0.1);
}
[data-testid="stSidebar"] * { color: #1a1a2e !important; }
.npc-card {
    background: linear-gradient(135deg, rgba(0,0,0,0.05) 0%, rgba(0,0,0,0.02) 100%);
    border: 1px solid rgba(0,0,0,0.1);
    border-radius: 10px; padding: 0.8rem 1rem; margin-bottom: 0.5rem; transition: all 0.3s ease;
}
.npc-card:hover { border-color: rgba(102, 126, 234, 0.5); box-shadow: 0 2px 12px rgba(102, 126, 234, 0.15); }
.npc-card.active {
    border-color: #667eea; box-shadow: 0 0 15px rgba(102, 126, 234, 0.3);
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.15) 0%, rgba(118, 75, 162, 0.1) 100%);
}
.module-card {
    background: rgba(0,0,0,0.03); border: 1px solid rgba(0,0,0,0.1);
    border-radius: 8px; padding: 0.6rem 0.8rem; margin-bottom: 0.4rem;
}
.module-card.current { border-color: #667eea; background: rgba(102, 126, 234, 0.1); }
.chat-container { background: rgba(0,0,0,0.02); border: 1px solid rgba(0,0,0,0.05); }
.sidebar-divider { border-top: 1px solid rgba(0,0,0,0.1); margin: 0.8rem 0; }
[data-testid="stChatMessage"] {
    background: rgba(0,0,0,0.03) !important; border: 1px solid rgba(0,0,0,0.06) !important;
    border-radius: 12px !important; margin-bottom: 0.5rem !important;
}
</style>
""", unsafe_allow_html=True)

# ── Constants ───────────────────────────────────────────────────────────

API_BASE = "http://localhost:8000"

PERSONA_CONFIG = {
    "CEO": {
        "emoji": "👔",
        "name": "Gucci Group CEO",
        "short": "Strategic, decisive, protective of Group DNA",
        "color": "#667eea",
    },
    "CHRO": {
        "emoji": "🎓",
        "name": "Gucci Group CHRO",
        "short": "Empathetic, Socratic, framework guardian",
        "color": "#764ba2",
    },
    "EB Regional Manager": {
        "emoji": "🌍",
        "name": "EB Regional Manager (Europe)",
        "short": "Pragmatic, execution-focused, ground truth",
        "color": "#f093fb",
    },
}

MODULE_INFO = {
    1: {"name": "Frame DNA", "full": "Frame the leadership problem & define Group DNA", "duration": "35-45 min"},
    2: {"name": "360° Design", "full": "Design the 360° + coaching program", "duration": "55-65 min"},
    3: {"name": "Cascade", "full": "Cascade & measure adoption", "duration": "30-40 min"},
}

# ── Session State Init ──────────────────────────────────────────────────

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_persona" not in st.session_state:
    st.session_state.current_persona = "CEO"
if "current_module" not in st.session_state:
    st.session_state.current_module = 1
if "emotional_states" not in st.session_state:
    st.session_state.emotional_states = {
        "CEO": {"trust": 0.5, "patience": 0.7, "engagement": 0.6},
        "CHRO": {"trust": 0.5, "patience": 0.7, "engagement": 0.6},
        "EB Regional Manager": {"trust": 0.5, "patience": 0.7, "engagement": 0.6},
    }
if "module_progress" not in st.session_state:
    st.session_state.module_progress = {
        "1": {"tasks_completed": [], "deliverables_submitted": []},
        "2": {"tasks_completed": [], "deliverables_submitted": []},
        "3": {"tasks_completed": [], "deliverables_submitted": []},
    }
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0
if "performance_score" not in st.session_state:
    st.session_state.performance_score = 0.5
if "topics_discussed" not in st.session_state:
    st.session_state.topics_discussed = []
if "api_available" not in st.session_state:
    st.session_state.api_available = None

# ── API Communication ──────────────────────────────────────────────────


def check_api():
    """Check if the FastAPI backend is available."""
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def send_message(persona_id: str, message: str) -> dict | None:
    """Send a message to the backend API."""
    try:
        r = httpx.post(
            f"{API_BASE}/chat",
            json={
                "session_id": st.session_state.session_id,
                "persona_id": persona_id,
                "message": message,
            },
            timeout=30.0,
        )
        if r.status_code == 200:
            return r.json()
        else:
            st.error(f"API error: {r.status_code} — {r.text}")
            return None
    except httpx.ConnectError:
        st.error("⚠️ Cannot connect to backend. Make sure FastAPI is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def advance_module(target_module: int):
    """Advance to a different module."""
    try:
        r = httpx.post(
            f"{API_BASE}/session/{st.session_state.session_id}/advance-module",
            json={"session_id": st.session_state.session_id, "target_module": target_module},
            timeout=5.0,
        )
        if r.status_code == 200:
            st.session_state.current_module = target_module
            return True
    except Exception:
        pass
    # Fallback: update locally
    st.session_state.current_module = target_module
    return True


# ── Sidebar ─────────────────────────────────────────────────────────────

with st.sidebar:
    # Logo & Title
    st.markdown("""
    <div style="text-align: center; padding: 0.5rem 0 1rem 0;">
        <div style="font-size: 2.5rem;">🏛️</div>
        <div style="font-size: 1.1rem; font-weight: 700; background: linear-gradient(135deg, #667eea, #764ba2);
                    -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            AI Co-worker Engine
        </div>
        <div style="font-size: 0.7rem; opacity: 0.6; margin-top: 0.2rem;">Gucci Group — HRM Simulation</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # ── NPC Selection ───────────────────────────────────────────────
    st.markdown("#### 🎭 Select NPC")

    for pid, config in PERSONA_CONFIG.items():
        is_active = st.session_state.current_persona == pid
        active_class = "active" if is_active else ""

        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"""
            <div class="npc-card {active_class}">
                <div class="npc-name">{config['emoji']} {config['name']}</div>
                <div class="npc-role">{config['short']}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("→", key=f"switch_{pid}", type="secondary" if not is_active else "primary"):
                st.session_state.current_persona = pid
                st.rerun()

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # ── Emotional State ─────────────────────────────────────────────
    st.markdown("#### 💫 Emotional State")
    current_emotions = st.session_state.emotional_states.get(
        st.session_state.current_persona,
        {"trust": 0.5, "patience": 0.7, "engagement": 0.6}
    )

    emotion_colors = {"trust": "#22c55e", "patience": "#facc15", "engagement": "#667eea"}
    emotion_emojis = {"trust": "🤝", "patience": "⏳", "engagement": "⚡"}

    for emotion, value in current_emotions.items():
        emoji = emotion_emojis.get(emotion, "")
        color = emotion_colors.get(emotion, "#667eea")
        st.markdown(f"""
        <div class="emotion-bar-container">
            <div class="emotion-label">{emoji} {emotion.upper()} — {value:.0%}</div>
        </div>
        """, unsafe_allow_html=True)
        st.progress(value)

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # ── Module Tracker ──────────────────────────────────────────────
    st.markdown("#### 📋 Module Progress")

    for mod_id, mod_info in MODULE_INFO.items():
        is_current = st.session_state.current_module == mod_id
        current_class = "current" if is_current else ""
        progress = st.session_state.module_progress.get(str(mod_id), {})
        tasks_done = len(progress.get("tasks_completed", []))

        col1, col2 = st.columns([4, 1])
        with col1:
            marker = "▶" if is_current else "○"
            st.markdown(f"""
            <div class="module-card {current_class}">
                <span class="module-number">{marker} Module {mod_id}</span><br>
                <span style="font-size: 0.78rem;">{mod_info['name']}</span><br>
                <span style="font-size: 0.68rem; opacity: 0.6;">Tasks: {tasks_done} done · {mod_info['duration']}</span>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if not is_current:
                if st.button(f"Go", key=f"mod_{mod_id}"):
                    advance_module(mod_id)
                    st.rerun()

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # ── Performance Score ───────────────────────────────────────────
    st.markdown("#### 🏆 Performance")
    score = st.session_state.performance_score
    st.markdown(f'<div class="perf-score">{score:.0%}</div>', unsafe_allow_html=True)
    st.caption(f"Turn count: {st.session_state.turn_count}")

    # ── Topics Discussed ────────────────────────────────────────────
    if st.session_state.topics_discussed:
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        st.markdown("#### 🏷️ Topics Covered")
        topics_display = " · ".join(
            f"`{t}`" for t in st.session_state.topics_discussed[-10:]
        )
        st.markdown(topics_display)


    # ── Session Info ────────────────────────────────────────────────
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.caption(f"Session: `{st.session_state.session_id}`")

    # API Status
    api_ok = check_api()
    if api_ok:
        st.markdown('<span class="status-badge badge-safe">● API Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-badge badge-danger">● API Offline</span>', unsafe_allow_html=True)
        st.caption("Run: `uvicorn src.main:app --port 8000`")

    if st.button("🔄 New Session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ── Main Chat Area ──────────────────────────────────────────────────────

persona_cfg = PERSONA_CONFIG[st.session_state.current_persona]
mod_info = MODULE_INFO[st.session_state.current_module]

# Header
st.markdown(f"""
<div class="main-header">
    <h1>{persona_cfg['emoji']} Conversation with {persona_cfg['name']}</h1>
    <p>Module {st.session_state.current_module}: {mod_info['full']} · {mod_info['duration']}</p>
</div>
""", unsafe_allow_html=True)

# Chat history
for msg in st.session_state.messages:
    role = msg["role"]
    persona = msg.get("persona_id", st.session_state.current_persona)
    avatar = PERSONA_CONFIG.get(persona, {}).get("emoji", "🤖") if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        if role == "assistant":
            st.markdown(f"**{PERSONA_CONFIG.get(persona, {}).get('name', persona)}:**")
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input(f"Message {persona_cfg['name']}..."):
    # Show user message
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "persona_id": st.session_state.current_persona,
    })

    # Get response
    with st.chat_message("assistant", avatar=persona_cfg["emoji"]):
        with st.spinner(f"{persona_cfg['name']} is thinking..."):
            api_ok = check_api()
            if api_ok:
                result = send_message(st.session_state.current_persona, prompt)
                if result:
                    response = result["response"]
                    # Update state from API response
                    st.session_state.emotional_states[st.session_state.current_persona] = result["emotional_state"]
                    st.session_state.current_module = result["current_module"]
                    st.session_state.module_progress = result["module_progress"]
                    st.session_state.turn_count = result["turn_count"]
                    st.session_state.performance_score = result["user_performance_score"]
                    st.session_state.topics_discussed = result["topics_discussed"]
                else:
                    response = "I'm having trouble processing that. Could you rephrase?"
            else:
                # Fallback: direct engine call (no API needed)
                try:
                    import sys
                    from pathlib import Path
                    # Add project root to path
                    project_root = Path(__file__).parent.parent.parent
                    if str(project_root) not in sys.path:
                        sys.path.insert(0, str(project_root))

                    from src.agents.graph import WorkflowEngine
                    from src.state.conversation import ConversationState

                    if "engine" not in st.session_state:
                        st.session_state.engine = WorkflowEngine()

                    if "conv_state" not in st.session_state:
                        st.session_state.conv_state = ConversationState(
                            session_id=st.session_state.session_id
                        )

                    conv = st.session_state.conv_state
                    response, conv, flags = st.session_state.engine.invoke(
                        session_id=st.session_state.session_id,
                        user_message=prompt,
                        persona_id=st.session_state.current_persona,
                        conversation_state=conv,
                    )
                    st.session_state.conv_state = conv

                    # Sync state
                    st.session_state.emotional_states = conv.emotional_states
                    st.session_state.current_module = conv.current_module
                    st.session_state.module_progress = conv.module_progress
                    st.session_state.turn_count = conv.turn_count
                    st.session_state.performance_score = conv.user_performance_score
                    st.session_state.topics_discussed = conv.topics_discussed
                except Exception as e:
                    response = f"Engine error: {e}. Please start the FastAPI backend."

        st.markdown(f"**{persona_cfg['name']}:**")
        st.markdown(response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "persona_id": st.session_state.current_persona,
    })

    st.rerun()

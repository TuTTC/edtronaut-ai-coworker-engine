"""
Conversation state management for AI Co-worker Engine.
Tracks messages, emotional memory (per-NPC), module progress, and safety flags.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Message:
    """A single message in the conversation."""

    role: str                               # "user" | "assistant" | "system"
    content: str
    persona_id: str | None = None
    timestamp: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "persona_id": self.persona_id,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Message:
        return cls(**data)


@dataclass
class ConversationState:
    """Full conversation state including emotional memory and module progress."""

    session_id: str
    messages: list[Message] = field(default_factory=list)
    current_persona: str = "CEO"

    # Emotional memory — per-NPC
    emotional_states: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "CEO": {"trust": 0.5, "patience": 0.7, "engagement": 0.6},
            "CHRO": {"trust": 0.5, "patience": 0.7, "engagement": 0.6},
            "EB Regional Manager": {"trust": 0.5, "patience": 0.7, "engagement": 0.6},
        }
    )

    # Module tracking
    current_module: int = 1
    module_progress: dict = field(
        default_factory=lambda: {
            "1": {"tasks_completed": [], "deliverables_submitted": []},
            "2": {"tasks_completed": [], "deliverables_submitted": []},
            "3": {"tasks_completed": [], "deliverables_submitted": []},
        }
    )
    topics_discussed: list[str] = field(default_factory=list)

    # Performance tracking
    user_performance_score: float = 0.5
    turn_count: int = 0

    # Director state
    loop_detected: bool = False
    director_hint: str | None = None

    # Safety
    safety_flags: list[str] = field(default_factory=list)

    # ── Properties ──────────────────────────────────────────────────────

    @property
    def current_emotional_state(self) -> dict[str, float]:
        """Get emotional state for the currently-selected NPC."""
        default = {"trust": 0.5, "patience": 0.7, "engagement": 0.6}
        return self.emotional_states.get(self.current_persona, default)

    @property
    def current_module_progress(self) -> dict:
        return self.module_progress.get(str(self.current_module), {
            "tasks_completed": [],
            "deliverables_submitted": [],
        })

    # ── Mutators ────────────────────────────────────────────────────────

    def add_message(
        self,
        role: str,
        content: str,
        persona_id: str | None = None,
        metadata: dict | None = None,
    ):
        self.messages.append(Message(
            role=role,
            content=content,
            persona_id=persona_id or self.current_persona,
            metadata=metadata or {},
        ))

    def get_recent_messages(self, n: int = 10) -> list[Message]:
        return self.messages[-n:]

    def get_recent_user_messages(self, n: int = 5) -> list[str]:
        """Get last N user messages (for loop detection)."""
        user_msgs = [m.content for m in self.messages if m.role == "user"]
        return user_msgs[-n:]

    def update_emotional_state(self, persona_id: str, deltas: dict[str, float]):
        """Apply emotional deltas to a specific NPC. Clamped to [0, 1]."""
        if persona_id not in self.emotional_states:
            self.emotional_states[persona_id] = {
                "trust": 0.5, "patience": 0.7, "engagement": 0.6
            }
        for key, delta in deltas.items():
            current = self.emotional_states[persona_id].get(key, 0.5)
            self.emotional_states[persona_id][key] = max(0.0, min(1.0, current + delta))

    def complete_task(self, module: int, task: str):
        key = str(module)
        if key in self.module_progress:
            completed = self.module_progress[key]["tasks_completed"]
            if task not in completed:
                completed.append(task)

    def submit_deliverable(self, module: int, deliverable: str):
        key = str(module)
        if key in self.module_progress:
            submitted = self.module_progress[key]["deliverables_submitted"]
            if deliverable not in submitted:
                submitted.append(deliverable)

    def add_topic(self, topic: str):
        if topic and topic not in self.topics_discussed:
            self.topics_discussed.append(topic)

    # ── Serialization ───────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "messages": [m.to_dict() for m in self.messages],
            "current_persona": self.current_persona,
            "emotional_states": self.emotional_states,
            "current_module": self.current_module,
            "module_progress": self.module_progress,
            "topics_discussed": self.topics_discussed,
            "user_performance_score": self.user_performance_score,
            "turn_count": self.turn_count,
            "loop_detected": self.loop_detected,
            "director_hint": self.director_hint,
            "safety_flags": self.safety_flags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ConversationState:
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return cls(
            session_id=data["session_id"],
            messages=messages,
            current_persona=data.get("current_persona", "CEO"),
            emotional_states=data.get("emotional_states", {}),
            current_module=data.get("current_module", 1),
            module_progress=data.get("module_progress", {}),
            topics_discussed=data.get("topics_discussed", []),
            user_performance_score=data.get("user_performance_score", 0.5),
            turn_count=data.get("turn_count", 0),
            loop_detected=data.get("loop_detected", False),
            director_hint=data.get("director_hint"),
            safety_flags=data.get("safety_flags", []),
        )

    def save(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

    @classmethod
    def load(cls, path: Path) -> ConversationState:
        with open(path, "r", encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

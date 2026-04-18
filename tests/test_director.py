"""Tests for Director Agent — loop, stuck, off-topic, stall detection."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.director import DirectorAgent


def test_loop_detection():
    """Director should detect when user repeats the same topic."""
    director = DirectorAgent()
    repeated = [
        "Tell me about the mission of the group",
        "What is the mission of the group",
        "Can you explain the mission of the group",
    ]
    result = director.analyze(
        user_message="Tell me about the mission of the group again",
        persona_id="CEO",
        current_module=1,
        recent_user_messages=repeated,
        emotional_state={"trust": 0.5, "patience": 0.5, "engagement": 0.5},
        tasks_completed=[],
        turn_count=5,
    )
    assert "loop_detected" in (result.detected_issues or []), "Should detect loop"
    assert result.hint is not None, "Should generate a hint"
    print("✅ test_loop_detection passed")


def test_stuck_detection():
    """Director should detect when user is confused/stuck."""
    director = DirectorAgent()
    result = director.analyze(
        user_message="I'm not sure what to do. Can you help me?",
        persona_id="CHRO",
        current_module=1,
        recent_user_messages=["ok", "hmm", "I don't know"],
        emotional_state={"trust": 0.5, "patience": 0.5, "engagement": 0.5},
        tasks_completed=[],
        turn_count=5,
    )
    assert "user_stuck" in (result.detected_issues or []), "Should detect stuck user"
    assert result.hint is not None, "Should generate a scaffolding hint"
    print("✅ test_stuck_detection passed")


def test_task_detection():
    """Director should detect tasks being addressed."""
    director = DirectorAgent()
    result = director.analyze(
        user_message="I've drafted a problem statement about the tension between brand autonomy and group needs",
        persona_id="CEO",
        current_module=1,
        recent_user_messages=[],
        emotional_state={"trust": 0.5, "patience": 0.5, "engagement": 0.5},
        tasks_completed=[],
        turn_count=3,
    )
    assert len(result.tasks_detected) > 0, "Should detect problem statement task"
    print(f"✅ test_task_detection passed — detected: {result.tasks_detected}")


def test_no_false_positives():
    """Normal conversation should not trigger detection rules."""
    director = DirectorAgent()
    result = director.analyze(
        user_message="I'd like to discuss the competency framework. Can you walk me through the 4 themes?",
        persona_id="CHRO",
        current_module=1,
        recent_user_messages=["Hello, nice to meet you"],
        emotional_state={"trust": 0.5, "patience": 0.7, "engagement": 0.6},
        tasks_completed=[],
        turn_count=2,
    )
    issues = result.detected_issues or []
    assert "loop_detected" not in issues, "Should not detect loop"
    assert "user_stuck" not in issues, "Should not detect stuck"
    print("✅ test_no_false_positives passed")


def test_module_stall():
    """Director should detect progress stall."""
    director = DirectorAgent()
    result = director.analyze(
        user_message="So about the mission...",
        persona_id="CEO",
        current_module=1,
        recent_user_messages=["hmm"] * 5,
        emotional_state={"trust": 0.3, "patience": 0.3, "engagement": 0.3},
        tasks_completed=[],
        turn_count=15,
    )
    assert "module_progress_stall" in (result.detected_issues or []), "Should detect stall"
    print("✅ test_module_stall passed")


if __name__ == "__main__":
    test_loop_detection()
    test_stuck_detection()
    test_task_detection()
    test_no_false_positives()
    test_module_stall()
    print("\n🎉 All Director tests passed!")

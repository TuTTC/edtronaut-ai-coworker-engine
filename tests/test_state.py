"""Tests for ConversationState and EmotionalAnalyzer."""

import sys
import json
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state.conversation import ConversationState, Message
from src.state.emotional import EmotionalAnalyzer


def test_state_initialization():
    """New state should have correct defaults."""
    state = ConversationState(session_id="test-001")
    assert state.current_module == 1
    assert state.turn_count == 0
    assert state.current_persona == "CEO"
    assert len(state.messages) == 0
    assert "CEO" in state.emotional_states
    assert "CHRO" in state.emotional_states
    assert "EB Regional Manager" in state.emotional_states
    print("✅ test_state_initialization passed")


def test_add_message():
    """Messages should be added correctly."""
    state = ConversationState(session_id="test-002")
    state.add_message("user", "Hello!", "CEO")
    state.add_message("assistant", "Welcome!", "CEO")
    assert len(state.messages) == 2
    assert state.messages[0].role == "user"
    assert state.messages[1].role == "assistant"
    print("✅ test_add_message passed")


def test_emotional_state_update():
    """Emotional state should be updated with deltas and clamped."""
    state = ConversationState(session_id="test-003")
    state.update_emotional_state("CEO", {"trust": 0.3, "patience": -0.5})
    assert abs(state.emotional_states["CEO"]["trust"] - 0.8) < 0.01  # 0.5 + 0.3
    assert abs(state.emotional_states["CEO"]["patience"] - 0.2) < 0.01  # 0.7 - 0.5
    print("✅ test_emotional_state_update passed")


def test_emotional_state_clamped():
    """Emotional values should be clamped to [0, 1]."""
    state = ConversationState(session_id="test-004")
    state.update_emotional_state("CEO", {"trust": 10.0})  # Way over
    assert state.emotional_states["CEO"]["trust"] == 1.0
    state.update_emotional_state("CEO", {"trust": -10.0})  # Way under
    assert state.emotional_states["CEO"]["trust"] == 0.0
    print("✅ test_emotional_state_clamped passed")


def test_per_npc_emotional_isolation():
    """Each NPC should have independent emotional state."""
    state = ConversationState(session_id="test-005")
    state.update_emotional_state("CEO", {"trust": -0.4})
    assert abs(state.emotional_states["CEO"]["trust"] - 0.1) < 0.01  # 0.5 - 0.4
    assert state.emotional_states["CHRO"]["trust"] == 0.5  # Unchanged
    print("✅ test_per_npc_emotional_isolation passed")


def test_serialization():
    """State should serialize to/from dict correctly."""
    state = ConversationState(session_id="test-006")
    state.add_message("user", "Hello", "CEO")
    state.complete_task(1, "Write problem statement")
    state.update_emotional_state("CEO", {"trust": 0.1})

    data = state.to_dict()
    restored = ConversationState.from_dict(data)

    assert restored.session_id == "test-006"
    assert len(restored.messages) == 1
    assert "Write problem statement" in restored.module_progress["1"]["tasks_completed"]
    assert abs(restored.emotional_states["CEO"]["trust"] - 0.6) < 0.01  # 0.5 + 0.1
    print("✅ test_serialization passed")


def test_save_load():
    """State should save to and load from disk."""
    state = ConversationState(session_id="test-007")
    state.add_message("user", "Test message", "CEO")
    state.turn_count = 5

    # Save to temp file
    tmp = Path(tempfile.mktemp(suffix=".json"))
    try:
        state.save(tmp)
        loaded = ConversationState.load(tmp)
        assert loaded.session_id == "test-007"
        assert loaded.turn_count == 5
        assert len(loaded.messages) == 1
        print("✅ test_save_load passed")
    finally:
        tmp.unlink(missing_ok=True)


def test_emotional_analyzer_positive():
    """Positive messages should generate positive deltas."""
    deltas = EmotionalAnalyzer.analyze_message(
        "I've drafted a problem statement with data showing 2.3% mobility. My recommendation is a phased approach.",
        "CEO",
    )
    assert deltas["trust"] > 0, "Positive message should increase trust"
    assert deltas["engagement"] > 0, "Positive message should increase engagement"
    print(f"✅ test_emotional_analyzer_positive passed — deltas: {deltas}")


def test_emotional_analyzer_negative():
    """Negative/lazy messages should generate negative deltas."""
    deltas = EmotionalAnalyzer.analyze_message(
        "Tell me about Gucci. What does the company do?",
        "CEO",
    )
    assert deltas["trust"] < 0 or deltas["patience"] < 0, \
        "Lazy message should decrease trust or patience"
    print(f"✅ test_emotional_analyzer_negative passed — deltas: {deltas}")


def test_emotional_analyzer_persona_modifier():
    """CEO should be harsher than CHRO for the same lazy message."""
    msg = "Tell me about the company"
    ceo_deltas = EmotionalAnalyzer.analyze_message(msg, "CEO")
    chro_deltas = EmotionalAnalyzer.analyze_message(msg, "CHRO")

    if ceo_deltas["patience"] < 0 and chro_deltas["patience"] < 0:
        assert abs(ceo_deltas["patience"]) >= abs(chro_deltas["patience"]), \
            "CEO should be harsher than CHRO"
    print(f"✅ test_emotional_analyzer_persona_modifier passed — CEO: {ceo_deltas['patience']:.3f}, CHRO: {chro_deltas['patience']:.3f}")


if __name__ == "__main__":
    test_state_initialization()
    test_add_message()
    test_emotional_state_update()
    test_emotional_state_clamped()
    test_per_npc_emotional_isolation()
    test_serialization()
    test_save_load()
    test_emotional_analyzer_positive()
    test_emotional_analyzer_negative()
    test_emotional_analyzer_persona_modifier()
    print("\n🎉 All State tests passed!")

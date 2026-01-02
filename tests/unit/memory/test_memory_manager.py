from __future__ import annotations

from pathlib import Path
import pytest

from research_learning_agent.schemas import (
    UserMemory,
    UserPreferences,
    ExplanationStyle,
    ResourcePreference,
    Verbosity,
    LearningIntent,
    LearningMode,
)
from research_learning_agent.memory import MemoryManager
from research_learning_agent.store.memory_store import MemoryStore


def test_memory_manager_load_missing_returns_default_memory(tmp_path: Path) -> None:
    """
    load missing file -> default memory
    (MemoryManager returns UserMemory even if sotre returns None)
    """
    store = MemoryStore(path=tmp_path / "user_memory.json")
    mgr = MemoryManager(store)

    mem = mgr.load(user_id="default")
    assert isinstance(mem, UserMemory)
    assert mem.user_id == "default"
    assert mem.topics == []
    assert mem.history == []
    assert mem.preferences is not None


def test_update_after_answer_adds_topic_and_updates_last_topic(tmp_path: Path) -> None:
    store = MemoryStore(path=tmp_path / "user_memory.json")
    mgr = MemoryManager(store)

    mem = UserMemory(user_id="default")

    mem2 = mgr.update_after_answer(
        mem,
        query="What is reinforcement learning?",
        topic="reinforcement learning",
        intent=LearningIntent.casual_curiosity,
        mode=LearningMode.quick_explain,
        answer_summary="RL is learning to maximize reward."
    )

    assert mem2.last_topic == "reinforcement learning"
    assert mem2.topics == ["reinforcement learning"]
    assert len(mem2.history) == 1
    assert mem2.history[0].topic == "reinforcement learning"
    assert mem2.history[0].mode == LearningMode.quick_explain


def test_update_after_answer_keeps_topic_recency_order(tmp_path: Path) -> None:
    """
    update adds topic, keeps recency (move existing topic to the end)
    """
    store = MemoryStore(path=tmp_path / "user_memory.json")
    mgr = MemoryManager(store)

    mem = UserMemory(user_id="default")
    mem.topics = ["topicA", "topicB", "topicC"]

    # repeat topicB; should move to end
    mem = mgr.update_after_answer(
        mem,
        query="x",
        topic="topicB",
        intent=LearningIntent.casual_curiosity,
        mode=LearningMode.quick_explain,
        answer_summary="s",
    )

    assert mem.topics == ["topicA", "topicC", "topicB"]
    assert mem.last_topic == "topicB"


def test_update_after_answer_caps_history(monkeypatch, tmp_path: Path) -> None:
    import research_learning_agent.memory as mem_mod

    # Make cap small so test is fast and detreministic
    monkeypatch.setattr(mem_mod, "MAX_HISTORY", 3)

    store = MemoryStore(path=tmp_path / "user_memory.json")
    mgr = MemoryManager(store)
    mem = UserMemory(user_id="default")

    for i in range(10):
        mem = mgr.update_after_answer(
            mem,
            query=f"q{i}",
            topic=f"t{i}",
            intent=LearningIntent.casual_curiosity,
            mode=LearningMode.quick_explain,
            answer_summary=f"s{i}",
        )

    assert len(mem.history) == 3
    # Ensure it kept the last 3 topics
    assert mem.history[0].query == "q7"
    assert mem.history[-1].query == "q9"


def test_update_after_answer_caps_topics(monkeypatch, tmp_path: Path) -> None:
    import research_learning_agent.memory as mem_mod

    monkeypatch.setattr(mem_mod, "MAX_TOPICS", 4)

    store = MemoryStore(path=tmp_path / "user_memory.json")
    mgr = MemoryManager(store)
    mem = UserMemory(user_id="default")

    for i in range(10):
        mem = mgr.update_after_answer(
            mem,
            query=f"q{i}",
            topic=f"t{i}",
            intent=LearningIntent.casual_curiosity,
            mode=LearningMode.quick_explain,
            answer_summary="s",
        )

    assert len(mem.topics) == 4
    assert mem.topics[0] == "t6"
    assert mem.topics[-1] == "t9"


def test_build_prompt_context_includes_recent_topics_and_preferences(tmp_path: Path) -> None:
    """
    build_prompt_context includes recent topics and preferences
    """
    store = MemoryStore(path=tmp_path / "user_memory.json")
    mgr = MemoryManager(store)

    mem = UserMemory(user_id="default")
    mem.topics = ["rl basics", "transformers", "deep learning"]
    mem.preferences = UserPreferences(
        explanation_style=ExplanationStyle.examples,
        resource_preference=ResourcePreference.video,
        verbosity=Verbosity.concise,
    )

    ctx = mgr.build_prompt_context(mem)

    # Recent topics appear
    assert "rl basics" in ctx
    assert "transformers" in ctx
    assert "deep learning" in ctx

    # Preferences appear
    assert "explanation_style=examples" in ctx
    assert "resource_preference=video" in ctx
    assert "verbosity=concise" in ctx

    # Instruction to avoid repeating basics should be included
    assert "Avoid repeating basics" in ctx


def test_memory_manager_save_then_load_roundtrip(tmp_path: Path) -> None:
    store = MemoryStore(path=tmp_path / "user_memory.json")
    mgr = MemoryManager(store)

    mem = mgr.load(user_id="default")
    mem.topics = ["topicX"]
    mgr.save(mem)

    mem2 = mgr.load(user_id="default")
    assert mem2.topics == ["topicX"]
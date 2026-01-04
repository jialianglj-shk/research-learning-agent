from __future__ import annotations

from research_learning_agent.orchestrator import suggest_followups
from research_learning_agent.schemas import (
    UserMemory, UserPreferences,ResourcePreference, ExplanationStyle, Verbosity
)


def _mem(topics: list[str], resource_pref: str = ResourcePreference.video) -> UserMemory:
    mem = UserMemory(user_id="default")
    mem.topics = topics
    mem.preferences = UserPreferences(
        explanation_style=ExplanationStyle.balanced,
        resource_preference=resource_pref,
        verbosity=Verbosity.balanced,
    )
    return mem


def test_suggest_followups_returns_empty_without_memory() -> None:
    assert suggest_followups(None, "RL basics") == []


def test_suggest_followups_returns_empty_without_topics() -> None:
    mem = _mem([])
    assert suggest_followups(mem, "RL basics") == []


def test_suggest_followups_connects_to_previous_different_topic() -> None:
    mem = _mem(["rl basics", "transformers", "finetuning"])
    out = suggest_followups(mem, "backprop", max_items=2)
    assert len(out) > 1
    # should reference current and a previous topic
    assert "backprop" in out[0].lower()
    assert "finetuning" in out[0].lower() or "transformers" in out[0].lower()


def test_suggest_followups_skips_when_current_equals_last_topic() -> None:
    mem = _mem(["rl basics", "backprop"])
    out = suggest_followups(mem, "backprop", max_items=2)
    # should connect to rl basics (previous different)
    assert "rl basics" in out[0].lower()


def test_suggest_followups_respects_max_items() -> None:
    mem = _mem(["topic1", "topic2"], resource_pref=ResourcePreference.video)
    out = suggest_followups(mem, "topic3", max_items=1)
    assert len(out) == 1
    assert "topic2" in out[0].lower()


def test_suggest_followups_adds_video_preference_prompt() -> None:
    mem = _mem(["rl basics"], resource_pref=ResourcePreference.video)
    out = suggest_followups(mem, "gradient descent", max_items=2)
    assert any("video" in x.lower() for x in out)


def test_suggerst_followups_adds_text_preference_prompt() -> None:
    mem = _mem(["rl basics"], resource_pref=ResourcePreference.text)
    out = suggest_followups(mem, "gradient descent", max_items=2)
    assert any("docs" in x.lower() or "articles" in x.lower() for x in out)

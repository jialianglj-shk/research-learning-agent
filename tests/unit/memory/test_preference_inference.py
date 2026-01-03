from __future__ import annotations


from research_learning_agent.memory import infer_preferences
from research_learning_agent.schemas import (
    ExplanationStyle, ResourcePreference, Verbosity, UserMemory
)


def test_infer_preferences_examples_from_query() -> None:
    mem = UserMemory(user_id="default")

    infer_preferences(mem, "Can you explain backpropagation and give me examples?")
    assert mem.preferences.explanation_style == ExplanationStyle.examples


def test_infer_preferences_formulas_from_query_math_proof() -> None:
    mem = UserMemory(user_id="default")

    infer_preferences(mem, "Please derive the math and give a proof-level explanation.")
    assert mem.preferences.explanation_style == ExplanationStyle.formulas


def test_infer_preferences_video_from_query() -> None:
    mem = UserMemory(user_id="default")

    infer_preferences(mem, "Any good video or YouTube resources for ROS2?")
    assert mem.preferences.resource_preference == ResourcePreference.video


def test_infer_preferences_examples_case_insensitive() -> None:
    mem = UserMemory(user_id="default")
    infer_preferences(mem, "Give me EXAMPLES please.")
    assert mem.preferences.explanation_style == ExplanationStyle.examples


def test_infer_preferences_video_case_insensitive() -> None:
    mem = UserMemory(user_id="default")
    infer_preferences(mem, "Any YOUTUBE links?")
    assert mem.preferences.resource_preference == ResourcePreference.video


def test_negation_prevents_math() -> None:
    mem = UserMemory(user_id="default")
    infer_preferences(mem, "do not provide any detailed math, just give me the overview.")
    assert mem.preferences.explanation_style != ExplanationStyle.formulas


def test_negation_prevents_detailed() -> None:
    mem = UserMemory(user_id="default")
    infer_preferences(mem, "do not provide any detailed math, just give me the overview.")
    assert mem.preferences.verbosity != Verbosity.detailed

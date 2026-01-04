from __future__ import annotations


from research_learning_agent.orchestrator import infer_topic, _MAX_TOPIC_LEN
from research_learning_agent.schemas import Plan, PlanStep, StepType,LearningIntent


def make_plan(goal: str) -> Plan:
    """Helper to construct a minimal Plan instance."""
    return Plan(
        goal=goal,
        intent=LearningIntent.guided_study,
        steps=[PlanStep(step_id="s1", type=StepType.finalize, description="finalize")]
    )


def test_infer_topic_prefers_plan_goal_when_present() -> None:
    plan = make_plan("Learn basics of reinforcement learning")
    out = infer_topic(plan, "What is reinforcement learning?")
    assert out == "Learn basics of reinforcement learning"


def test_infer_topic_falls_back_to_cleaned_query_when_no_plan() -> None:
    out = infer_topic(None, "What is reinforcement learning?")
    assert out == "reinforcement learning"


def test_infer_topics_strips_common_prefixes_explain_definitions() -> None:
    out = infer_topic(None, "Explain backpropagation at a high level.")
    assert out == "backpropagation at a high level"


def test_infer_topic_strips_common_prefixes_help_me() -> None:
    out = infer_topic(None, "Help me understand transformers")
    assert out == "understand transformers"


def test_infer_topic_trims_punctuation_and_whitespace() -> None:
    out = infer_topic(None, '  What is "reinforcement learning"???   ')
    assert out == "reinforcement learning"


def test_infer_topic_rejects_overly_generic_goal_and_uses_query() -> None:
    # Goal is too generic; should fall back to cleaned query.
    plan = make_plan("Learn")
    out = infer_topic(plan, "What is reinforcement learning?")
    assert out == "reinforcement learning"


def test_infer_topic_truncates_long_topic() -> None:
    long_query = "What is " + ("very " * 100) + "long topic name?"
    out = infer_topic(None, long_query)
    assert isinstance(out, str)
    assert 1 <= len(out) <= _MAX_TOPIC_LEN
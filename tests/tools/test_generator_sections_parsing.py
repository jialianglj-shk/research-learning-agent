import pytest

from research_learning_agent.generator import Generator
from research_learning_agent.schemas import (
    AgentAnswer, AnswerSection, GenerationSpec, LearningMode, SourceItem, ToolResult, ToolType, 
    UserProfile, UserQuery, IntentResult, Plan, UserLevel, LearningIntent, PlanStep, StepType
    )
from research_learning_agent.llm_client import LLMMessage


class FakeLLM:
    """
    Fake LLM client that returns a canned response in the exact format
    the generator parser expects.
    """

    def __init__(self, text: str) -> None:
        self.text = text

    def chat(self, messages: list[LLMMessage]) -> str:
        return self.text


def _get_minimul_inputs():
    """Get minimum inputs for the generator."""
    profile = UserProfile(user_id="u1", background="x", level=UserLevel.beginner, goals="x")
    query = UserQuery(question="x")
    intent = IntentResult(intent=LearningIntent.casual_curiosity, confidence=0.9, rationale="x")
    plan = Plan(goal="x", intent="x", steps=[PlanStep(step_id="s1", type=StepType.explain, description="x")])
    tool_results = [
        ToolResult(
            tool=ToolType.web_search, 
            query="x", 
            results=[
                {"title": "x", "url": "x", "snippet": "x"}
            ],
            error=None
        )
    ]
    return profile, query, intent, plan, tool_results


def test_generator_parses_sections():
    canned = """
EXPLANATION:
Refinformce Learning (RL) is learning by trail and error to maximize reward.

BULLETS:
- Agent interacts with environment
- Learns a plicy to maximize reward

SECTIONS:
## Explanation
RL trains an agent using rewards and penalties.

## Analogy
Like training a dog with treats.

## Key Points
- Reward signal
- Exploration vs exploitation

## Next Steps
Try a simple Q-learning tutorial.
"""

    spec = GenerationSpec(
        mode=LearningMode.quick_explain, 
        required_sections=["Explanation", "Analogy", "Key Points", "Next Steps"],
        style_notes="Be concise and to the point.",
    )

    gen = Generator()
    gen.llm = FakeLLM(canned)

    profile, query, intent, plan, tool_results = _get_minimul_inputs()

    out = gen.generate(
        query=query, 
        profile=profile, 
        intent=intent, 
        plan=plan, 
        tool_results=tool_results, 
        spec=spec,
        force_final=True
    )

    assert out.sections, "Expected non-empty sections"
    titles = [s.title for s in out.sections]
    assert titles == ["Explanation", "Analogy", "Key Points", "Next Steps"]
    assert "RL trains an agent" in out.sections[0].content
    assert "Like training a dog with treats." in out.sections[1].content
    assert out.mode == LearningMode.quick_explain


def test_generator_fills_missing_requried_sections():
    """
    If the LLM fails to include a required section, the parser should still
    return the required section list (with empty content) so downstream code
    is stable.
    """
    canned = """
EXPLANATION:
x

BULLETS:
- A
- B

SECTIONS:
## Explanation
Explanation text

## Analogy
Analogy text
"""

    spec = GenerationSpec(
        mode=LearningMode.quick_explain, 
        required_sections=["Explanation", "Analogy", "Key Points", "Next Steps"],
        style_notes="Be concise and to the point.",
    )

    gen = Generator()
    gen.llm = FakeLLM(canned)

    profile, query, intent, plan, tool_results = _get_minimul_inputs()

    out = gen.generate(
        query=query, 
        profile=profile, 
        intent=intent, 
        plan=plan, 
        tool_results=tool_results, 
        spec=spec,
        force_final=True
    )

    assert out.sections, "Expected non-empty sections"
    titles = [s.title for s in out.sections]
    assert titles == ["Explanation", "Analogy", "Key Points", "Next Steps"]
    assert out.sections[0].content == "Explanation text"
    assert out.sections[1].content == "Analogy text"
    assert out.sections[2].content == ""
    assert out.sections[3].content == ""


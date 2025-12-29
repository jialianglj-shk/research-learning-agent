import pytest

from research_learning_agent.orchestrator import Orchestrator
from research_learning_agent.schemas import (
    LearningIntent, IntentResult, LearningMode, GenerationSpec, UserProfile, 
    AgentAnswer, AnswerSection, UserQuery, UserProfile, UserLevel, OrchestratorActionType
)


# What this test suite guarantees:
# 1. Orchestrator actually integrated pedagogy (not dead code)
# 2. Spec is passed to generator (correct wiring)
# 3. Answer contains the mode (traceable behavior)
#
# This test suit doesn't validate Pedagogy's internal logic (e.g. mode selection).


# --------------------------------
# Fakes / stubs
# --------------------------------

class FakeIntent:
    def __init__(self, intent: LearningIntent):
        self.intent = intent
    
    def classify(self, question, profile):
        return IntentResult(intent=self.intent, confidence=0.9, rationale="x")


class CapturePedagogy:
    """ Capture calls and return a deterministric mode/spec. """
    def __init__(self, mode: LearningMode):
        self.mode = mode
        self.choose_mode_called_with = None
        self.build_spec_called_with = None
    
    def choose_mode(self, intent: IntentResult, profile: UserProfile) -> LearningMode:
        self.choose_mode_called_with = (intent, profile)
        return self.mode

    def build_spec(self, mode: LearningMode, profile: UserProfile) -> GenerationSpec:
        self.build_spec_called_with = (mode, profile)
        return GenerationSpec(mode=mode, required_sections=["Explanation", "Next Steps"], style_notes="x")


class CaptureGenerator:
    """
    Captures the spec passed by orchestrator.
    Returns an AgentAnswer whose mode is set to spec.mode.
    """
    def __init__(self):
        self.last_spec = None

    def generate(self, *, query, profile, intent, plan, tool_results, spec, force_final=False):
        self.last_spec = spec
        return AgentAnswer(
            explanation="x",
            bullet_summary=["x"],
            mode=spec.mode,
            sections=[
                AnswerSection(title="Explanation", content="E"),
                AnswerSection(title="Next Steps", content="N"),
            ],
            sources=[]
        )

def _get_minimul_inputs():
    """Get minimum inputs for the generator."""
    profile = UserProfile(user_id="u1", background="x", level=UserLevel.beginner, goals="x")
    query = UserQuery(question="x")
    return profile, query


# --------------------------------
# Tests
# --------------------------------

def test_orchestrator_calls_pedagogy_and_passes_spec_to_generator():
    orch = Orchestrator()

    # Inject fakes
    orch.intent = FakeIntent(LearningIntent.guided_study)
    
    ped = CapturePedagogy(mode=LearningMode.guided_study)
    orch.pedagogy = ped

    gen = CaptureGenerator()
    orch.generator = gen

    profile, query = _get_minimul_inputs()
    res = orch.run(query=query, profile=profile, force_final=True)

    # Orchestrator returns a final answer
    assert res.action.kind == OrchestratorActionType.final
    assert res.answer is not None

    # 1) Pedagogy must be called
    assert ped.choose_mode_called_with is not None
    assert ped.build_spec_called_with is not None

    # 2) Generator must receive the spec built by Pedagogy
    assert gen.last_spec is not None
    assert gen.last_spec.mode == LearningMode.guided_study
    assert gen.last_spec.required_sections == ["Explanation", "Next Steps"]

    # 3) Mode stored correctly in AgentAnswer
    assert res.answer.mode == LearningMode.guided_study


@pytest.mark.parametrize(
    "learning_intent, expected_mode",
    [
        (LearningIntent.casual_curiosity, LearningMode.quick_explain),
        (LearningIntent.guided_study, LearningMode.guided_study),
        (LearningIntent.professional_research, LearningMode.deep_research),
        (LearningIntent.urgent_troubleshooting, LearningMode.fix_my_problem),
    ],
)
def test_orchestrator_mode_mapping_via_pedagogy(learning_intent, expected_mode):
    orch = Orchestrator()
    orch.intent = FakeIntent(intent=learning_intent)

    ped = CapturePedagogy(mode=expected_mode)
    orch.pedagogy = ped

    gen = CaptureGenerator()
    orch.generator = gen

    res = orch.run(
        query=UserQuery(question="x"),
        profile=UserProfile(user_id="u1", background="x", level=UserLevel.beginner, goals="x"),
        force_final=True
    )

    assert gen.last_spec.mode == expected_mode
    assert res.answer.mode == expected_mode


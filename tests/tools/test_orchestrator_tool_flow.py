from research_learning_agent.orchestrator import Orchestrator
from research_learning_agent.schemas import (
    AgentAnswer, IntentResult, OrchestratorAction, OrchestratorResult, OrchestratorActionType, 
    Plan, PlanStep, StepType,ToolCall, ToolResult, ToolType, UserProfile, UserQuery, SourceItem
)


class FakeIntent:
    def classify(self, question, profile):
        return IntentResult(
            intent="casual_curiosity", confidence=0.9, rationale="r", should_ask_clarifying_question=False
        )


class FakePlanner:
    def create_plan(self, question, profile, intent):
        return Plan(
            goal="g",
            intent=intent.intent,
            steps=[
                PlanStep(
                    step_id="s1",
                    type=StepType.research,
                    description="research",
                    tool_calls=[ToolCall(tool=ToolType.web_search, query="rl basics", top_k=2)],
                ),
                PlanStep(step_id="s2", type=StepType.finalize, description="finalize"),
            ],
        )


class FakeToolExecutor:
    def execute_step(self, step):
        return [
            ToolResult(
                tool=ToolType.web_search,
                query="rl basics",
                results=[{"title": "A","url": "https://a.com", "snippet": "A snippet"}],
            )
        ]


class CaptureGenerator:
    def __init__(self):
        self.last_tool_results = None

    def generate(self, *, query, profile, intent, plan, tool_results, force_final=False):
        self.last_tool_results = tool_results
        return AgentAnswer(
            explanation="ok",
            bullets=["b1", "b2"],
            sources=[SourceItem(title="A", url="https://a.com")],
            model_name="gpt-4.1-mini",
        )   


def test_orchestrator_executes_tools_and_passes_evidence():
    gen = CaptureGenerator()
    
    orch = Orchestrator()
    orch.intent=FakeIntent()
    orch.planner=FakePlanner()
    orch.tools=FakeToolExecutor()
    orch.generator=gen

    res = orch.run(
        UserQuery(question="what is rl"), 
        UserProfile(user_id="u1", background="b", level="beginner", goals="g"),
        force_final=True
    )

    assert res.action.kind == OrchestratorActionType.final
    assert res.tool_results is not None
    assert gen.last_tool_results is not None
    assert gen.last_tool_results[0].results[0]["url"] == "https://a.com"
    assert res.answer.sources[0].url == "https://a.com"

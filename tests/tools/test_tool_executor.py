from research_learning_agent.tool_executor import ToolExecutor
from research_learning_agent.schemas import PlanStep, ToolCall, ToolType
from research_learning_agent.tools.base import Tool
from research_learning_agent.tools.http import ToolHTTPError


class OKTool(Tool):
    def run(self, query: str, top_k: int = 5):
        return [{"title": "OK", "url": "https://ok.com", "snippet": "OK"}]


class FailTool(Tool):
    def run(self, query: str, top_k: int = 5):
        raise ToolHTTPError(error_type="network", message="test error")


class FakeRegistry:
    def __init__(self, tool):
        self.tool = tool
    
    def get(self, tool_type):
        return self.tool


def test_execute_step_success():
    exec_ = ToolExecutor(registry=FakeRegistry(OKTool()))
    step = PlanStep(step_id="s1", type="research", description="test", tool_calls=[
        ToolCall(tool=ToolType.web_search, query="test", top_k=5),
    ])

    out = exec_.execute_step(step)
    assert len(out) == 1
    assert out[0].error is None
    assert out[0].results[0]["url"] == "https://ok.com"


def test_execute_step_failure_returns_error_not_raises():
    exec_ = ToolExecutor(registry=FakeRegistry(FailTool()))
    step = PlanStep(step_id="s1", type="research", description="test", tool_calls=[
        ToolCall(tool=ToolType.web_search, query="test", top_k=5),
    ])

    out = exec_.execute_step(step)
    assert len(out) == 1
    assert out[0].error is not None
    assert out[0].error.error_type == "network"
    assert out[0].results == []

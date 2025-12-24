import pytest

from research_learning_agent.tool_registry import ToolRegistry
from research_learning_agent.schemas import ToolType
from research_learning_agent.tools.base import Tool
from research_learning_agent.tools.http import ToolHTTPError


class FailTool(Tool):
    def run(self, query: str, top_k: int = 5):
        raise ToolHTTPError(error_type="network", message="test error")


class OKTool(Tool):
    def __init__(self, marker: str):
        self.marker = marker

    def run(self, query: str, top_k: int = 5):
        return [{"title": self.marker, "url": "https://ok.com", "snippet": "ok"}]


def test_web_search_uses_fallback_when_primary_fails(monkeypatch):
    reg = ToolRegistry()

    # Replace the web_search tool wrapper with one using FailTool/OKTool
    # Easiest: directly set web_search to a srapper instance.
    from research_learning_agent.tool_registry import WebToolWithFallback

    reg.set_tool(
        ToolType.web_search,
        WebToolWithFallback(primary=FailTool(), fallback=OKTool(marker="fallback")),
    )

    tool = reg.get(ToolType.web_search)
    out = tool.run("test", 5)
    assert out[0]["title"] == "fallback"


def test_non_web_tools_donot_have_fallback(monkeypatch):
    reg = ToolRegistry()

    # Overwrite video tool with Failtool and ensure it raises (no fallback)
    reg.set_tool(ToolType.video_search, FailTool())

    tool = reg.get(ToolType.video_search)
    with pytest.raises(ToolHTTPError) as e:
        tool.run("test", 5)
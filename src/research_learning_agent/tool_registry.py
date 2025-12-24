from __future__ import annotations

from .schemas import ToolType
from .tools.base import Tool
from .tools.http import ToolHTTPError
from .tools.serper_web import SerperWebSearchTool
from .tools.youtube_data_api import YouTubeSearchTool
from .tools.ddg_instant_answer import DuckDuckGoInstantAnswerTool
from .logging_utils import get_logger

logger = get_logger("tool_registry")


class WebToolWithFallback(Tool):
    def __init__(self, primary: Tool, fallback: Tool) -> None:
        self.primary = primary
        self.fallback = fallback
    
    def run(self, query: str, top_k: int = 5) -> list[dict[str, str]]:
        try:
            return self.primary.run(query, top_k)
        except ToolHTTPError as e:
            logger.warning("web_search primary failed (%s): %s", e.error_type, e)
            logger.info("web_search using fallback: %s", self.fallback.__class__.__name__)
            return self.fallback.run(query, top_k)


class ToolRegistry:
    def __init__(self) -> None:
        serper = SerperWebSearchTool()
        ddg = DuckDuckGoInstantAnswerTool()

        self._tools: dict[ToolType, Tool] = {
            ToolType.web_search: WebToolWithFallback(serper, ddg),
            ToolType.docs_search: serper,
            ToolType.video_search: YouTubeSearchTool(),
        }

    def get(self, tool_type: ToolType) -> Tool:
        return self._tools[tool_type]
    
    # test hooks
    def set_tool(self, tool_type: ToolType, tool: Tool) -> None:
        self._tools[tool_type] = tool
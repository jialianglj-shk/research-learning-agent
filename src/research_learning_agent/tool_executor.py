from __future__ import annotations

from .schemas import PlanStep, ToolCall, ToolError, ToolResult
from .tool_registry import ToolRegistry
from .tools.http import ToolHTTPError
from .logging_utils import get_logger

logger = get_logger("tool_executor")


class ToolExecutor:
    def __init__(self, registry: ToolRegistry | None = None) -> None:
        self.registry = registry or ToolRegistry()
    
    def execute_step(self, step: PlanStep) -> list[ToolResult]:
        results: list[ToolResult] = []
        if not step.tool_calls:
            return results
        
        for call in step.tool_calls:
            results.append(self._execute_tool(call))
        return results

    def _execute_tool(self, call: ToolCall) -> ToolResult:
        tool = self.registry.get(call.tool)
        logger.info("tool_call tool=%s query=%r top_k=%d", call.tool.value, call.query, call.top_k)
        try:
            out = tool.run(call.query, call.top_k)
            # normalize: ensure list[dict] with required keys
            out_norm = []
            for item in out or []:
                if not isinstance(item, dict):
                    continue
                title = str(item.get("title", "")).strip()
                url = str(item.get("url", "")).strip()
                snippet = str(item.get("snippet", "")).strip()
                if url:
                    out_norm.append({"title": title, "url": url, "snippet": snippet})
            return ToolResult(tool=call.tool, query=call.query, results=out_norm)

        except ToolHTTPError as e:
            logger.warning("tool_failed tool=%s err_type=%s msg=%s", call.tool.value, e.error_type, e)
            return ToolResult(
                tool=call.tool,
                query=call.query,
                results=[],
                error=ToolError(
                    tool=call.tool,
                    query=call.query,
                    error_type=e.error_type,
                    message=str(e),
                ),
            )

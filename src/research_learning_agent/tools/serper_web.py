from __future__ import annotations

import os
from typing import Any

from .base import Tool
from .http import ToolHTTPError, request_json
from ..logging_utils import get_logger

logger = get_logger("tools.serper_web")


SERPER_SEARCH_URL = "https://google.serper.dev/search"


def _get_api_key() -> str:
    key = os.getenv("SERPER_API_KEY", "").strip()
    if not key:
        raise ToolHTTPError(
            error_type="config",
            message="Missing SERPER_API_KEY environment variable",
            url=SERPER_SEARCH_URL,
        )
    return key


def _normalize_item(item: dict[str, Any]) -> dict[str, str] | None:
    """
    Normalize a Serper organic result to {title, url, snippet}
    Returns None if the item is missing required fields.
    """
    title = (item.get("title") or "").strip()
    url = (item.get("link") or "").strip()
    snippet = (item.get("snippet") or "").strip()

    if not url:
        return None
    
    # title/snippet might be missing; keep them but avoid None
    return {
        "title": title if title else url,
        "url": url,
        "snippet": snippet,
    }


class SerperWebSearchTool(Tool):
    """
    Web search tool backed by Serper (Google Search API).

    Output: list of dicts with keys:
      - title
      - url
      - snippet
    """

    def run(self, query: str, top_k: int = 5) -> list[dict[str, str]]:
        q = (query or "").strip()
        if not q:
            return []
        
        k = max(1, min(int(top_k), 10))  # keep it limited for Day 4

        api_key = _get_api_key()
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
        }
        body = {
            "q": q,
            "num": k,
        }

        logger.debug("Serper search query=%r top_k=%d", q, k)

        data = request_json(
            "POST",
            SERPER_SEARCH_URL,
            headers=headers,
            json_body=body,
        )

        organic = data.get("organic") or []
        results: list[dict[str, str]] = []
        for item in organic:
            if len(results) >= k:
                break
            if not isinstance(item, dict):
                continue
            norm = _normalize_item(item)
            if norm:
                results.append(norm)

        # Some queries might produce knowledgeGraph/answerBox; optional enrichment:
        # If no organic results, try to emit a single "best effort" result from answerBox.
        if not results:
            answer_box = data.get("answerBox") or {}
            if isinstance(answer_box, dict):
                title = (answer_box.get("title") or answer_box.get("heading") or "").strip()
                snippet = (answer_box.get("answer") or answer_box.get("snippet") or "").strip()
                url = (answer_box.get("link") or "").strip()
                if url:
                    results.append(
                        {
                            "title": title if title else url,
                            "url": url,
                            "snippet": snippet,
                        }
                    )

        return results
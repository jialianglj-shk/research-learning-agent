from __future__ import annotations

from typing import Any
from urllib.parse import quote_plus

from .base import Tool
from .http import request_json
from ..logging_utils import get_logger

logger = get_logger("tools.ddg_instant_answer")

DDG_IA_URL = "https://api.duckduckgo.com/"


def _normalized_result(title: str, url: str, snippet: str) -> dict[str, str] | None:
    title = (title or "").strip()
    url = (url or "").strip()
    snippet = (snippet or "").strip()
    if not url:
        return None
    return {"title": title if title else url, "url": url, "snippet": snippet}


def _extract_related_topics(node: Any, out: list[dict[str, str]], limit: int) -> None:
    """
    DuckDuckGo IA returns RelatedTopics as a list of:
      - dict with 'Text' and 'FirstURL'
      - or dict with 'Topics': [ ... ] nested
    """
    if len(out) >= limit:
        return
    
    if isinstance(node, list):
        for item in node:
            _extract_related_topics(item, out, limit)
            if len(out) >= limit:
                return
        return
    
    if not isinstance(node, dict):
        return
    
    # Nested topics
    topics = node.get("Topics")
    if topics:
        _extract_related_topics(topics, out, limit)
        return
    
    text = node.get("Text") or ""
    url = node.get("FirstURL") or ""
    norm = _normalized_result(text, url, text)
    if norm:
        out.append(norm)


class DuckDuckGoInstantAnswerTool(Tool):
    """
    Fallback web tool using DuckDuckGo Instant Answer API (no key).
    Returns best-effort results (summary + related topics).
    """

    def run(self, query: str, top_k: int = 5) -> list[dict[str, str]]:
        q = (query or "").strip()
        if not q:
            return []
        
        k = max(1, min(int(top_k), 10))

        params = {
            "q": q,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 0,
        }

        logger.debug("DDG IA query=%r top_k=%d", q, k)

        data = request_json("GET", DDG_IA_URL, params=params, headers={"Accept": "application/json"})

        results: list[dict[str, str]] = []

        # Abstract (often present for well-known topics)
        abstract_url = (data.get("AbstractURL") or "").strip()
        abstract_text = (data.get("AbstractText") or "").strip()
        heading = (data.get("Heading") or "").strip()
        if abstract_url:
            norm = _normalized_result(heading or q, abstract_url, abstract_text)
            if norm:
                results.append(norm)
        
        # Related topics
        related = data.get("RelatedTopics")
        if related and len(results) < k:
            _extract_related_topics(related, results, k)
        
        return results[:k]
from __future__ import annotations

import os
from typing import Any

from .base import Tool
from .http import request_json, ToolHTTPError
from ..logging_utils import get_logger

logger = get_logger("tools.youtube_data_api")

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def _get_api_key() -> str:
    key = os.getenv("YOUTUBE_API_KEY")
    if not key:
        raise ToolHTTPError(
            error_type="config",
            message="Missing YOUTUBE_API_KEY environment variable",
            url=YOUTUBE_SEARCH_URL,
        )
    return key


def _video_url(video_id: str) -> str:
    return f"https://www.youtube.com/watch?v={video_id}"


def _normalize_item(item: dict[str, Any]) -> dict[str, str] | None:
    """
    Normalize a YouTube search item to {title, url, snippet}
    Returns None if required fields are missing.
    """
    if not isinstance(item, dict):
        return None
    
    id_obj = item.get("id") or {}
    if not isinstance(id_obj, dict):
        return None
    
    video_id = (id_obj.get("videoId") or "").strip()
    if not video_id:
        # Sometimes search can return channels/playlists if type is wrong; we filter them out.
        return None
    
    snippet_obj = item.get("snippet") or {}
    if not isinstance(snippet_obj, dict):
        snippet_obj = {}
    
    title = (snippet_obj.get("title") or "").strip()
    desc = (snippet_obj.get("description") or "").strip()

    url = _video_url(video_id)
    return {
        "title": title if title else url,
        "url": url,
        "snippet": desc,
    }


class YouTubeSearchTool(Tool):
    """
    Video search tool backed by YouTube Data API v3 (search.list).

    Output: list of dicts with keys:
        - title
        - url
        - snippet
    """

    def run(self, query: str, top_k: int = 5) -> list[dict[str, str]]:
        q = (query or "").strip()
        if not q:
            return []
        
        k = max(1, min(int(top_k), 25))  # YouTube maxResults max is 50; keep Day 4 conservative.

        api_key = _get_api_key()

        params = {
            "part": "snippet",
            "q": q,
            "type": "video",
            "maxResults": k,
            "safeSearch": "moderate",
            "key": api_key,
        }

        logger.debug("YouTube search query=%r top_k=%d", q, k)

        data = request_json(
            "GET",
            YOUTUBE_SEARCH_URL,
            params=params,
            headers={"Accept": "application/json"},
        )

        items = data.get("items") or []
        results: list[dict[str, str]] = []
        for item in items:
            if len(results) >= k:
                break
            norm = _normalize_item(item)
            if norm:
                results.append(norm)

        return results
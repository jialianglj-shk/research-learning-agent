from __future__ import annotations

import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _slugify(name: str, *, max_len: int = 60) -> str:
    """Slugify a name to a valid filename."""
    name = (name or "").strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    name = name.strip("-")
    if not name:
        name = "session"
    return name[:max_len].strip("-")


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _flatten_assistant_content(content: Any) -> str:
    """
    st.session_state.messages stores assistant content as either:
    - str
    - list[UIChatHistoryItem] where each item has (rendiner_function_name, message_md)

    For workflow export, flatten list items into a single markdown string.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    
    # list of objects/dicts with message_md
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            # support both pydantic model and dict-like
            md = getattr(item, "message_md", None)
            if md is None and isinstance(item, dict):
                md = item.get("message_md")
            if md:
                parts.append(str(md).strip())
        return "\n\n".join([p for p in parts if p])
    
    # fallback
    return str(content)


def build_workflow_record(
    *,
    title: str,
    session_id: str,
    messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Build the workflow JSON record.

    messages is expected to be st.session_state.messages:
        [{"role": "user"/"assistant", "content": str|list[UIChatHistoryItem]}, ...]
    """
    normalized_msgs: list[dict[str, str]] = []
    for m in messages:
        role = str(m.get("role", "")).strip()
        content = m.get("content")
        if role == "assistant":
            text = _flatten_assistant_content(content)
        else:
            text = str(content) if content is not None else ""
        
        text = text.strip()
        if not role or not text:
            continue

        normalized_msgs.append({"role": role, "content": text})

    return {
        "title": title.strip() or "Untitled session",
        "session_id": session_id,
        "saved_at_utc": _now_utc_iso(),
        "messages": normalized_msgs,
    }


def save_workflow(
    *,
    workflows_dir: Path,
    title: str,
    session_id: str,
    messages: list[dict[str, Any]],
) -> Path:
    """
    Save the workflow record to workflows_dir/<slug>-<short_session>.json
    Returns the saved path.
    """
    workflows_dir.mkdir(parents=True, exist_ok=True)

    slug = _slugify(title)
    short_sid = (session_id or "session")[:8]
    filename = f"{slug}-{short_sid}.json"
    path = workflows_dir / filename

    record = build_workflow_record(title=title, session_id=session_id, messages=messages)
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    return path
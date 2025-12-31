from __future__ import annotations

import json

from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from .logging_utils import get_logger

logger = get_logger("Telemetry")


DATA_DIR = Path("data")
INTENT_LOG_PATH = DATA_DIR / "intent_events.jsonl"


def log_intent_event(event: dict[str, Any]) -> None:
    """Log an intent event to the telemetry file."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        event = dict[str, Any](event)
        event["ts"] = datetime.now(timezone.utc).isoformat()
        INTENT_LOG_PATH.write_text("", encoding="utf-8") if not INTENT_LOG_PATH.exists() else None
        with INTENT_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        logger.error(f"Failed to log intent event: {e}")
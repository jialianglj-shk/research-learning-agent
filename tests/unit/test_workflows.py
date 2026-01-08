from __future__ import annotations

import json
from pathlib import Path

from research_learning_agent.workflows import build_workflow_record, save_workflow


class FakeItem:
    def __init__(self, md: str) -> None:
        self.message_md = md
        self.render_function_name = "st.markdown"


def test_build_workflow_record_flattens_assistant_list() -> None:
    msgs = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": [FakeItem("World"), FakeItem("How are you?")]},
    ]
    rec = build_workflow_record(title="Test", session_id="123", messages=msgs)
    assert rec["messages"][1]["content"] == "World\n\nHow are you?"


def test_save_workflow_writes_file(tmp_path: Path) -> None:
    msgs = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "World"}]
    p = save_workflow(workflows_dir=tmp_path, title="Test", session_id="123", messages=msgs)
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["title"] == "Test"
    assert data["session_id"] == "123"
    assert len(data["messages"]) == 2


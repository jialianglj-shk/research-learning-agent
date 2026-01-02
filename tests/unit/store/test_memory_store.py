from __future__ import annotations

from pathlib import Path

from research_learning_agent.schemas import UserMemory
from research_learning_agent.store.memory_store import MemoryStore


def test_memory_store_load_missing_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "user_memory.json"
    store = MemoryStore(path=path)

    out = store.load(user_id="default")
    assert out is None


def test_memory_store_save_then_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "user_memory.json"
    store = MemoryStore(path=path)

    mem = UserMemory(user_id="default")
    mem.topics = ["rl basics"]
    mem.last_topic = "rl basics"

    store.save(mem)
    assert path.exists()

    loaded = store.load(user_id="default")
    assert loaded is not None
    assert isinstance(loaded, UserMemory)
    assert loaded.user_id == "default"
    assert loaded.topics == ["rl basics"]
    assert loaded.last_topic == "rl basics"


def test_memory_store_overwrites_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "user_memory.json"
    store = MemoryStore(path=path)

    mem1 = UserMemory(user_id="default")
    mem1.topics = ["topic1"]
    store.save(mem1)

    mem2 = UserMemory(user_id="default")
    mem2.topics = ["topic2", "topic3"]
    store.save(mem2)

    loaded = store.load(user_id="default")
    assert loaded is not None
    assert loaded.topics == ["topic2", "topic3"]
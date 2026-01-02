import json
from pathlib import Path
from re import S

from research_learning_agent.schemas import UserMemory


DATA_DIR = Path("data")
MEMORY_PATH = DATA_DIR / "user_memory.json"


class MemoryStore:
    def __init__(self, path: Path = MEMORY_PATH) -> None:
        self.path = path
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def load(self, user_id: str = "default") -> UserMemory | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        # if later support multiple users, key by user_id
        return UserMemory.model_validate(data)
    
    def save(self, mem: UserMemory) -> None:
        self.path.write_text(mem.model_dump_json(indent=2), encoding="utf-8")
        
import json
from pathlib import Path

from .schemas import UserProfile

DATA_DIR = Path("data")
PROFILE_PATH = DATA_DIR / "user_profile.json"


class ProfileStore:
    def __init__(self, path: Path = PROFILE_PATH) -> None:
        self.path = path
        DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    def load(self) -> UserProfile | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return UserProfile.model_validate(data)
    
    def save(self, profile: UserProfile) -> None:
        self.path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")

from abc import ABC, abstractmethod
from typing import Any


class Tool(ABC):
    @abstractmethod
    def run(self, query: str, top_k: int) -> list[dict[str, Any]]:
        raise NotImplemented
from dataclasses import dataclass
import os

@dataclass
class LLMConfig:
    model_name: str
    temperature: float = 0.2
    max_tokens: int = 800

def get_llm_config() -> LLMConfig:
    return LLMConfig(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.2")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "800")),
    )
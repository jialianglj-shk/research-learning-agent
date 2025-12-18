import os

from openai import OpenAI

from .schemas import LLMMessage
from .config import get_llm_config


class LLMClient:
    """Thin wrapper around the OpenAI chat completions API."""
    
    def __init__(self) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=api_key)
        self.config = get_llm_config()
    
    def chat(self, messages: list[LLMMessage]) -> str:
        """Send a list of messages to the LLM and return the the assistant's reply text."""
        completion = self.client.chat.completions.create(
            model=self.config.model_name,
            messages=[m.model_dump() for m in messages],
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )
        return completion.choices[0].message.content


    
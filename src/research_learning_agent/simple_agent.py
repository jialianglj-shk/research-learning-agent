from .schemas import UserQuery, AgentAnswer, LLMMessage
from .llm_client import LLMClient
from .config import get_llm_config

SYSTEM_PROMPT = """
You are a concise, clear research and learning assistant.

Given a user's question, respond in TWO parts:

1. A short explanation (2-5 paragraphs) that teaches the concept clearly.
2. 3-7 bullet points summarizing the key takeaways.

Respond in the following format exactly:

EXPLANATION:
<your explanation here>

BULLETS:
- point 1
- point 2
- ...
"""

class SimpleAgent:
    """Week-1 baseline agent: one LLM call, simple parsing."""

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.config = get_llm_config()
    
    def answer(self, query: UserQuery) -> AgentAnswer:
        """Generate an answer to the user's question."""
        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=SYSTEM_PROMPT),
            LLMMessage(role="user", content=f"Question: {query.question}"),
        ]

        raw_text = self.llm.chat(messages)
        explanation, bullets = self._parse_response(raw_text)

        return AgentAnswer(
            explanation=explanation,
            bullet_summary=bullets,
            model_name=self.config.model_name,
        )

    @staticmethod
    def _parse_response(raw_text: str) -> tuple[str, list[str]]:
        """Parse the raw text response into an explanation and bullet points."""
        explanation = raw_text
        bullets: list[str] = []

        lower = raw_text.lower()
        if "explanation:" in lower and "bullets:" in lower:
            exp_idx = lower.index("explanation:")
            bul_idx = lower.index("bullets:")

            explanation = raw_text[exp_idx + len("explanation:") : bul_idx].strip()
            bullet_block = raw_text[bul_idx + len("bullets:") :].strip()

            for line in bullet_block.splitlines():
                stripped = line.strip()
                if stripped.startswith("-"):
                    bullets.append(stripped.lstrip("-").strip())

        if not bullets:
            bullets = ["Summary not clearly formatted; improve prompt or parsing later."]
        
        return explanation, bullets

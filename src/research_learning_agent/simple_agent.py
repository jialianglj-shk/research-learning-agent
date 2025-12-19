from .schemas import UserQuery, AgentAnswer, LLMMessage, UserProfile, IntentResult
from .llm_client import LLMClient
from .config import get_llm_config


def build_system_prompt(profile: UserProfile, intent_result: IntentResult) -> str:
    return f"""
You are a concise, clear research and learning assistant.

User profile:
- background: {profile.background}
- Level: {profile.level}
- Goals: {profile.goals}
- Preferred output: {profile.preferred_output}

Current intent classification:
- Intent: {intent_result.intent}
- Suggested output: {intent_result.suggested_output}

Adapt your response style accordingly:
- casual_curiosity: friendly, intuitive, short
- guided_study: structured, step-by-step, include a mini learning path
- professional_research: precise, include terminology and clear framing
- urgent_troubleshooting: actionable steps first, then brief explanation

Return in this exact format:

EXPLANATION:
<...>

BULLETS:
- ...
"""

class SimpleAgent:
    """Week-1 baseline agent: one LLM call, simple parsing."""

    def __init__(self) -> None:
        self.llm = LLMClient()
        self.config = get_llm_config()
    
    def answer(self, query: UserQuery, profile: UserProfile, intent: IntentResult) -> AgentAnswer:
        """Generate an answer to the user's question."""
        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=build_system_prompt(profile=profile, intent_result=intent)),
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

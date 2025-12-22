from .schemas import UserQuery, AgentAnswer, LLMMessage, UserProfile, IntentResult, Plan
from .llm_client import LLMClient
from .logging_utils import get_logger


logger = get_logger("Generator")



def build_generator_prompt(profile: UserProfile, intent_result: IntentResult, plan: Plan, force_final: bool) -> str:
    forced_instruction = ""
    if force_final:
        forced_instruction = """
IMPORTANT:
The user quedstion may still be ambiguous.
YOU MUST:
1) State your assumptioms explicitly (bullet list).
2) Provide the best possible answer under those assumptions.
3) End with ONE follow-up question to confirm or refine assumptions.    
"""

    return f"""
You are a learning/research assistant.

User profile:
- background: {profile.background}
- Level: {profile.level}
- Goals: {profile.goals}
- Preferred output: {profile.preferred_output}

Intent:
- Intent: {intent_result.intent}
- Suggested output: {intent_result.suggested_output}

Plan:
{plan.model_dump_json(indent=2)}

{forced_instruction}

Follow the plan. If a clarify step exists and missing info, ask ONE clarifying question first.
Otherwise generate the final response.

Return in this exact format:

EXPLANATION:
<...>

BULLETS:
- ...
"""

class Generator:
    def __init__(self) -> None:
        self.llm = LLMClient()
    
    def generate(
        self, query: UserQuery, profile: UserProfile, intent: IntentResult, 
        plan: Plan, force_final: bool = False
    ) -> AgentAnswer:
        system_prompt = build_generator_prompt(profile, intent, plan, force_final)
        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=query.question),
        ]

        raw = self.llm.chat(messages)
        logger.debug("Raw generator output:\n%s", raw)

        explanation, bullets = self._parse_response(raw)

        return AgentAnswer(
            explanation=explanation,
            bullet_summary=bullets,
            model_name=None,
        )

    # Keep parser for now, Day 5+ can move to JSON structured output
    @staticmethod
    def _parse_response(raw_text: str) -> tuple[str, list[str]]:
        lower = raw_text.lower()
        explanation = raw_text
        bullets: list[str] = []

        
        if "explanation:" in lower and "bullets:" in lower:
            exp_idx = lower.index("explanation:")
            bul_idx = lower.index("bullets:")

            explanation = raw_text[exp_idx + len("explanation:") : bul_idx].strip()
            bullet_block = raw_text[bul_idx + len("bullets:") :].strip()

            for line in bullet_block.splitlines():
                s = line.strip()
                if s.startswith("-"):
                    bullets.append(s.lstrip("-").strip())

        if not bullets:
            bullets = ["Summary not clearly formatted; improve prompt/parsing or add JSON output later."]
        
        return explanation, bullets

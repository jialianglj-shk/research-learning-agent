from .schemas import UserQuery, AgentAnswer, LLMMessage, UserProfile, IntentResult, Plan, ToolResult, SourceItem
from .llm_client import LLMClient
from .logging_utils import get_logger


logger = get_logger("Generator")



def build_generator_prompt(
    profile: UserProfile, intent_result: IntentResult, plan: Plan, evidence: str, force_final: bool
) -> str:
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

Evidence you may use (URLs provided)
{evidence}

Rules:
- Use evidence when relevant.
- Do NOT invent sources.
- If evidence is empty/unavailable, anser from general knowledge and say so briefly.
- End with a SOURCES section listing the URLs you actually used.

Return in this exact format:

EXPLANATION:
<...>

BULLETS:
- ...

SOURCES:
- ...
"""

class Generator:
    def __init__(self) -> None:
        self.llm = LLMClient()
    
    def generate(
        self, query: UserQuery, profile: UserProfile, intent: IntentResult, 
        plan: Plan, tool_results: list[ToolResult], *, force_final: bool = False
    ) -> AgentAnswer:
        evidence = self._format_evidence(tool_results)

        system_prompt = build_generator_prompt(profile, intent, plan, evidence, force_final)

        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=query.question),
        ]

        raw = self.llm.chat(messages)
        logger.debug("Raw generator output:\n%s", raw)

        explanation, bullets = self._parse_response(raw)
        sources = self._build_sources(tool_results)

        return AgentAnswer(
            explanation=explanation,
            bullet_summary=bullets,
            model_name=None,
            sources=sources,
        )

    @staticmethod
    def _format_evidence(tool_results: list[ToolResult], max_items_per_tool: int = 5) -> str:
        lines = []
        for tr in tool_results:
            if tr.error:
                lines.append(f"- {tr.tool} FAILED for query={tr.query!r}: {tr.error.error_type}")
                continue
            for r in (tr.results or [])[:max_items_per_tool]:
                lines.append(f"- [{tr.tool}] {r.get('title')} | {r.get('url')}")
        return "\n".join(lines) if lines else "(no external evidence)"
    

    @staticmethod
    def _build_sources(tool_results: list[ToolResult], max_sources: int = 5) -> list[SourceItem]:
        seen = set()
        out = []
        for tr in tool_results:
            if tr.error:
                continue
            for r in tr.results:
                url = r.get("url", "").strip()
                title = r.get("title", "").strip()
                if url and url not in seen:
                    out.append(SourceItem(title=title, url=url))
                    seen.add(url)
                if len(out) >= max_sources:
                    return out
        return out

    # Keep parser for now, Day 5+ can move to JSON structured output
    @staticmethod
    def _parse_response(raw_text: str) -> tuple[str, list[str]]:
        lower = raw_text.lower()
        explanation = raw_text
        bullets: list[str] = []

        
        if "explanation:" in lower and "bullets:" in lower:
            exp_idx = lower.index("explanation:")
            bul_idx = lower.index("bullets:")
            src_idx = lower.index("sources:")

            explanation = raw_text[exp_idx + len("explanation:") : bul_idx].strip()
            bullet_block = raw_text[bul_idx + len("bullets:") : src_idx].strip()

            for line in bullet_block.splitlines():
                s = line.strip()
                if s.startswith("-"):
                    bullets.append(s.lstrip("-").strip())

        if not bullets:
            bullets = ["Summary not clearly formatted; improve prompt/parsing or add JSON output later."]
        
        return explanation, bullets

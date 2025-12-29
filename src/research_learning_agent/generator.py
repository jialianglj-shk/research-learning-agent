import re

from .schemas import (
    UserQuery, AgentAnswer, LLMMessage, UserProfile, IntentResult, Plan, ToolResult, 
    SourceItem, GenerationSpec, AnswerSection
)
from .llm_client import LLMClient
from .logging_utils import get_logger


logger = get_logger("Generator")



def build_generator_prompt(
    profile: UserProfile, intent_result: IntentResult, plan: Plan, evidence: str, 
    sections_list: list[str], force_final: bool
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

Required section titles:
{sections_list}

Rules:
- Use evidence when relevant.
- Do NOT invent sources.
- If evidence is empty/unavailable, anser from general knowledge and say so briefly.
- Do not add extra section titles beyond the required sections list.
- End with a SOURCES section listing the URLs you actually used.

Return in this exact format:

EXPLANATION:
<...>

BULLETS:
- ...

SECTIONS:
## <Section Title>
<Section Contents>

SOURCES:
- ...
"""

class Generator:
    def __init__(self) -> None:
        self.llm = LLMClient()
    
    def generate(
        self, query: UserQuery, profile: UserProfile, intent: IntentResult, 
        plan: Plan, tool_results: list[ToolResult], spec: GenerationSpec,
        *, force_final: bool = False
    ) -> AgentAnswer:
        evidence = self._format_evidence(tool_results)

        system_prompt = build_generator_prompt(
            profile, intent, plan, evidence, spec.required_sections, force_final
        )

        messages: list[LLMMessage] = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=query.question),
        ]

        raw = self.llm.chat(messages)
        logger.debug("Raw generator output:\n%s", raw)

        explanation, bullets = self._parse_response(raw)
        sections = self._parse_sections(raw, spec.required_sections)
        sources = self._build_sources(tool_results)

        return AgentAnswer(
            explanation=explanation,
            bullet_summary=bullets,
            model_name=None,
            sections=sections,
            mode=spec.mode,
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

    @staticmethod
    def _parse_sections(text: str, required_sections: list[str]) -> list[AnswerSection]:
        # Find "SECTIONS:" then parse "## Title" blocks
        # enforce only required titles, fill missing with empty content if needed.
        
        # 1. Locate the "SECTIONS:" portion
        # First split by "SECTIONS:" and take the text following it.
        # Then Split by "SOURCES:" to ensure we don't accidentially parse the sources list
        if "SECTIONS:" not in text:
            return [AnswerSection(title=t, content="") for t in required_sections]

        sections_block = text.split("SECTIONS:")[1].split("SOURCES:")[0].strip()

        # 2. Extract title and content blocks using Regex
        # Pattern explanation:
        # ##\s*(.*?)\n  -> Matches "##", optional whitespace, captures the title until the newline
        # (.*?)         -> Capture the content (non-greedy)
        # (?=\n##|$)    -> Lookahead: stops when it hits a new "##" or the end of the string
        pattern = r"##\s*(.*?)\n(.*?)(?=\n##|$)"
        matches = re.findall(pattern, sections_block, re.DOTALL)

        # 3. Map findings into a dictionary for easy lookup (stripping whitespace)
        parsed_map = {title.strip(): content.strip() for title, content in matches}

        final_sections = []
        for section_title in required_sections:
            # If the title exists in the LLM output, use it; otherwise, use and empty string
            content = parsed_map.get(section_title, "")
            final_sections.append(AnswerSection(title=section_title, content=content))
        
        return final_sections
    
    # Keep parser for now, Day 5+ can move to JSON structured output
    @staticmethod
    def _parse_response(raw_text: str) -> tuple[str, list[str]]:
        lower = raw_text.lower()
        explanation = raw_text
        bullets: list[str] = []

        
        if "explanation:" in lower and "bullets:" in lower:
            exp_idx = lower.index("explanation:")
            bul_idx = lower.index("bullets:")
            sec_idx = lower.index("sections:")

            explanation = raw_text[exp_idx + len("explanation:") : bul_idx].strip()
            bullet_block = raw_text[bul_idx + len("bullets:") : sec_idx].strip()

            for line in bullet_block.splitlines():
                s = line.strip()
                if s.startswith("-"):
                    bullets.append(s.lstrip("-").strip())

        if not bullets:
            bullets = ["Summary not clearly formatted; improve prompt/parsing or add JSON output later."]
        
        return explanation, bullets

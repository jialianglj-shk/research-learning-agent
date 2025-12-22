import json
import re
from .llm_client import LLMClient
from .schemas import LLMMessage, UserProfile, IntentResult, Plan
from .prompts import PLANNER_SYSTEM_PROMPT
from .logging_utils import get_logger


logger = get_logger("Planner")


class Planner:
    def __init__(self) -> None:
        self.llm = LLMClient()
    
    def create_plan(self, question: str, profile: UserProfile, intent: IntentResult) -> Plan:
        user_context=f"""
User background: {profile.background}
User level: {profile.level}
User goals: {profile.goals}
Preferred output: {profile.preferred_output}
"""

        intent_context=f"""
Intent: {intent.intent}
Confidence: {intent.confidence}
Rationale: {intent.rationale}
Suggested output: {intent.suggested_output}
"""

        messages = [
            LLMMessage(role="system", content=PLANNER_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_context + "\n" + intent_context + "\nUser question:" + question),
        ]

        raw = self.llm.chat(messages)
        logger.debug("Raw planner output:\n%s", raw)

        data = self._extract_json(raw)
        plan = Plan.model_validate(data)

        logger.debug("Validated plan: \n%s", plan.model_dump())
        return plan
    
    @staticmethod
    def _extract_json(text: str) -> dict:
        """
        Parses an LLM response to find and extract a single valid JSON object or list.
        """
        # 1. Try to find content inside Markdown code blocks
        code_block_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
        match = re.search(code_block_pattern, text)
        
        if match:
            json_str = match.group(1).strip()
        else:
            # 2. If no code blocks, look for the first '{' or '[' and the last '}' or ']'
            # This handles cases where the LLM provides raw text.
            json_pattern = r"(\{[\s\S]*\}|\[[\s\S]*\])"
            match = re.search(json_pattern, text)
            if match:
                json_str = match.group(1).strip()
            else:
                return None # No JSON-like structure found

        # 3. Attempt to parse the string
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parsing Error: {e}")
            return None
        
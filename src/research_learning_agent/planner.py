import json
import re
from .llm_client import LLMClient
from .schemas import LLMMessage, UserProfile, IntentResult, Plan
from .prompts import PLANNER_SYSTEM_PROMPT
from .utils.json_extract import extract_json
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

        data = extract_json(raw)
        plan = Plan.model_validate(data)

        logger.debug("Validated plan: \n%s", plan.model_dump())
        return plan

        
import json

from .llm_client import LLMClient
from .schemas import IntentResult, LLMMessage, UserProfile
from .prompts import INTENT_SYSTEM_PROMPT
from .logging_utils import get_logger


logger = get_logger("IntentClassifier")


class IntentClassifier:
    def __init__(self) -> None:
        self.llm = LLMClient()
    
    def classify(self, user_question: str, profile: UserProfile) -> IntentResult:
        # INclude profile context lightly to improve classification
        user_context = f"""
User background: {profile.background}
User level: {profile.level}
User goals: {profile.goals}
"""

        messages = [
            LLMMessage(role="system", content=INTENT_SYSTEM_PROMPT),
            LLMMessage(role="user", content=user_context + "\nUser message: " + user_question),
        ]
        raw = self.llm.chat(messages)

        logger.debug("Raw intent classifier output:")
        logger.debug(raw)

        # Robust-ish JSON parse: extract first JSON object
        parsed = self._extract_json(raw)

        logger.debug("Parsed intent JSON:")
        logger.debug(parsed)

        intent = IntentResult.model_validate(parsed)
        
        logger.debug("Validated IntentResult:")
        logger.debug(intent.model_dump())

        return intent
    
    @staticmethod
    def _extract_json(text: str) -> dict:
        # Simple heuristic: find first { ... } block
        start = text.find("{")
        end = text.find("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError(f"Could not parse JSON from intent classifier output: {text}")
        return json.loads(text[start:end+1])
import json
import re

from .llm_client import LLMClient
from .schemas import IntentResult, LLMMessage, UserProfile, LearningIntent
from .prompts import INTENT_SYSTEM_PROMPT
from .utils.json_extract import extract_json
from .telemetry import log_intent_event
from .logging_utils import get_logger


logger = get_logger("intent_classifier")


_INTENT_KEYWORDS = {
    LearningIntent.urgent_troubleshooting: [
        r"\berror\b", r"\bexception\b", r"\btraceback\b", r"\bfailed\b", r"\bfailing\b",
        r"\bbug\b", r"\bfix\b", r"\bhow do i fix\b", r"\bdoesn't work\b", r"\bissue\b",
        r"\b\what's the problem\b", r"\bwhat caused the problem\b", r"\bwhat's wrong\b"
    ],
    LearningIntent.guided_study: [
        r"\bstudy\b", r"\blearn\b", r"\broadmap\b", r"\bplan\b", r"\bschedule\b",
        r"\b7[- ]?day\b", r"\b10[- ]?day\b", r"\bcourse\b", r"\bcurriculum\b",
    ],
    LearningIntent.professional_research: [
        r"\bsurvey\b", r"\bcompare\b", r"\btrade[- ]?offs?\b", r"\bstate of the art\b",
        r"\bsota\b", r"\bpapers?\b", r"\bcitations?\b", r"\breferences?\b",
        r"\bbenchmark\b", r"\bablations?\b",
    ],
}

_WHAT_IS_PAT = re.compile(r"^\s*(what is|what's|explain|define|how does)\b", re.IGNORECASE)


def _signal_strength(query: str) -> dict[LearningIntent, float]:
    """Calculate signal strength for each intent based on the query."""
    q = query.lower()
    scores = {k: 0.0 for k in LearningIntent}

    if _WHAT_IS_PAT.search(q):
        scores[LearningIntent.casual_curiosity] += 1.0
    
    for intent, pats in _INTENT_KEYWORDS.items():
        for p in pats:
            if re.search(p, q):
                scores[intent] += 1.0
    
    # Code-like /stacktrace cues boost troubleshooting
    if "traceback" in q or "file " in q or "line " in q or "syntaxerror" in q:
        scores[LearningIntent.urgent_troubleshooting] += 1.5

    return scores


def _calibrate_confidence(chosen: LearningIntent, scores: dict[LearningIntent, float]) -> float:
    """ Map 'how strong is the evidence for the chosen intent' into a confidence score."""
    best = scores.get(chosen, 0.0)
    runner_up = max(v for k, v in scores.items() if k != chosen)

    # If nothing triggered, it's waek -> low confidence
    if best <= 0.0:
        return 0.55
    
    margin = best - runner_up

    # Strong clear signals
    if best >= 2.5 and margin >= 1.5:
        return 0.90
    if best >= 2.0 and margin >= 1.0:
        return 0.85
    if best >= 1.5 and margin >= 0.8:
        return 0.78
    if best >= 1.0 and margin >= 0.5:
        return 0.70
    
    # Conflicting signals
    return 0.60


def _blend_confidence(rule_c: float, llm_c: float | None) -> float:
    """Blend rule-based confidence with LLM-provided confidence."""
    if llm_c is None:
        return rule_c
    # weights: rules dominate for stability
    c = 0.7 * rule_c + 0.3 * max(0.0, min(1.0, llm_c))
    return max(0.55, min(0.92, c))


def _pick_intent(scores: dict[LearningIntent, float]) -> LearningIntent:
    """Pick the intent with the highest score."""
    # break ites in a sensible order
    # troubleshooting > professional > guided > casual
    order = [
        LearningIntent.urgent_troubleshooting, 
        LearningIntent.professional_research, 
        LearningIntent.guided_study, 
        LearningIntent.casual_curiosity
    ]
    best_val = max(scores.values())
    best = [k for k, v in scores.items() if v == best_val]
    for k in order:
        if k in best:
            return k
    return LearningIntent.casual_curiosity


def _needs_llm(scores: dict[LearningIntent, float], conf: float, query: str) -> bool:
    """Determine if we need the LLM to classify the intent."""
    if conf >= 0.70:
        return False
    q = query.strip()

    if len(q.split()) <= 4:
        return True   # very short queries are ambiguous
    
    # conflict: top two clost
    vals = sorted(scores.values(), reverse=True)
    if len(vals) >= 2 and (vals[0] - vals[1]) <= 0.5:
        return True
    
    return True


def _intent_clarifier(intent: LearningIntent, conf: float, query: str) -> str | None:
    """Propose a clarifying question for the intent."""
    if conf >= 0.65:
        return None
    # Generic best clarifier:
    return "Is this question mainly out of curiosity, or are you trying to study it systematically (or use it for work?"


def _normalize_clarifying_qeustion(res: IntentResult, query: str) -> str | None:
    """Normalize the clarifying question to avoid format-related confusion."""
    if not res.should_ask_clarifying_question:
        return None
    q = (res.clarifying_question or "").strip()
    # If it asks about format, replace it.
    bad_phrases = ["overview", "detailed", "technical", "theoretical", "depth", "level of detail"]
    if any(p in q.lower() for p in bad_phrases) or not q:
        return _intent_clarifier(res.intent, res.confidence, query)
    return q


class IntentClassifier:
    def __init__(self) -> None:
        self.llm = LLMClient()
    
    def classify(self, user_question: str, profile: UserProfile) -> IntentResult:
        scores = _signal_strength(user_question)
        rule_intent = _pick_intent(scores)
        rule_conf = _calibrate_confidence(rule_intent, scores)

        if not _needs_llm(scores, rule_conf, user_question):
            # produce IntenResult from rules
            result = IntentResult(
                intent=rule_intent,
                confidence=rule_conf,
                rationale="Rule-based: strong intent signals in query.",
                suggested_output="balanced" if rule_intent != LearningIntent.urgent_troubleshooting else "detailed",
                should_ask_clarifying_question=rule_conf < 0.65 and rule_intent not in {LearningIntent.urgent_troubleshooting},
                clarifying_question=_intent_clarifier(rule_intent, rule_conf, user_question),
                use_llm=False,
            )

            logger.debug("Rule-based IntentResult:")
            logger.debug(result.model_dump())

            log_intent_event({
                "query": user_question[:200],
                "intent": result.intent,
                "confidence": result.confidence,
                "use_llm": result.use_llm,
                "should_ask_clarifying_question": result.should_ask_clarifying_question,
                "suggested_output": result.suggested_output,
                # optional for debugging (safe):
                "signals": scores,  # from _signal_strength
            })

            return result

        # Stage 2: call LLM (query-first; profile secondary)
        llm_result = self._classify_with_llm(user_question, profile)

        # Blend/conflict resolution
        final_conf = _blend_confidence(rule_conf, llm_result.confidence)
        final_intent = llm_result.intent

        # Gardrails: "what is X" should rarely be guided_study unless user explicitly ask to study
        if _WHAT_IS_PAT.search(user_question.lower()) and final_intent == LearningIntent.guided_study:
            final_intent = LearningIntent.casual_curiosity
            final_conf = max(0.65, final_conf - 1.10)
        
        llm_result.intent = final_intent
        llm_result.confidence = final_conf

        # Ensure clarifying question is intent-disambiguating
        llm_result.clarifying_question = _normalize_clarifying_qeustion(llm_result, user_question)

        logger.debug("LLM-based IntentResult:")
        logger.debug(llm_result.model_dump())

        log_intent_event({
            "query": user_question[:200],
            "intent": llm_result.intent,
            "confidence": llm_result.confidence,
            "use_llm": llm_result.use_llm,
            "should_ask_clarifying_question": llm_result.should_ask_clarifying_question,
            "suggested_output": llm_result.suggested_output,
            # optional for debugging (safe):
            "signals": scores,  # from _signal_strength
        })

        return llm_result
    
    def _classify_with_llm(self, user_question: str, profile: UserProfile) -> IntentResult:
        """Classify the intent using the LLM."""
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
        parsed = extract_json(raw)

        logger.debug("Parsed intent JSON:")
        logger.debug(parsed)

        intent = IntentResult.model_validate(parsed)
        intent.use_llm = True
        
        logger.debug("Validated IntentResult:")
        logger.debug(intent.model_dump())

        return intent
    
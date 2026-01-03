import re
from datetime import datetime, timezone

from .schemas import (
    UserMemory, LearningMode, MemoryItem, UserPreferences, 
    ExplanationStyle, ResourcePreference, Verbosity
)
from .stores.memory_store import MemoryStore
from .logging_utils import get_logger


logger = get_logger("memory_manager")


MAX_HISTORY = 50
MAX_TOPICS = 10


_NEG = r"(?:no|not|don't|do not|without|avoid|skip)"
_WS = r"(?:\W+\w+){0,3}?\W+"  # up to ~3 words gap
# Patterns like: "no ... math" / "don't ... formulas"
NEG_MATH = re.compile(_NEG + _WS + r"(math|formula|formulas|derive|derivation|proof)", re.I)
NEG_DETAIL = re.compile(_NEG + _WS + r"(detailed|detail|in-depth|deep dive|deep|technical)", re.I)
POS_MATH = re.compile(r"\b(math|formula|formulas|derive|derivation|proof)\b", re.I)
POS_EXAMPLES = re.compile(r"\b(example|examples|intuitive|analogy)\b", re.I)
POS_CONCISE = re.compile(r"\b(brief|quick|tldr|overview|high[- ]level)\b", re.I)
POS_DETAILED = re.compile(r"\b(detailed|in-depth|deep dive|deep)\b", re.I)


def infer_preferences(mem: UserMemory, query: str) -> UserPreferences:
    q = query.lower()

    # 1) Negative constraints FIRST
    if NEG_MATH.search(q):
        mem.preferences.explanation_style = ExplanationStyle.examples  # or balanced
    if NEG_DETAIL.search(q) or "just an overview" in q or "high level only" in q:
        mem.preferences.verbosity = Verbosity.concise
    
    # 2) Positive cues only if not contradicted
    if POS_EXAMPLES.search(q):
        mem.preferences.explanation_style = ExplanationStyle.examples

    # math only if not negated
    if POS_MATH.search(q) and not NEG_MATH.search(q):
        mem.preferences.explanation_style = ExplanationStyle.formulas
    
    # verbosity: detailed only if not negated and not overridden by concise
    if POS_CONCISE.search(q):
        mem.preferences.verbosity = Verbosity.concise
    elif POS_DETAILED.search(q) and not NEG_DETAIL.search(q):
        mem.preferences.verbosity = Verbosity.detailed
    
    # Resource preference cues
    if any(w in q for w in ["video", "youtube"]):
        mem.preferences.resource_preference = ResourcePreference.video
    elif any(w in q for w in ["paper", "docs", "documentation", "blog"]):
        mem.preferences.resource_preference = ResourcePreference.text
    
    return mem.preferences


class MemoryManager:
    def __init__(self, store: MemoryStore) -> None:
        self.store = store

    def load(self, user_id: str = "default") -> UserMemory:
        logger.debug("Loading memory for user %s", user_id)
        return self.store.load(user_id) or UserMemory(user_id=user_id)

    def save(self, mem: UserMemory) -> None:
        logger.debug("Saving memory for user %s", mem.user_id)
        self.store.save(mem)
    
    def update_after_answer(
        self,
        mem: UserMemory,
        *,
        query: str,
        topic: str,
        intent: str,
        mode: LearningMode,
        answer_summary: str,
    ) -> UserMemory:
        logger.debug("Updating memory after answer for user %s", mem.user_id)

        ts = datetime.now(timezone.utc).isoformat()
        item = MemoryItem(ts=ts, query=query[:200], topic=topic, intent=intent, mode=mode, summary=answer_summary[:300])
        mem.history.append(item)
        mem.history = mem.history[-MAX_HISTORY:]

        # update topics list (unique, keep recency)
        if topic:
            if topic in mem.topics:
                mem.topics.remove(topic)
            mem.topics.append(topic)
            mem.topics = mem.topics[-MAX_TOPICS:]
            mem.last_topic = topic
        
        return mem

    def build_prompt_context(self, mem: UserMemory) -> str:
        # Keep this short. The generator prompt should not blow up.
        recent_topics = ", ".join(mem.topics[max(-5, -MAX_HISTORY):]) if mem.topics else "none"
        prefs = mem.preferences

        return (
            f"USER_MEMORY:\n"
            f"- Recent topics: {recent_topics}\n"
            f"- Preferences: explanation_style={prefs.explanation_style.value}, resource_preference={prefs.resource_preference.value}, verbosity={prefs.verbosity.value}\n"
            f"- Avoid repeating basics for topics the user already coverred.\n"
        )

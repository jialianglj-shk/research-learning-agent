from datetime import datetime, timezone

from .schemas import UserMemory, LearningMode, MemoryItem
from .store.memory_store import MemoryStore
from .logging_utils import get_logger


logger = get_logger("memory_manager")


MAX_HISTORY = 50
MAX_TOPICS = 10


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

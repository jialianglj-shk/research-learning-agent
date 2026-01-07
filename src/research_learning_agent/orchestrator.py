from __future__ import annotations

import re

from .schemas import (
    UserQuery, AgentAnswer, UserProfile, StepType, OrchestratorActionType, 
    OrchestratorAction, OrchestratorResult, ToolResult, Plan, UserMemory,
    ResourcePreference, UIResponse, UISourcesItem, UIResponseAction
)
from .intent_classifier import IntentClassifier
from .planner import Planner
from .generator import Generator
from .tool_executor import ToolExecutor
from .pedagogy import Pedagogy
from .memory import MemoryManager, infer_preferences
from .stores.memory_store import MemoryStore
from .logging_utils import get_logger


logger = get_logger("Orchesrator")


_MAX_TOPIC_LEN = 80


# Remove common "instruction wrappers" to make fallback topic less ugly
_PREFIX_STRIP = re.compile(
    r"^\s*(please|can you|could you|help me|i want to|i need to|tell me|explain|what is|what's)\s+",
    re.IGNORECASE,
)

_WS = re.compile(r"\s+")


def _clean_topic(s: str) -> str:
    s = s.strip()
    s = _PREFIX_STRIP.sub("", s)
    s = _WS.sub(" ", s)
    # strip trailing punctuation
    s = s.strip(" .,:;!?\"'()[]{}")
    if len(s) > _MAX_TOPIC_LEN:
        s = s[:_MAX_TOPIC_LEN].rstrip()
    return s


def infer_topic(plan: Plan | None, query: str) -> str:
    """
    Infer a short 'topic' string used for memory tracking.

    Priority:
    1) plan.goal (if present and nontrivial)
    2) cleaned query prefix (truncated)
    """
    goal = ""
    if plan is not None:
        goal = (plan.goal or "").strip()
    
    # Heuristic: reject overly generic goals
    if goal:
        cleaned_goal = _clean_topic(goal)
        if cleaned_goal and cleaned_goal.lower() not in {
            "general", "overview", "summary", "intro", "explanation", 
            "learn", "study", "research", "understand", "help", "teach"
            }:
            return cleaned_goal
    
    # Fallback: use the query (cleaned)
    cleaned_query = _clean_topic(query)
    return cleaned_query or "unknown"


def suggest_followups(mem: UserMemory | None, current_topic: str, *, max_items: int = 2) -> list[str]:
    """
    Generate 0..max_items follow-up questions bsed on memory + current topic.

    Design goals:
    - deterministic
    - no LLM calls
    - non-repetitive
    - connect to prior topics when useful
    """
    if mem is None:
        return []
    if max_items <= 0:
        return []
    
    cur = _clean_topic(current_topic)
    if not cur:
        return []
    
    topics = mem.topics or []
    if not topics:
        return []

    # Normalize and preserve order
    norm_topics = [_clean_topic(t) for t in topics if _clean_topic(t)]
    if not norm_topics:
        return []

    out: list[str] = []

    # 1) Connect to most recent *different* prior topic
    # (usually mem.topics[-1] is last topic; but current may equal last after update,
    # so we search backwards for a different one)
    prev: str | None = None
    for t in reversed(norm_topics):
        if t != cur:
            prev = t
            break
    
    if prev:
        out.append(f"Want to connect **{cur}** to what you learned earlier about **{prev}**?")

    # 2) If user prefers video/text, suggest a next action (optional)
    # Keep this generic; don't create tool calls here.
    if len(out) < max_items:
        prefs = getattr(mem, "preferences", None)
        resource_pref = getattr(prefs, "resource_preference", None)

        if resource_pref == ResourcePreference.video:
            out.append(f"Want a short **video-first** next step for **{cur}** (5-10 min)")
        elif resource_pref == ResourcePreference.text:
            out.append(f"Want a **docs/articles-first** next step for **{cur}**?")

    # Deduplicate and cap
    dedup: list[str] = []
    seen = set()
    for x in out:
        if x not in seen:
            dedup.append(x)
            seen.add(x)
    
    return dedup[:max_items]


class Orchestrator:
    def __init__(self) -> None:
        self.intent = IntentClassifier()
        self.planner = Planner()
        self.tools = ToolExecutor()
        self.pedagogy = Pedagogy()
        self.generator = Generator()
        self.memory_store = MemoryStore()
        self.memory = MemoryManager(self.memory_store)

    def run(
        self, query: UserQuery, profile: UserProfile, user_id: str = "default", 
        *, force_final: bool = False,
    ) -> OrchestratorResult:
        # 0) load memory
        mem = self.memory.load(user_id)
    
        # 1) intent
        intent_result = self.intent.classify(query.question, profile)

        # 2) clarification decision (skipped if force_final)
        if not force_final:
            # 3.1 Prefer intent clarifying question if available
            cq = getattr(intent_result, "clarifying_question", None)
            needs_clarify = bool(intent_result.should_ask_clarifying_question and cq)

            # # 3.2 Fallback: plan contains clarify step
            # if not needs_clarify:
            #     for step in plan.steps:
            #         if step.type.value == StepType.clarify:
            #             cq = step.outputs.get("calrifying_question")
            #             needs_clarify = True
            #             break
            
            # 3.3 Return clarifying question
            if needs_clarify:
                return OrchestratorResult(
                    action=OrchestratorAction(
                        kind=OrchestratorActionType.need_clarification,
                        clarifying_question=cq
                    )
                )

        # 3) plan
        plan = self.planner.create_plan(query.question, profile, intent_result)

        # 4) tool execution
        tool_results: list[ToolResult] = []
        for step in plan.steps:
            if step.type == StepType.research:
                tool_results.extend(self.tools.execute_step(step))
        
        # 5) pedagogy
        mode = self.pedagogy.choose_mode(intent_result, profile)
        spec = self.pedagogy.build_spec(mode, profile)

        # TODO: Add memory-derived style adjustment (optional)
        # e.g. if user prefers formulas and mode is quick_explain, keep sections but instruct tone.
        # spec.style_notes += f" User preferes {mem.preferences.explanation_style.value} explanations."
        
        # 6) generate final answer
        answer = self.generator.generate(
            query=query, 
            profile=profile, 
            intent=intent_result, 
            plan=plan, 
            tool_results=tool_results,
            spec=spec,
            memory=mem,
            force_final=force_final,
        )

        # 7) infer prefs + update memory
        infer_preferences(mem, query.question)

        # 8) infer topic and update memory
        topic = infer_topic(plan, query.question)

        # 9) suggest follow-up questions
        answer.follow_up_questions = suggest_followups(mem, topic, max_items=2)

        # 10) update memory
        mem = self.memory.update_after_answer(
            mem,
            query=query.question,
            topic=topic,
            intent=intent_result.intent,
            mode=answer.mode,
            answer_summary=answer.explanation,
        )
        self.memory.save(mem)

        return OrchestratorResult(
            action=OrchestratorAction(kind=OrchestratorActionType.final),
            answer=answer,
            intent=intent_result,
            plan=plan,
            tool_results=tool_results,
        )
    
    def chat(self, *, session_id: str, message: str, profile: UserProfile, force_final: bool = False) -> UIResponse:
        """
        UI-friendly wrapper:
        - accepts session_id + user message
        - return a structured response the UI can render
        """
        # Just map seesion_id -> user_id for now (1:1)
        user_id = session_id

        res = self.run(UserQuery(question=message), profile, user_id, force_final=force_final)

        # Build sources from res.answer.sources
        sources = []
        if res.answer and getattr(res.answer, "sources", None):
            for source_item in res.answer.sources:
                sources.append(UISourcesItem(title=source_item.title, url=source_item.url))
        
        followups = []
        if res.answer and getattr(res.answer, "follow_up_questions", None):
            followups = list[str](res.answer.follow_up_questions) # a shallower copy
        
        if res.action.kind == OrchestratorActionType.need_clarification:
            action = UIResponseAction.clarify
            clarifying_question = res.action.clarifying_question
        else:
            action = UIResponseAction.answer
            clarifying_question = None

        return UIResponse(
            session_id=session_id,
            action=action,
            mode=res.answer.mode if res.answer else None,
            plan=res.plan,
            answer=res.answer,
            sources=sources,
            followups=followups,
            clarifying_question=clarifying_question,
        )
        
        


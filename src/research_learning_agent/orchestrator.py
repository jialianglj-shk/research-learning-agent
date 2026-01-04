from __future__ import annotations

import re

from .schemas import (
    UserQuery, AgentAnswer, UserProfile, StepType, OrchestratorActionType, 
    OrchestratorAction, OrchestratorResult, ToolResult, Plan
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



from __future__ import annotations

from .schemas import (
    UserQuery, AgentAnswer, UserProfile, StepType, OrchestratorActionType, 
    OrchestratorAction, OrchestratorResult, ToolResult
)
from .intent_classifier import IntentClassifier
from .planner import Planner
from .generator import Generator
from .tool_executor import ToolExecutor
from .pedagogy import Pedagogy
from .logging_utils import get_logger


logger = get_logger("Orchesrator")


class Orchestrator:
    def __init__(self) -> None:
        self.intent = IntentClassifier()
        self.planner = Planner()
        self.tools = ToolExecutor()
        self.pedagogy = Pedagogy()
        self.generator = Generator()

    def run(self, query: UserQuery, profile: UserProfile, *, force_final: bool = False) -> OrchestratorResult:
        # 1) intent
        intent_result = self.intent.classify(query.question, profile)

        # 2) plan
        plan = self.planner.create_plan(query.question, profile, intent_result)

        # 3) clarification decision (skipped if force_final)
        if not force_final:
            # 3.1 Prefer intent clarifying question if available
            cq = getattr(intent_result, "clarifying_question", None)
            needs_clarify = bool(intent_result.should_ask_clarifying_question and cq)

            # 3.2 Fallback: plan contains clarify step
            if not needs_clarify:
                for step in plan.steps:
                    if step.type.value == StepType.clarify:
                        cq = step.outputs.get("calrifying_question")
                        needs_clarify = True
                        break
            
            # 3.3 Return clarifying question
            if needs_clarify:
                return OrchestratorResult(
                    action=OrchestratorAction(
                        kind=OrchestratorActionType.need_clarification,
                        clarifying_question=cq
                    )
                )

        # 4) tool execution
        tool_results: list[ToolResult] = []
        for step in plan.steps:
            if step.type == StepType.research:
                tool_results.extend(self.tools.execute_step(step))
        
        # 5) pedagogy
        mode = self.pedagogy.choose_mode(intent_result, profile)
        spec = self.pedagogy.build_spec(mode, profile)
        
        # 6) generate final answer
        answer = self.generator.generate(
            query=query, 
            profile=profile, 
            intent=intent_result, 
            plan=plan, 
            tool_results=tool_results,
            spec=spec,
            force_final=force_final,
        )

        return OrchestratorResult(
            action=OrchestratorAction(kind=OrchestratorActionType.final),
            answer=answer,
            intent=intent_result,
            plan=plan,
            tool_results=tool_results,
        )

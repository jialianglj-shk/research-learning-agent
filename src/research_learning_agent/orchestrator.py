from .schemas import UserQuery, AgentAnswer, UserProfile, StepType, OrchestratorActionType, OrchestratorAction, OrchestratorResult
from .intent_classifier import IntentClassifier
from .planner import Planner
from .generator import Generator
from .logging_utils import get_logger


logger = get_logger("Orchesrator")


class Orchestrator:
    def __init__(self) -> None:
        self.intent = IntentClassifier()
        self.planner = Planner()
        self.generator = Generator()

    def run(self, query: UserQuery, profile: UserProfile, force_final: bool = False) -> OrchestratorResult:
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

        # 4) generate final answer
        answer = self.generator.generate(query, profile, intent_result, plan, force_final)
        return OrchestratorResult(
            action=OrchestratorAction(kind=OrchestratorActionType.final),
            answer=answer,
            intent=intent_result,
            plan=plan,
        )

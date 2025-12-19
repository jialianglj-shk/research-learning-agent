from .schemas import UserQuery, AgentAnswer, UserProfile, OrchestratorAction
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

    def run(self, query: UserQuery, profile: UserProfile) -> tuple[AgentAnswer, dict]:
        # 1) intent
        intent_result = self.intent.classify(query.question, profile)

        # 2) plan
        plan = self.planner.create_plan(query.question, profile, intent_result)

        debug = {
            "intent": intent_result,
            "plan": plan,
        }

        # 3) Decide if we need clarification
        cq = getattr(intent_result, "clarifying_question", None)
        needs_clarify_intent = bool(intent_result.should_ask_clarifying_question and cq)
        needs_clarify_plan = any(step.type.value == "clarify" for step in plan.steps)
        
        if needs_clarify_intent:
            return None, OrchestratorAction(kind="need_clarification", clarifying_question=cq), debug
        
        if needs_clarify_plan:
            # For Day 3: use the plan's clarify step description as a question (or a generic question)
            question_text = "Can you clarify what you mean / your goal? (1-2 sentences)"
            return None, OrchestratorAction(kind="need_clarification", clarifying_question=question_text), debug

        # 3) generate final
        answer = self.generator.generate(query, profile, intent_result, plan)

        return answer, OrchestratorAction(kind="final"), debug

from .schemas import UserQuery, AgentAnswer, UserProfile
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

        # 3) generate final
        answer = self.generator.generate(query, profile, intent_result, plan)

        debug = {
            "intent": intent_result,
            "plan": plan,
        }

        return answer, debug

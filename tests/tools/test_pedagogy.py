from research_learning_agent.pedagogy import Pedagogy
from research_learning_agent.schemas import LearningMode, UserProfile, UserLevel, IntentResult, LearningIntent


def test_choose_mode_mapping():
    ped = Pedagogy()
    profile = UserProfile(
        user_id="u1",
        background="backgournd",
        level=UserLevel.beginner,
        goals="goals"
    )
    assert ped.choose_mode(
        IntentResult(intent=LearningIntent.professional_research, confidence=0.9, rationale="x"), 
        profile
    ) == LearningMode.deep_research
from research_learning_agent.schemas import AgentAnswer, LearningMode


def test_agent_answer_defaults():
    a = AgentAnswer(explanation="x")
    assert a.mode == LearningMode.quick_explain
    assert a.sections == []

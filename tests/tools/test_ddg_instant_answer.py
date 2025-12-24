import pytest

from research_learning_agent.tools.ddg_instant_answer import DuckDuckGoInstantAnswerTool


def test_empty_query_returns_empty():
    tool = DuckDuckGoInstantAnswerTool()
    assert tool.run("", 5) == []
    assert tool.run("   ", 5) == []


def test_users_abstract_when_present(monkeypatch):
    def fake_request_json(method, url, **kwargs):
        assert method == "GET"
        assert "duckduckgo.com" in url
        return {
            "Heading": "Reinforcement learning",
            "AbstractText": "RL is ...",
            "AbstractURL": "https://example.com/rl",
            "RelatedTopics": []
        }
    
    monkeypatch.setattr("research_learning_agent.tools.ddg_instant_answer.request_json", fake_request_json)

    tool = DuckDuckGoInstantAnswerTool()
    out = tool.run("reinforcement learning", 5)

    assert out[0]["title"] == "Reinforcement learning"
    assert out[0]["url"] == "https://example.com/rl"
    assert "RL is ..." in out[0]["snippet"]


def test_extracts_related_topics_flat(monkeypatch):
    def fake_request_json(method, url, **kwargs):
        return {
            "AbstractURL": "",
            "AbstractText": "",
            "RelatedTopics": [
                {"Text": "Topic A", "FirstURL": "https://a.com"},
                {"Text": "Topic B", "FirstURL": "https://b.com"},
            ]
        }

    monkeypatch.setattr("research_learning_agent.tools.ddg_instant_answer.request_json", fake_request_json)

    tool = DuckDuckGoInstantAnswerTool()
    out = tool.run("test", 2)

    assert out == [
        {"title": "Topic A", "url": "https://a.com", "snippet": "Topic A"},
        {"title": "Topic B", "url": "https://b.com", "snippet": "Topic B"},
    ]


def test_extracts_related_topics_nested(monkeypatch):
    def fake_request_json(method, url, **kwargs):
        return {
            "RelatedTopics": [
                {"Name": "Group", "Topics": [
                    {"Text": "Nested A", "FirstURL": "https://na.com"},
                    {"Text": "Nested B", "FirstURL": "https:/nb.com"},
                ]}
            ]
        }
    
    monkeypatch.setattr("research_learning_agent.tools.ddg_instant_answer.request_json", fake_request_json)

    tool = DuckDuckGoInstantAnswerTool()
    out = tool.run("test", 1)

    assert out == [
        {"title": "Nested A", "url": "https://na.com", "snippet": "Nested A"},
    ]


def test_top_k_limites_results(monkeypatch):
    def fake_request_json(method, url, **kwargs):
        return {
            "RelatedTopics": [
                {"Text": f"T{i}", "FirstURL": f"https://t{i}.com"} for i in range(10)
            ]
        }
    
    monkeypatch.setattr("research_learning_agent.tools.ddg_instant_answer.request_json", fake_request_json)
    
    tool = DuckDuckGoInstantAnswerTool()
    out = tool.run("test", 3)
    assert len(out) == 3
    assert out[0] == {"title": "T0","url": "https://t0.com","snippet": "T0"}
    assert out[2] == {"title": "T2","url": "https://t2.com","snippet": "T2"}
import pytest

from research_learning_agent.tools.serper_web import SerperWebSearchTool
from research_learning_agent.tools.http import ToolHTTPError


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("SERPER_API_KEY", "test-key")


def test_empty_query_returns_empty(monkeypatch):
    tool = SerperWebSearchTool()
    assert tool.run("", top_k=5) == []
    assert tool.run("   ", top_k=5) == []


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("SERPER_API_KEY", raising=False)
    tool = SerperWebSearchTool()
    with pytest.raises(ToolHTTPError) as e:
        tool.run("what is supervised learning?", top_k=5)
    assert "SERPER_API_KEY" in str(e.value)


def test_top_k_is_clamped(monkeypatch):
    # Return many orgainic results; tool should clamp to at most 10
    def fake_request_json(method, url, **kwargs):
        assert kwargs["json_body"]["num"] == 10 # top_k should beclamped before calling api
        return {
            "organic": [
                {"title": f"T{i}", "link": f"https://x{i}.com", "snippet": f"S{i}"}
                for i in range(30)
            ]
        }

    monkeypatch.setattr("research_learning_agent.tools.serper_web.request_json", fake_request_json)

    tool = SerperWebSearchTool()
    out = tool.run("test", top_k=999)
    assert len(out) == 10
    assert out[0]["url"] == "https://x0.com"
    assert out[-1]["url"] == "https://x9.com"


def test_skips_items_without_link(monkeypatch):
    def fake_request_json(method, url, **kwargs):
        return {
            "organic": [
                {"title": "NoLink", "snippet": "missing link"},
                {"title": "HasLink", "link": "https://x.com", "snippet": "has link"},
            ]
        }
    
    monkeypatch.setattr("research_learning_agent.tools.serper_web.request_json", fake_request_json)

    tool = SerperWebSearchTool()
    out = tool.run("test", top_k=5)
    assert out == [{"title": "HasLink", "url": "https://x.com", "snippet": "has link"}]


def test_title_falls_back_to_url_when_missing(monkeypatch):
    def fake_request_json(method, url, **kwargs):
        return {"organic": [{"link": "https://only-link.com", "snippet": "only link"}]}
    
    monkeypatch.setattr("research_learning_agent.tools.serper_web.request_json", fake_request_json)

    tool = SerperWebSearchTool()
    out = tool.run("test", top_k=1)
    assert out == [{"title": "https://only-link.com", "url": "https://only-link.com", "snippet": "only link"}]


def test_answerbox_used_when_no_organic(monkeypatch):
    def fake_request_json(method, url, **kwargs):
        return {
            "organic": [],
            "answerBox": {
                "title": "Answer Box Title",
                "answer": "Short answer text",
                "link": "https://answerbox.com",
            }
        }
    
    monkeypatch.setattr("research_learning_agent.tools.serper_web.request_json", fake_request_json)

    tool = SerperWebSearchTool()
    out = tool.run("test", top_k=5)
    assert out == [{"title": "Answer Box Title", "url": "https://answerbox.com", "snippet": "Short answer text"}]
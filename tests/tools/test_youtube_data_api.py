import pytest

from research_learning_agent.tools.youtube_data_api import YouTubeSearchTool
from research_learning_agent.tools.http import ToolHTTPError


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("YOUTUBE_API_KEY", "test-key")


def test_empty_query_returns_empty():
    tool = YouTubeSearchTool()
    assert tool.run("", top_k=5) == []
    assert tool.run("   ", top_k=5) == []


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("YOUTUBE_API_KEY", raising=False)
    tool = YouTubeSearchTool()
    with pytest.raises(ToolHTTPError) as e:
        tool.run("test", top_k=5)
    assert "YOUTUBE_API_KEY" in str(e.value)


def test_youtube_normalizes_results(monkeypatch):
    def fake_request_json(method, url, **kwargs):
        assert method == "GET"
        assert "youtube" in url
        params = kwargs.get("params") or {}
        assert params["type"] == "video"
        assert params["part"] == "snippet"
        assert params["q"] == "reinforcement learning tutorial"
        assert params["maxResults"] == 2

        return {
            "items": [
                {
                    "id": {"videoId": "video-id-1"},
                    "snippet": {"title": "Intro RL", "description": "description1..."},
                },
                {
                    "id": {"videoId": "video-id-2"},
                    "snippet": {"title": "Deep RL", "description": "description2..."},
                }
            ]
        }

    monkeypatch.setattr("research_learning_agent.tools.youtube_data_api.request_json", fake_request_json)

    tool = YouTubeSearchTool()
    out = tool.run("reinforcement learning tutorial", top_k=2)

    assert out == [
        {"title": "Intro RL", "url": "https://www.youtube.com/watch?v=video-id-1", "snippet": "description1..."},
        {"title": "Deep RL", "url": "https://www.youtube.com/watch?v=video-id-2", "snippet": "description2..."},
    ]


def test_skips_items_without_video_id(monkeypatch):
    def fake_request_json(method, url, **kwargs):
        return {
            "items": [
                {"id": {}, "snippet": {"title": "Bad", "descrition": "desc..."}},
                {"id": {"videoId": "video-id-ok"}, "snippet": {"title": "OK", "description": "ok"}},
            ]
        }
    
    monkeypatch.setattr("research_learning_agent.tools.youtube_data_api.request_json", fake_request_json)

    tool = YouTubeSearchTool()
    out = tool.run("test", top_k=5)
    assert out == [{"title": "OK", "url": "https://www.youtube.com/watch?v=video-id-ok", "snippet": "ok"}]


def test_title_falls_back_to_url_when_missing(monkeypatch):
    def fake_request_json(method, url, **kwargs):
        return {
            "items": [
                {"id": {"videoId": "video-id-1"}, "snippet": {"description": "desc only"}},
            ]
        }

    monkeypatch.setattr("research_learning_agent.tools.youtube_data_api.request_json", fake_request_json)

    tool = YouTubeSearchTool()
    out = tool.run("test", top_k=1)
    assert out == [{
        "title": "https://www.youtube.com/watch?v=video-id-1", 
        "url": "https://www.youtube.com/watch?v=video-id-1", 
        "snippet": "desc only"
    }]


def test_top_k_is_clamped(monkeypatch):
    # If pass something > 25, the tool should clamp to 25 (per implementation)
    def fake_request_json(method, url, **kwargs):
        assert kwargs["params"]["maxResults"] == 25
        return {
            "items": [
                 {"id": {"videoId": f"video-id-{i}"}, "snippet": {"title": f"T{i}", "description": f"D{i}"}}
                 for i in range(50)
            ]
        }
    
    monkeypatch.setattr("research_learning_agent.tools.youtube_data_api.request_json", fake_request_json)

    tool = YouTubeSearchTool()
    out = tool.run("test", top_k=100)
    assert len(out) == 25
    assert out[0] == {
        "title": "T0",
        "url": "https://www.youtube.com/watch?v=video-id-0",
        "snippet": "D0"
    }
    assert out[-1] == {
        "title": "T24",
        "url": "https://www.youtube.com/watch?v=video-id-24",
        "snippet": "D24"
    }


def test_request_json_error_bubbles_up(monkeypatch):
    def fake_request_json(method, url, **kwargs):
        raise ToolHTTPError(error_type="http", message="test error", url=url, status_code=403)
    
    monkeypatch.setattr("research_learning_agent.tools.youtube_data_api.request_json", fake_request_json)

    tool = YouTubeSearchTool()
    with pytest.raises(ToolHTTPError) as e:
        tool.run("test", top_k=5)
    assert e.value.error_type == "http"

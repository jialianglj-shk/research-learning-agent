import pytest
import requests
import responses

from research_learning_agent.tools.http import request_json, ToolHTTPError


@responses.activate
def test_request_json_success():
    responses.add(
        responses.GET,
        "https://example.com/api",
        json={"ok": True},
        status=200,
    )
    data = request_json("GET", "https://example.com/api")
    assert data["ok"] is True


@responses.activate
def test_request_json_parse_error():
    responses.add(
        responses.GET,
        "https://example.com/api",
        body="invalid json",
        status=200,
        content_type="text/plain",
    )
    with pytest.raises(ToolHTTPError) as e:
        request_json("GET", "https://example.com/api")
    assert e.value.error_type == "parse"


@responses.activate
def test_request_retries_on_429_then_succeeds(monkeypatch):
    # speed up backoff in test
    monkeypatch.setattr("research_learning_agent.tools.http._sleep_backoff", lambda attempt: None)

    responses.add(responses.GET, "https://example.com/api", json={"err": "rate limit"}, status=429)
    responses.add(responses.GET, "https://example.com/api", json={"ok": True}, status=200)

    data = request_json("GET", "https://example.com/api", max_retries=2)
    assert data["ok"] is True


@responses.activate
def test_request_no_retry_on_400(monkeypatch):
    monkeypatch.setattr("research_learning_agent.tools.http._sleep_backoff", lambda attempt: None)

    responses.add(responses.GET, "https://example.com/api", json={"err": "bad request"}, status=400)

    with pytest.raises(ToolHTTPError) as e:
        request_json("GET", "https://example.com/api", max_retries=2)
        assert e.value.error_type == "http"
        assert e.value.status_code == 400
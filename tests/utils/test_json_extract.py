import pytest
import json

from research_learning_agent.utils.json_extract import extract_json


def test_extract_json_object_plain():
    text = '{"intent":"casual_curiosity","confidence":0.7,"rationale":"x","should_ask_clarifying_question":false,"clarifying_question":null,"suggested_output":"concise"}'
    out = extract_json(text)
    assert isinstance(out, dict)
    assert out["intent"] == "casual_curiosity"
    assert out["confidence"] == 0.7


def test_extract_json_object_with_leading_and_trailing_text():
    text = """
Sure! Here is the result:
{
  "intent": "guided_study",
  "confidence": 0.85,
  "rationale": "User wants a structured plan",
  "suggested_output": "detailed",
  "should_ask_clarifying_question": false,
  "clarifying_question": null
}
Hope this helps.
"""
    out = extract_json(text)
    assert out["intent"] == "guided_study"
    assert out["should_ask_clarifying_question"] is False


def test_extract_json_object_prefers_fenced_json_block():
    text = """
Some explanation first.

```json
{
  "intent": "professional_research",
  "confidence": 0.8,
  "rationale": "Request mentions papers and comparison",
  "suggested_output": "detailed",
  "should_ask_clarifying_question": false,
  "clarifying_question": null
}
```

Some extra trailing words.
"""
    out = extract_json(text)
    assert out["intent"] == "professional_research"
    assert out["suggested_output"] == "detailed"


def test_extract_json_object_handles_nested_braces():
    # This is the classic bug: naive find("{") + find("}") breaks here.
    text = """
```json
{
  "goal": "Learn RL",
  "steps": [
    {
      "type": "research",
      "tool_calls": [
        {"tool": "web_search", "query": "reinforcement learning basics", "top_k": 3}
      ]
    }
  ],
  "notes": "ok"
}
```
"""
    out = extract_json(text)
    assert out["goal"] == "Learn RL"
    assert isinstance(out["steps"], list)
    assert out["steps"][0]["tool_calls"][0]["tool"] == "web_search"


def test_extract_json_object_ignores_non_json_curly_braces():
    text = """
This is not JSON: {hello world}.
But below is JSON:

{
"a": 1,
"b": 2
}
"""
    out = extract_json(text)
    assert out == {"a": 1, "b": 2}


def test_extract_json_object_multiple_json_objects_returns_first_valid():
    text = """
First:
{"a": 1}

Second:
{"b": 2}
"""
    out = extract_json(text)
    assert out == {"a": 1}


def test_extract_json_object_with_single_quotes_should_fail():
    # LLM sometimes outputs Python dict style; we should fail fast.
    text = "{'a': 1, 'b': 2}"
    out = extract_json(text)
    assert out is None


def test_extract_json_object_invalid_json_returns_none():
    # trailing comma or comment makes it invalid JSON
    text="""
{
  "a": 1,
  "b": 2,   
}
"""
    out = extract_json(text)
    assert out is None


def test_extract_json_object_handles_no_json_text():
    text = "This is not JSON."
    out = extract_json(text)
    assert out is None


def test_extract_json_object_handles_empty_string():
    text = ""
    out = extract_json(text)
    assert out is None


def test_extract_json_object_handles_none():
    text = None
    out = extract_json(text)
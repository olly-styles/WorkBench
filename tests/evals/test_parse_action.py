import pytest

from src.evals import agent
from src.evals.agent import PARSE_ERROR, parse_action


def test_parse_action_fenced_tool_call():
    text = '```json\n{"action": "calendar.search_events", "action_input": {"query": "x"}}\n```'
    action, action_input = parse_action(text)
    assert action == "calendar.search_events"
    assert action_input == {"query": "x"}


def test_parse_action_fenced_final_answer():
    text = '```json\n{"action": "Final Answer", "action_input": "done"}\n```'
    action, action_input = parse_action(text)
    assert action == "Final Answer"
    assert action_input == "done"


def test_parse_action_bare_object_without_fence():
    text = 'Thought: I will search.\n{"action": "calendar.search_events", "action_input": {"query": "x"}}'
    action, action_input = parse_action(text)
    assert action == "calendar.search_events"
    assert action_input == {"query": "x"}


def test_parse_action_plain_prose_is_final_answer():
    action, action_input = parse_action("The answer is 42.")
    assert action == "Final Answer"
    assert action_input == "The answer is 42."


def test_parse_action_malformed_json_returns_parse_error_without_raising():
    text = '```json\n{"action": "x", "action_input": }\n```'
    action, action_input = parse_action(text)
    assert action == PARSE_ERROR
    assert isinstance(action_input, str)


def test_parse_action_non_dict_json_returns_parse_error():
    action, _ = parse_action("```json\n123\n```")
    assert action == PARSE_ERROR


def test_parse_action_malformed_bare_object_returns_parse_error():
    action, action_input = parse_action('Thought: do it\n{"action": "x", "action_input": }')
    assert action == PARSE_ERROR
    assert isinstance(action_input, str)


def test_run_agent_recovers_from_malformed_action(monkeypatch: pytest.MonkeyPatch):
    responses = iter(
        [
            '```json\n{"action": "calendar.search_events", "action_input": }\n```',
            '```json\n{"action": "Final Answer", "action_input": "recovered"}\n```',
        ]
    )
    monkeypatch.setattr(agent, "call_llm", lambda *args, **kwargs: next(responses))
    result = agent.run_agent("gpt-4", [], "task", "")
    assert result.output == "recovered"
    assert any(step.action == PARSE_ERROR for step in result.trace)
    assert all(action != PARSE_ERROR for action, _ in result.intermediate_steps)

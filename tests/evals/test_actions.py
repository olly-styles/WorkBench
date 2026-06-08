from src.evals.actions import (
    _TOOL_DISPATCH,
    convert_intermediate_step_to_function_call,
    execute_actions_and_reset_state,
)
from src.tools.state import get_state, reset_state
from src.tools.toolkits import all_tools


def test_convert_intermediate_step_simple():
    result = convert_intermediate_step_to_function_call(
        "calendar.create_event",
        {"event_name": "Standup", "duration": "30"},
    )
    assert result == 'calendar.create_event.func(event_name="Standup", duration="30")'


def test_convert_intermediate_step_escapes_quotes():
    result = convert_intermediate_step_to_function_call(
        "email.send_email",
        {"body": 'He said "hello"'},
    )
    assert r"\"hello\"" in result


def test_convert_intermediate_step_escapes_newlines():
    result = convert_intermediate_step_to_function_call(
        "email.send_email",
        {"body": "line1\nline2"},
    )
    assert r"\n" in result
    assert "\n" not in result.split("(", 1)[1]


def test_dispatch_table_covers_all_tools():
    registered_names = {t.name for t in all_tools}
    dispatch_names = set(_TOOL_DISPATCH.keys())
    assert registered_names == dispatch_names


def test_execute_actions_and_reset_state_returns_tuple():
    result = execute_actions_and_reset_state([])
    assert len(result) == 6
    assert result[0] is True


def test_execute_actions_creates_event():
    action = "calendar.create_event.func(event_name='Test', participant_email='test@atlas.com', event_start='2023-10-02 12:00:00', duration='60')"
    success, cal_state, _, _, _, _ = execute_actions_and_reset_state([action])
    assert success
    assert any(cal_state["event_name"].str.contains("Test"))
    state = get_state()
    assert not any(state.calendar_events["event_name"].str.contains("Test"))
    reset_state()


def test_execute_actions_invalid_action_marks_failure_but_continues():
    actions = [
        "not_valid_python!!!",
        "calendar.create_event.func(event_name='Valid', participant_email='test@atlas.com', event_start='2023-10-02 12:00:00', duration='60')",
    ]
    success, cal_state, _, _, _, _ = execute_actions_and_reset_state(actions)
    assert not success
    assert any(cal_state["event_name"].str.contains("Valid"))
    reset_state()


def test_execute_actions_disallowed_tool_marks_failure():
    success, *_ = execute_actions_and_reset_state(["foo.bar.func(x='1')"])
    assert not success
    reset_state()


def test_execute_actions_wrong_kwarg_marks_failure():
    success, *_ = execute_actions_and_reset_state(["calendar.create_event.func(unknown_kwarg='x')"])
    assert not success
    reset_state()

from src.tools.calendar import create_event
from src.tools.state import get_state

_LEAK_EVENT = "State isolation leak probe"


def test_mutate_state_without_explicit_cleanup():
    create_event(_LEAK_EVENT, "probe@atlas.com", "2023-10-02 12:00:00", "60")
    assert (get_state().calendar_events["event_name"] == _LEAK_EVENT).any()


def test_state_is_reset_between_tests_despite_no_inline_cleanup():
    assert not (get_state().calendar_events["event_name"] == _LEAK_EVENT).any()

import pandas as pd
import pytest

from src.tools import calendar


calender_events = pd.read_csv("data/processed/calender_events.csv")


def test_get_event_information_by_id():
    """
    Tests get_event_information_by_id.
    """
    assert calendar.get_event_information_by_id.func("70838584", "event_name") == {
        "event_name": "Board of Directors Meeting"
    }


def test_get_event_information_by_id_no_id():
    """
    Tests get_event_information_by_id with no ID.
    """
    with pytest.raises(TypeError):
        calendar.get_event_information_by_id.func()


def test_get_event_information_by_id_no_field():
    """
    Tests get_event_information_by_id with no field raises a TypeError.
    """
    with pytest.raises(TypeError):
        calendar.get_event_information_by_id.func("70838584")


def test_get_event_information_by_id_field_not_found():
    """
    Tests get_event_information_by_id with field not found.
    """
    event = calendar.get_event_information_by_id.func(
        "70838584", "field_does_not_exist"
    )
    assert event == "Field not found."

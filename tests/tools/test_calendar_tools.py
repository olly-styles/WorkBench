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
    assert calendar.get_event_information_by_id.func() == "Event ID not provided."


def test_get_event_information_by_id_no_field():
    """
    Tests get_event_information_by_id with no field raises a TypeError.
    """
    assert (
        calendar.get_event_information_by_id.func("70838584") == "Field not provided."
    )


def test_get_event_information_by_id_field_not_found():
    """
    Tests get_event_information_by_id with field not found.
    """
    event = calendar.get_event_information_by_id.func(
        "70838584", "field_does_not_exist"
    )
    assert event == "Field not found."


def test_search_events():
    """
    Tests search_events.
    """
    assert calendar.search_events.func("Yuki")[0] == {
        "event_id": "70838584",
        "event_name": "Board of Directors Meeting",
        "participant_email": "Yuki.Tanaka@company.com",
        "event_start": "2023-10-01 10:00:00",
        "event_end": "2023-10-01 11:00:00",
    }


def test_search_for_event_no_results():
    """
    Tests search_events with no results.
    """
    assert calendar.search_events.func("event_does_not_exist") == "No events found."


def test_search_for_event_time_max():
    """
    Tests search_events with time_min.
    """
    assert calendar.search_events.func(time_max="2023-10-01 11:00:00") == [
        {
            "event_id": "70838584",
            "event_name": "Board of Directors Meeting",
            "participant_email": "Yuki.Tanaka@company.com",
            "event_start": "2023-10-01 10:00:00",
            "event_end": "2023-10-01 11:00:00",
        }
    ]

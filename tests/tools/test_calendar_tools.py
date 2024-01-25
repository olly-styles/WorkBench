import pandas as pd
import pytest

from src.tools import calendar

test_events = [
    {
        "event_id": "70838584",
        "event_name": "Board of Directors Meeting",
        "participant_email": "Yuki.Tanaka@company.com",
        "event_start": "2023-10-01 10:00:00",
        "duration": "60",
    },
    {
        "event_id": "70838585",
        "event_name": "Meeting with Sam",
        "participant_email": "sam@company.com",
        "event_start": "2023-10-02 11:00:00",
        "duration": "60",
    },
]
calendar.CALENDAR_EVENTS = pd.DataFrame(test_events)


def test_get_event_information_by_id():
    """
    Tests get_event_information_by_id.
    """
    assert calendar.get_event_information_by_id.func("70838584", "event_name") == {
        "event_name": "Board of Directors Meeting"
    }


def test_get_event_information_missing_arguments():
    """
    Tests get_event_information_by_id with no ID and no field.
    """
    assert calendar.get_event_information_by_id.func() == "Event ID not provided."
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
        "duration": "60",
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
            "duration": "60",
        }
    ]


def test_create_event():
    """
    Tests create_event.
    """
    assert (
        calendar.create_event.func(
            "Meeting with Sam",
            "sam@company.com",
            "2023-10-01 10:00:00",
            "60",
        )
        == "70838586"
    )
    assert calendar.CALENDAR_EVENTS.iloc[-1]["event_name"] == "Meeting with Sam"


def test_create_event_missing_args():
    """
    Tests create_event with no event name, participant email, event start, and event end.
    """
    assert calendar.create_event.func() == "Event name not provided."
    assert (
        calendar.create_event.func("Meeting with Sam")
        == "Participant email not provided."
    )
    assert (
        calendar.create_event.func("Meeting with Sam", "sam@company.com")
        == "Event start not provided."
    )
    assert (
        calendar.create_event.func(
            "Meeting with Sam", "sam@company.com", "2023-10-01 10:00:00"
        )
        == "Event duration not provided."
    )


def test_delete_event():
    """
    Tests delete_event.
    """
    assert calendar.delete_event.func("70838585") == "Event deleted successfully."
    assert "70838585" not in calendar.CALENDAR_EVENTS["event_id"].values


def test_delete_event_no_id_provided():
    """
    Tests delete_event with no event_id provided.
    """
    assert calendar.delete_event.func() == "Event ID not provided."


def test_delete_event_not_found():
    """
    Tests delete_event with an event_id that does not exist.
    """
    assert calendar.delete_event.func("00000000") == "Event not found."


def test_update_event():
    """
    Tests update_event.
    """
    assert (
        calendar.update_event.func("70838584", "event_name", "New Event Name")
        == "Event updated successfully."
    )
    assert (
        calendar.CALENDAR_EVENTS.loc[
            calendar.CALENDAR_EVENTS["event_id"] == "70838584", "event_name"
        ].values[0]
        == "New Event Name"
    )


def test_update_event_no_id_provided():
    """
    Tests update_event with no event_id provided.
    """
    assert (
        calendar.update_event.func(None, "event_name", "New Event Name")
        == "Event ID, field, or new value not provided."
    )


def test_update_event_not_found():
    """
    Tests update_event with an event_id that does not exist.
    """
    assert (
        calendar.update_event.func("99999999", "event_name", "New Event Name")
        == "Event not found."
    )

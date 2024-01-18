import pandas as pd
import pytest

from src.tools import calendar

test_events = [
    {
        "event_id": "70838584",
        "event_name": "Board of Directors Meeting",
        "participant_email": "Yuki.Tanaka@company.com",
        "event_start": "2023-10-01 10:00:00",
        "event_end": "2023-10-01 11:00:00",
    },
    {
        "event_id": "70838585",
        "event_name": "Meeting with Sam",
        "participant_email": "sam@company.com",
        "event_start": "2023-10-02 11:00:00",
        "event_end": "2023-10-02 12:00:00",
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


def create_event(
    event_name=None, participant_email=None, event_start=None, event_end=None
):
    """
    Creates a new event.

    Parameters
    ----------
    event_name: str, optional
        Name of the event.
    participant_email: str, optional
        Email of the participant.
    event_start: str, optional
        Start time of the event. Format: "YYYY-MM-DD HH:MM:SS"
    event_end: str, optional
        End time of the event. Format: "YYYY-MM-DD HH:MM:SS"

    Returns
    -------
    event_id : str
        ID of the newly created event.

    Examples
    --------
    >>> create_event("Meeting with Sam", "sam@example.com", "2021-06-01 13:00:00", "2021-06-01 14:00:00")
    "00000000"
    """

    if not event_name:
        return "Event name not provided."
    if not participant_email:
        return "Participant email not provided."
    if not event_start:
        return "Event start not provided."
    if not event_end:
        return "Event end not provided."

    event_id = str(CALENDAR_EVENTS["event_id"].max() + 1).zfill(8)
    new_event = pd.DataFrame(
        {
            "event_id": [event_id],
            "event_name": [event_name],
            "participant_email": [participant_email],
            "event_start": [event_start],
            "event_end": [event_end],
        }
    )
    CALENDAR_EVENTS = pd.concat([CALENDAR_EVENTS, new_event])
    return event_id


def test_create_event():
    """
    Tests create_event.
    """
    assert (
        calendar.create_event.func(
            "Meeting with Sam",
            "sam@company.com",
            "2023-10-01 10:00:00",
            "2023-10-01 11:00:00",
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
        == "Event end not provided."
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

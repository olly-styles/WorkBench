import json
from collections.abc import Mapping, Sequence

import pandas as pd

from src.tools import calendar
from src.tools.state import get_state

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


def _set_calendar(events: Sequence[Mapping[str, str]]):
    get_state().calendar_events = pd.DataFrame(events)


def test_get_event_information_by_id():
    """
    Tests get_event_information_by_id.
    """
    _set_calendar(test_events)
    assert calendar.get_event_information_by_id("70838584", "event_name") == json.dumps(
        {"event_name": "Board of Directors Meeting"}
    )


def test_get_event_information_missing_arguments():
    """
    Tests get_event_information_by_id with no ID and no field.
    """
    _set_calendar(test_events)
    assert calendar.get_event_information_by_id() == "Event ID not provided."
    assert calendar.get_event_information_by_id("70838584") == "Field not provided."


def test_get_event_information_by_id_field_not_found():
    """
    Tests get_event_information_by_id with field not found.
    """
    _set_calendar(test_events)
    event = calendar.get_event_information_by_id("70838584", "field_does_not_exist")
    assert event == "Field not found."


def test_search_events():
    """
    Tests search_events.
    """
    _set_calendar(test_events)
    assert json.loads(calendar.search_events("Yuki"))[0] == {
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
    _set_calendar(test_events)
    assert json.loads(calendar.search_events("event_does_not_exist")) == []


def test_search_events_result_limit():
    """
    Tests search_events returns at most 5 results.
    """
    many_events = [
        {
            "event_id": f"7083858{i}",
            "event_name": "Standup",
            "participant_email": "test@company.com",
            "event_start": f"2023-10-0{i + 1} 10:00:00",
            "duration": "30",
        }
        for i in range(7)
    ]
    _set_calendar(many_events)
    results = json.loads(calendar.search_events("Standup"))
    assert len(results) == 5


def test_search_for_event_time_max():
    """
    Tests search_events with time_max.
    """
    _set_calendar(test_events)
    assert json.loads(calendar.search_events(time_max="2023-10-01 11:00:00")) == [
        {
            "event_id": "70838584",
            "event_name": "Board of Directors Meeting",
            "participant_email": "Yuki.Tanaka@company.com",
            "event_start": "2023-10-01 10:00:00",
            "duration": "60",
        }
    ]


def test_search_for_event_time_during_meeting():
    """
    Tests search_events with time_max where the time is during a meeting. We should still returning the meeting if it is ongoing.
    """
    _set_calendar(test_events)
    assert json.loads(calendar.search_events(time_max="2023-10-02 11:30:00")) == [
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


def test_search_for_event_time_min_during_meeting():
    """
    Tests search_events with time_min set to a time during an ongoing meeting. The meeting started before
    time_min but ends after it, so it should still be returned (time_min bounds the event's end time).
    """
    _set_calendar(test_events)
    results = json.loads(calendar.search_events(time_min="2023-10-01 10:30:00"))
    assert results == [
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


def test_search_for_event_time_min_after_meeting_ends():
    """
    Tests search_events with time_min set after a meeting has ended. The meeting should be excluded.
    """
    _set_calendar(test_events)
    results = json.loads(calendar.search_events(time_min="2023-10-01 11:00:01"))
    assert results == [
        {
            "event_id": "70838585",
            "event_name": "Meeting with Sam",
            "participant_email": "sam@company.com",
            "event_start": "2023-10-02 11:00:00",
            "duration": "60",
        }
    ]


def test_create_event():
    """
    Tests create_event.
    """
    _set_calendar(test_events)
    assert (
        calendar.create_event(
            "Meeting with Sam",
            "sam@company.com",
            "2023-10-01 10:00:00",
            "60",
        )
        == "70838586"
    )
    assert get_state().calendar_events.iloc[-1]["event_name"] == "Meeting with Sam"


def test_create_event_missing_args():
    """
    Tests create_event with no event name, participant email, event start, and event end.
    """
    _set_calendar(test_events)
    assert calendar.create_event() == "Event name not provided."
    assert calendar.create_event("Meeting with Sam") == "Participant email not provided."
    assert calendar.create_event("Meeting with Sam", "sam@company.com") == "Event start not provided."
    assert (
        calendar.create_event("Meeting with Sam", "sam@company.com", "2023-10-01 10:00:00")
        == "Event duration not provided."
    )


def test_delete_event():
    """
    Tests delete_event.
    """
    _set_calendar(test_events)
    assert calendar.delete_event("70838585") == "Event deleted successfully."
    assert "70838585" not in get_state().calendar_events["event_id"].values


def test_delete_event_no_id_provided():
    """
    Tests delete_event with no event_id provided.
    """
    assert calendar.delete_event() == "Event ID not provided."


def test_delete_event_not_found():
    """
    Tests delete_event with an event_id that does not exist.
    """
    _set_calendar(test_events)
    assert calendar.delete_event("00000000") == "Event not found."


def test_update_event():
    """
    Tests update_event.
    """
    _set_calendar(test_events)
    assert calendar.update_event("70838584", "event_name", "New Event Name") == "Event updated successfully."
    assert (
        get_state().calendar_events.loc[get_state().calendar_events["event_id"] == "70838584", "event_name"].values[0]
        == "New Event Name"
    )


def test_update_event_no_id_provided():
    """
    Tests update_event with no event_id provided.
    """
    _set_calendar(test_events)
    assert calendar.update_event(None, "event_name", "New Event Name") == "Event ID, field, or new value not provided."


def test_update_event_not_found():
    """
    Tests update_event with an event_id that does not exist.
    """
    _set_calendar(test_events)
    assert calendar.update_event("99999999", "event_name", "New Event Name") == "Event not found."

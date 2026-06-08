import json

import pandas as pd

from src.tools._utils import (
    DEFAULT_SEARCH_RESULT_LIMIT,
    delete_record,
    generate_next_id,
    get_record_field,
    normalize_email,
)
from src.tools.state import get_state
from src.tools.tool import tool


@tool("calendar.get_event_information_by_id")
def get_event_information_by_id(event_id: str | None = None, field: str | None = None) -> str:
    """
    Returns the event for a given ID.

    Parameters
    ----------
    event_id : str, optional
        8-digit ID of the event.
    field : str, optional
        Field to return. Available fields are: "event_id", "event_name", "participant_email", "event_start", "duration"

    Returns
    -------
    event : dict
        Event information for the given ID and field.


    Examples
    --------
    >>> calendar.get_event_information_by_id("00000000", "event_name")
    {{"event_name": "Meeting with Sam"}}

    >>> calendar.get_event_information_by_id("00000000", "event_start")
    {{"event_start": "2021-06-01 13:00:00"}}

    >>> calendar.get_event_information_by_id("00000000", "duration")
    {{"duration": "60"}}

    """
    return get_record_field(get_state().calendar_events, "event_id", event_id, field, "Event")


@tool("calendar.search_events")
def search_events(query: str = "", time_min: str | None = None, time_max: str | None = None) -> str:
    """
    Returns the events for a given query.

    Parameters
    ----------
    query: str, optional
        Query to search for. Terms will be matched in the event_name and participant_email fields.
    time_min: str, optional
        Lower bound (inclusive) for an event's end time to filter by. Format: "YYYY-MM-DD HH:MM:SS"
    time_max: str, optional
        Upper bound (inclusive) for an event's start time to filter by. Format: "YYYY-MM-DD HH:MM:SS

    Returns
    -------
    events : list
        List of events matching the query. Returns at most 5 events.

    Examples
    --------
    >>> calendar.search_events("Sam")
    [{{"event_id": "00000000", "event_name": "Meeting with Sam", "participant_email: "sam@example.com", "event_start": "2021-06-01 13:00:00", "duration": "60"}},
    {{"event_id": "00000001", "event_name": "Lunch with Sam", "participant_email": "sam@example.com", "event_start": "2021-06-01 13:00:00", "duration": "30}}"
    ]
    """
    state = get_state()
    events = state.calendar_events[
        (state.calendar_events["event_name"].str.contains(query, case=False, regex=False))
        | (state.calendar_events["participant_email"].str.contains(query, case=False, regex=False))
    ].to_dict(orient="records")
    if time_min:
        events = [
            event
            for event in events
            if pd.Timestamp(event["event_start"]) + pd.Timedelta(minutes=int(event["duration"]))
            >= pd.Timestamp(time_min)
        ]
    if time_max:
        events = [event for event in events if pd.Timestamp(event["event_start"]) <= pd.Timestamp(time_max)]
    return json.dumps(events[:DEFAULT_SEARCH_RESULT_LIMIT])


@tool("calendar.create_event")
def create_event(
    event_name: str | None = None,
    participant_email: str | None = None,
    event_start: str | None = None,
    duration: str | None = None,
) -> str:
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
    duration: str, optional
        Duration of the event in minutes.

    Returns
    -------
    event_id : str
        ID of the newly created event.

    Examples
    --------
    >>> calendar.create_event("Meeting with Sam", "sam@example.com", "2021-06-01 13:00:00", "60")
    "00000000"
    """
    state = get_state()

    if not event_name:
        return "Event name not provided."
    if not participant_email:
        return "Participant email not provided."
    if not event_start:
        return "Event start not provided."
    if not duration:
        return "Event duration not provided."

    participant_email = normalize_email(participant_email)

    event_id = generate_next_id(state.calendar_events, "event_id")
    new_event = pd.DataFrame(
        {
            "event_id": [event_id],
            "event_name": [event_name],
            "participant_email": [participant_email],
            "event_start": [event_start],
            "duration": [duration],
        }
    )
    state.calendar_events = pd.concat([state.calendar_events, new_event], ignore_index=True)
    return event_id


@tool("calendar.delete_event")
def delete_event(event_id: str | None = None) -> str:
    """
    Deletes an event.

    Parameters
    ----------
    event_id: str, optional
        8-digit ID of the event.

    Returns
    -------
    message : str
        Message indicating whether the deletion was successful.

    Examples
    --------
    >>> calendar.delete_event("00000000")
    "Event deleted successfully."

    """
    state = get_state()
    state.calendar_events, message = delete_record(state.calendar_events, "event_id", event_id, "Event")
    return message


@tool("calendar.update_event")
def update_event(event_id: str | None = None, field: str | None = None, new_value: str | None = None) -> str:
    """
    Updates an event.

    Parameters
    ----------
    event_id: str, optional
        8-digit ID of the event.
    field: str, optional
        Field to update. Available fields are: "event_name", "participant_email", "event_start", "duration".
    new_value: str, optional
        New value for the field.

    Returns
    -------
    message : str
        Message indicating whether the update was successful.

    Examples
    --------
    >>> calendar.update_event("00000000", "event_name", "New Event Name")
    "Event updated successfully."

    """
    state = get_state()

    if not event_id or not field or not new_value:
        return "Event ID, field, or new value not provided."
    if event_id not in state.calendar_events["event_id"].values:
        return "Event not found."
    if field == "participant_email":
        new_value = normalize_email(new_value)
    state.calendar_events.loc[state.calendar_events["event_id"] == event_id, field] = new_value
    return "Event updated successfully."

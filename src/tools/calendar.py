import pandas as pd
from langchain.tools import tool

CALENDAR_EVENTS = pd.read_csv("data/processed/calender_events.csv", dtype=str)


@tool("calendar.get_event_information_by_id", return_direct=False)
def get_event_information_by_id(event_id, field):
    """
    Returns the event for a given ID.

    Parameters
    ----------
    event_id : str
        ID of the event.
    field : str
        Field to return. Available fields are: "event_id", "event_name", "participant_email", "event_start", "event_end"

    Returns
    -------
    event : dict
        Event information for the given ID and field.


    Examples
    --------
    >>> get_event_information_by_id("0001", "event_name")
    {{"event_name": "Meeting with Sam"}}

    >>> get_event_information_by_id("0001", "event_start")
    {{"event_start": "2021-06-01 13:00:00"}}

    """
    event = CALENDAR_EVENTS[CALENDAR_EVENTS["event_id"] == event_id].to_dict(
        orient="records"
    )
    if event:
        if field in event[0]:
            return {field: event[0][field]}
        else:
            return "Field not found."
    else:
        return "Event not found."

import pandas as pd

CALENDAR_EVENTS = pd.read_csv("data/processed/calender_events.csv", dtype=str)


def get_event_information_by_id(args):
    """
    Returns the event for a given ID.

    Parameters
    ----------
    args : dict
        JSON object with the following keys:
            - id: str
                ID of the event.
            - field: str
                Field of the event to return.

    Returns
    -------
    event : dict
        JSON object with the following keys:
            - event_id: str
                ID of the event.
            - event_name: str
                Name of the event.
            - participant_email: str
                Email of the participant.
            - event_start: str
                Start date of the event.
            - event_end: str
                End date of the event.
    """
    if "id" not in args:
        return "No ID provided."
    if "field" not in args:
        return "No field provided."

    event_id = args["id"]
    field = args["field"]
    event = CALENDAR_EVENTS[CALENDAR_EVENTS["event_id"] == event_id].to_dict(
        orient="records"
    )
    if event:
        if field in event[0]:
            return {field: event[0][field]}
        else:
            return "Field not found."
    else:
        return {}

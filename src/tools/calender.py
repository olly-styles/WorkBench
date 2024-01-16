import pandas as pd

CALENDAR_EVENTS = pd.read_csv("data/processed/calender_events.csv", dtype=str)


def get_event_by_id(args):
    """
    Returns the event for a given ID.

    Parameters
    ----------
    args : dict
        JSON object with the following keys:
            - id: str
                ID of the event.

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

    event_id = args["id"]
    event = CALENDAR_EVENTS[CALENDAR_EVENTS["event_id"] == event_id].to_dict(
        orient="records"
    )
    if event:
        return event[0]
    else:
        return {}

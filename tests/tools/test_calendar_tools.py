import pandas as pd

from src.tools.calender import get_event_by_id


calender_events = pd.read_csv("data/processed/calender_events.csv")


def test_get_event_by_id():
    """
    Tests get_event_by_id.
    """
    args = {"id": "0395"}
    event = get_event_by_id(args)
    assert event["event_id"] == "0395"
    assert event["event_name"] == "Digital Transformation Summit"
    assert event["participant_email"] == "Fatima.Khan@company.com"
    assert event["event_start"] == "2023-10-01 09:00:00"
    assert event["event_end"] == "2023-10-01 09:30:00"

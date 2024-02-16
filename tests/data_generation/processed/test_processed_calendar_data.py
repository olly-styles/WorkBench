import pandas as pd

calendar_events = pd.read_csv("data/processed/calendar_events.csv").sort_values("event_start")


def test_no_two_events_overlap():
    """
    Tests that no two events overlap.
    """
    for i in range(len(calendar_events) - 1):
        event_start = pd.to_datetime(calendar_events.iloc[i]["event_start"])
        event_end = event_start + pd.Timedelta(calendar_events.iloc[i]["duration"], unit="m")
        next_event_start = pd.to_datetime(calendar_events.iloc[i + 1]["event_start"])
        next_event_end = next_event_start + pd.Timedelta(calendar_events.iloc[i + 1]["duration"], unit="m")
        assert event_end <= next_event_start or next_event_end <= event_start


def test_no_two_events_same_name_same_day():
    """
    Tests that no two events with the same name are on the same day.
    """
    calendar_events["date"] = pd.to_datetime(calendar_events.event_start).dt.date
    grouped = calendar_events.groupby(["date", "event_name"]).size()
    assert len(grouped[grouped > 1]) == 0
    del calendar_events["date"]

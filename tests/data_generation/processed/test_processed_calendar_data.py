import pandas as pd

calendar_events = pd.read_csv("data/processed/calendar_events.csv").sort_values(
    "event_start"
)


def test_no_two_events_overlap():
    """
    Tests that no two events overlap.
    """
    for i in range(len(calendar_events) - 1):
        event_start = pd.to_datetime(calendar_events.iloc[i]["event_start"])
        event_end = event_start + pd.Timedelta(
            calendar_events.iloc[i]["duration"], unit="m"
        )
        next_event_start = pd.to_datetime(calendar_events.iloc[i + 1]["event_start"])
        next_event_end = next_event_start + pd.Timedelta(
            calendar_events.iloc[i + 1]["duration"], unit="m"
        )
        assert event_end <= next_event_start or next_event_end <= event_start

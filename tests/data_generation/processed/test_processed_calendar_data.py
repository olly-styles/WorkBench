import pandas as pd

calendar_events = pd.read_csv("data/processed/calendar_events.csv").sort_values(
    "event_start"
)


def test_no_two_events_overlap():
    # Sort the events by start time

    for i in range(len(calendar_events) - 1):
        current_event_end = pd.to_datetime(calendar_events.iloc[i]["event_end"])
        next_event_start = pd.to_datetime(calendar_events.iloc[i + 1]["event_start"])
        assert (
            current_event_end <= next_event_start
        ), f"Event {i+1} overlaps with the next event {current_event_end} {next_event_start}"

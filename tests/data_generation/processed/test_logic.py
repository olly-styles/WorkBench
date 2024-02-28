import pandas as pd
from src.data_generation.data_generation_utils import get_first_free_slot


def test_get_first_free_slot_between_others():
    meetings_df = pd.DataFrame(
        {
            "event_id": ["00000001", "00000002", "00000003"],
            "event_start": ["2022-01-01 09:00:00", "2022-01-01 10:00:00", "2022-01-01 11:00:00"],
            "duration": ["60", "30", "30"],
        }
    )
    date = pd.to_datetime("2022-01-01 09:00:00")
    assert get_first_free_slot(date, meetings_df, duration_minutes=30) == pd.to_datetime("2022-01-01 10:30:00")
    assert get_first_free_slot(date, meetings_df, duration_minutes=120) == pd.to_datetime("2022-01-01 11:30:00")


def test_get_first_free_slot_no_meetings():
    meetings_df = pd.DataFrame(columns=["event_id", "event_start", "duration"])
    date = pd.to_datetime("2022-01-01 09:00:00")
    assert get_first_free_slot(date, meetings_df, duration_minutes=30) == pd.to_datetime("2022-01-01 09:00:00")


def test_get_first_free_slot_no_free_slot():
    meetings_df = pd.DataFrame(
        {
            "event_id": ["00000001", "00000002", "00000003", "00000004", "00000005"],
            "event_start": [
                "2022-01-01 09:00:00",
                "2022-01-01 11:00:00",
                "2022-01-01 13:00:00",
                "2022-01-01 15:00:00",
                "2022-01-01 17:00:00",
            ],
            "duration": ["60", "60", "60", "60", "60"],
        }
    )
    date = pd.to_datetime("2022-01-01 09:00:00")
    assert get_first_free_slot(date, meetings_df, duration_minutes=120) == None

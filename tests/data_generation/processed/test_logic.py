import pandas as pd
from src.data_generation.data_generation_utils import get_first_free_slot


def test_get_first_free_slot():
    meetings_df = pd.DataFrame(
        {
            "event_id": ["00000001", "00000002", "00000003"],
            "event_start": ["2022-01-01 09:00:00", "2022-01-01 10:00:00", "2022-01-01 11:00:00"],
            "duration": ["60", "30", "30"],
        }
    )
    assert get_first_free_slot(meetings_df) == pd.to_datetime("2022-01-01 10:30:00")

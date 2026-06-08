import random

import numpy as np
import pandas as pd

from src.data_generation.data_generation_utils import (
    format_event_duration,
    generate_datetime_between,
    generate_end_time,
    generate_event_duration_minutes,
    get_first_free_slot,
    get_first_name,
    get_natural_language_date,
    get_natural_language_time,
    random_choice_excluding,
)


def test_generate_datetime_between_within_range():
    np.random.seed(42)
    start = pd.to_datetime("2023-10-01T00:00:00")
    end = pd.to_datetime("2023-10-31T23:59:59")
    for _ in range(20):
        dt = generate_datetime_between(start, end)
        assert start <= dt <= end


def test_generate_datetime_between_nearest_30_minutes():
    np.random.seed(42)
    start = pd.to_datetime("2023-10-01T00:00:00")
    end = pd.to_datetime("2023-10-31T23:59:59")
    for _ in range(20):
        dt = generate_datetime_between(start, end, nearest_30_minutes=True)
        assert dt.minute in [0, 30]
        assert dt.second == 0


def test_generate_datetime_between_not_nearest_30():
    np.random.seed(42)
    start = pd.to_datetime("2023-10-01T00:00:00")
    end = pd.to_datetime("2023-10-31T23:59:59")
    minutes_seen = set()
    for _ in range(50):
        dt = generate_datetime_between(start, end, nearest_30_minutes=False)
        minutes_seen.add(dt.minute)
    assert len(minutes_seen) > 2


def test_generate_datetime_between_february():
    np.random.seed(42)
    start = pd.to_datetime("2023-02-01T00:00:00")
    end = pd.to_datetime("2023-02-28T23:59:59")
    for _ in range(20):
        dt = generate_datetime_between(start, end)
        assert dt.day <= 28


def test_generate_datetime_between_work_hours():
    np.random.seed(42)
    start = pd.to_datetime("2023-10-01T00:00:00")
    end = pd.to_datetime("2023-10-31T23:59:59")
    for _ in range(20):
        dt = generate_datetime_between(start, end)
        assert 9 <= dt.hour <= 15


def test_get_first_free_slot_empty_day():
    events = pd.DataFrame(columns=pd.Index(["event_start", "duration"]))
    slot = get_first_free_slot("2023-12-01", events, 30)
    assert slot == pd.to_datetime("2023-12-01 09:00:00")


def test_get_first_free_slot_with_morning_event():
    events = pd.DataFrame(
        {
            "event_start": ["2023-12-01 09:00:00"],
            "duration": ["60"],
        }
    )
    slot = get_first_free_slot("2023-12-01", events, 30)
    assert slot == pd.to_datetime("2023-12-01 10:00:00")


def test_get_first_free_slot_full_day():
    events = pd.DataFrame(
        {
            "event_start": ["2023-12-01 09:00:00"],
            "duration": ["540"],
        }
    )
    slot = get_first_free_slot("2023-12-01", events, 30)
    assert slot is None


def test_get_first_name_standard():
    assert get_first_name("alice.smith@atlas.com") == "alice"


def test_get_first_name_no_dot():
    assert get_first_name("alice@atlas.com") == "alice"


def test_random_choice_excluding():
    random.seed(42)
    collection = ["a", "b", "c"]
    for _ in range(20):
        result = random_choice_excluding(collection, "a")
        assert result != "a"
        assert result in collection


def test_random_choice_excluding_two_items():
    random.seed(42)
    collection = ["a", "b"]
    for _ in range(20):
        result = random_choice_excluding(collection, "a")
        assert result == "b"


def test_get_natural_language_date():
    assert get_natural_language_date("2023-01-01") == "January 1"
    assert get_natural_language_date("2023-12-25") == "December 25"


def test_get_natural_language_time():
    assert get_natural_language_time("09:30:00") == "9:30"
    assert get_natural_language_time("13:00:00") == "1"
    assert get_natural_language_time("15:30:00") == "3:30"


def test_format_event_duration():
    assert format_event_duration(30) == "30 minute"
    assert format_event_duration(60) == "1 hour"
    assert format_event_duration(90) == "1.5 hour"
    assert format_event_duration(120) == "2 hour"


def test_generate_event_duration_minutes():
    np.random.seed(42)
    for _ in range(20):
        minutes = generate_event_duration_minutes()
        assert minutes in [30, 60, 90, 120]


def test_generate_end_time():
    assert generate_end_time("2023-12-01 09:00:00", "60 minutes") == "2023-12-01 10:00:00"
    assert generate_end_time("2023-12-01 09:00:00", "30 minutes") == "2023-12-01 09:30:00"

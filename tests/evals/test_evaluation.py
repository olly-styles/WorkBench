from src.evals.evaluation import (
    end_date_minor_error,
    get_function_name,
    is_exact_match,
    meeting_start_time_error,
)


def test_get_function_name():
    assert get_function_name("calendar.create_event.func(event_name='Test')") == "calendar.create_event"
    assert get_function_name("email.send_email.func(recipient='a@b.com')") == "email.send_email"


def test_is_exact_match_identical():
    pred = ["calendar.create_event.func(event_name='Test', event_start='2023-10-02 12:00:00', duration='60')"]
    gt = ["calendar.create_event.func(event_name='Test', event_start='2023-10-02 12:00:00', duration='60')"]
    assert is_exact_match(pred, gt)


def test_is_exact_match_case_insensitive():
    pred = ["calendar.create_event.func(event_name='TEST EVENT')"]
    gt = ["calendar.create_event.func(event_name='test event')"]
    assert is_exact_match(pred, gt)


def test_is_exact_match_different():
    pred = ["calendar.create_event.func(event_name='Test A')"]
    gt = ["calendar.create_event.func(event_name='Test B')"]
    assert not is_exact_match(pred, gt)


def test_is_exact_match_filters_non_side_effect_tools():
    pred = [
        "calendar.search_events.func(query='test')",
        "calendar.create_event.func(event_name='Test')",
    ]
    gt = ["calendar.create_event.func(event_name='Test')"]
    assert is_exact_match(pred, gt)


def test_is_exact_match_empty():
    assert is_exact_match([], [])


def test_end_date_minor_error_matching():
    gt = ['analytics.create_plot.func(time_min="2023-10-01", time_max="2023-11-29", value_to_plot="total_visits")']
    pred = ['analytics.create_plot.func(time_min="2023-10-01", time_max="2023-11-30", value_to_plot="total_visits")']
    assert end_date_minor_error(gt, pred)


def test_end_date_minor_error_not_matching():
    gt = ['analytics.create_plot.func(time_min="2023-10-01", time_max="2023-11-29", value_to_plot="total_visits")']
    pred = ['analytics.create_plot.func(time_min="2023-10-01", time_max="2023-12-01", value_to_plot="total_visits")']
    assert not end_date_minor_error(gt, pred)


def test_end_date_minor_error_empty_ground_truth():
    assert not end_date_minor_error([], [])


def test_meeting_start_time_error_matching():
    gt = ['calendar.create_event.func(event_start="2023-12-01 13:00:00")']
    pred = ['calendar.create_event.func(event_start="2023-12-01 09:00:00")']
    assert meeting_start_time_error(gt, pred)


def test_meeting_start_time_error_not_matching():
    gt = ['calendar.create_event.func(event_start="2023-12-01 13:00:00")']
    pred = ['calendar.create_event.func(event_start="2023-12-01 14:00:00")']
    assert not meeting_start_time_error(gt, pred)


def test_meeting_start_time_error_empty_ground_truth():
    assert not meeting_start_time_error([], [])


def test_meeting_start_time_error_no_relevant_time():
    gt = ['calendar.create_event.func(event_start="2023-12-01 10:00:00")']
    pred = ['calendar.create_event.func(event_start="2023-12-01 09:00:00")']
    assert not meeting_start_time_error(gt, pred)

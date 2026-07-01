import pytest

from src.evals.evaluation import has_side_effects, is_correct


def test_is_correct_single_action():
    error = ""
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    assert is_correct(predicted_actions, ground_truth_actions, error)
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event2', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    assert not is_correct(predicted_actions, ground_truth_actions, error)


def test_is_correct_case_insensitive():
    error = ""
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='Sam@Company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    assert is_correct(predicted_actions, ground_truth_actions, error)


def test_is_correct_multiple_actions():
    error = ""
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
        "calendar.create_event.func(event_name='My event 2', participant_email='olly@company.com', event_start='2023-10-03 12:00:00', duration=60)",
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
        "calendar.create_event.func(event_name='My event 2', participant_email='olly@company.com', event_start='2023-10-03 12:00:00', duration=60)",
    ]
    assert is_correct(predicted_actions, ground_truth_actions, error)
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
        "calendar.create_event.func(event_name='My event 2', participant_email='olly@company.com', event_start='2023-10-03 12:00:00', duration=60)",
        "calendar.create_event.func(event_name='My event 3', participant_email='tommy@company.com', event_start='2023-10-04 12:00:00', duration=60)",
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
        "calendar.create_event.func(event_name='My even2t', participant_email='olly@company.com', event_start='2023-10-03 12:00:00', duration=60)",
    ]
    assert not is_correct(predicted_actions, ground_truth_actions, error)


def test_is_correct_different_action_path():
    """
    Tests if the function can handle different action paths that lead to the same state.
    """
    error = ""
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
        "calendar.delete_event.func(event_id='00000300')",
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
    ]
    assert is_correct(predicted_actions, ground_truth_actions, error)


def test_is_correct_bad_syntax():
    """
    Tests if the function can handle bad syntax in the actions.
    """
    error = ""
    predicted_actions = [
        "not a python function",
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
    ]
    assert not is_correct(predicted_actions, ground_truth_actions, error)


def test_is_correct_failed_prediction_not_credited_on_readonly_task():
    """
    A prediction whose actions all fail to execute must not be scored correct just
    because it leaves the state unchanged, matching a read-only ground truth.
    """
    error = ""
    predicted_actions = [
        "calendar.create_event.func(unknown_kwarg='x')",
    ]
    ground_truth_actions = [
        "calendar.search_events.func(query='Meeting')",
    ]
    assert not is_correct(predicted_actions, ground_truth_actions, error)


def test_is_correct_valid_readonly_prediction_matches_readonly_ground_truth():
    """
    A valid read-only prediction that leaves the state unchanged is still correct
    against a read-only ground truth (the success flag must not cause false negatives).
    """
    error = ""
    predicted_actions = [
        "calendar.search_events.func(query='Standup')",
    ]
    ground_truth_actions = [
        "calendar.search_events.func(query='Meeting')",
    ]
    assert is_correct(predicted_actions, ground_truth_actions, error)


def test_is_correct_raises_on_malformed_ground_truth():
    """
    Ground truth is curated data: if it does not execute cleanly the comparison
    state is meaningless, so fail loudly rather than silently mis-scoring.
    """
    with pytest.raises(AssertionError):
        is_correct(["calendar.search_events.func(query='x')"], ["not valid python!!!"], "")


def test_is_correct_with_error():
    """
    Tests if the function can handle errors in the actions.
    """
    error = "Context window exceeded"
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    assert not is_correct(predicted_actions, ground_truth_actions, error)


def test_has_side_effects_no_side_effect():
    predicted_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)"
    ]
    assert not has_side_effects(predicted_actions, correct=True)


def test_has_side_effects_unrelated_change():
    predicted_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)",
        "calendar.create_event.func(event_name='Team Meeting 2', participant_email='alex@company.com', event_start='2023-10-06 09:00:00', duration=60)",
    ]
    assert has_side_effects(predicted_actions, correct=False)


def test_has_side_effects_missing_action():
    predicted_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)"
    ]
    assert has_side_effects(predicted_actions, correct=False)


def test_has_side_effects_no_action():
    predicted_actions: list[str] = []
    assert not has_side_effects(predicted_actions, correct=False)


def test_has_side_effects_complex_scenario():
    predicted_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)",
        "calendar.delete_event.func(event_id='00000250')",
    ]
    assert has_side_effects(predicted_actions, correct=False)


def test_is_correct_additive_plots_order_independent():
    """
    Two plots produce the same final state regardless of the order they are
    created in, so a reversed-order prediction must still be scored correct.
    """
    error = ""
    plot_a = 'analytics.create_plot.func(time_min="2023-01-01", time_max="2023-01-31", value_to_plot="total_visits", plot_type="bar")'
    plot_b = 'analytics.create_plot.func(time_min="2023-02-01", time_max="2023-02-28", value_to_plot="total_visits", plot_type="line")'
    ground_truth_actions = [plot_a, plot_b]
    predicted_actions = [plot_b, plot_a]
    assert is_correct(predicted_actions, ground_truth_actions, error)


def test_is_correct_additive_different_rows_still_incorrect():
    """
    Order-independence must not make genuinely different states match: a plot
    with different parameters is still incorrect even after reordering.
    """
    error = ""
    plot_a = 'analytics.create_plot.func(time_min="2023-01-01", time_max="2023-01-31", value_to_plot="total_visits", plot_type="bar")'
    plot_b = 'analytics.create_plot.func(time_min="2023-02-01", time_max="2023-02-28", value_to_plot="total_visits", plot_type="line")'
    plot_c = 'analytics.create_plot.func(time_min="2023-03-01", time_max="2023-03-31", value_to_plot="user_engaged", plot_type="bar")'
    ground_truth_actions = [plot_a, plot_b]
    predicted_actions = [plot_c, plot_a]
    assert not is_correct(predicted_actions, ground_truth_actions, error)


def test_is_correct_chart_end_date_today_accepted():
    """
    Ground truth plots charts ending on the last day with data (2023-11-29,
    "yesterday"). A model that plots up to the current date (2023-11-30,
    "today") draws the same chart and must be scored correct.
    """
    error = ""
    ground_truth_actions = [
        'analytics.create_plot.func(time_min="2023-11-01", time_max="2023-11-29", value_to_plot="total_visits", plot_type="bar")'
    ]
    predicted_actions = [
        'analytics.create_plot.func(time_min="2023-11-01", time_max="2023-11-30", value_to_plot="total_visits", plot_type="bar")'
    ]
    assert is_correct(predicted_actions, ground_truth_actions, error)


def test_is_correct_chart_end_date_yesterday_still_accepted():
    """The unchanged ground-truth end date (2023-11-29) is still correct."""
    error = ""
    ground_truth_actions = [
        'analytics.create_plot.func(time_min="2023-11-01", time_max="2023-11-29", value_to_plot="total_visits", plot_type="bar")'
    ]
    predicted_actions = [
        'analytics.create_plot.func(time_min="2023-11-01", time_max="2023-11-29", value_to_plot="total_visits", plot_type="bar")'
    ]
    assert is_correct(predicted_actions, ground_truth_actions, error)


def test_is_correct_chart_other_end_date_still_incorrect():
    """
    Only the today/yesterday pair is accepted: a different end date (here a
    plot ending two days late) is still a genuine error.
    """
    error = ""
    ground_truth_actions = [
        'analytics.create_plot.func(time_min="2023-11-01", time_max="2023-11-29", value_to_plot="total_visits", plot_type="bar")'
    ]
    predicted_actions = [
        'analytics.create_plot.func(time_min="2023-11-01", time_max="2023-12-01", value_to_plot="total_visits", plot_type="bar")'
    ]
    assert not is_correct(predicted_actions, ground_truth_actions, error)

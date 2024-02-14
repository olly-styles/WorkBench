from src.evals.utils import has_side_effects, is_correct


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
        "calendar.delete_event.func(event_id='00000500')",
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
    ground_truth_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)"
    ]
    assert not has_side_effects(predicted_actions, ground_truth_actions)


def test_has_side_effects_unrelated_change():
    predicted_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)",
        "calendar.create_event.func(event_name='Team Meeting 2', participant_email='alex@company.com', event_start='2023-10-06 09:00:00', duration=60)",
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)"
    ]
    assert has_side_effects(predicted_actions, ground_truth_actions)


def test_has_side_effects_missing_action():
    error = ""
    predicted_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)"
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)",
        "calendar.create_event.func(event_name='Team Meeting 2', participant_email='alex@company.com', event_start='2023-10-06 09:00:00', duration=60)",
    ]
    assert has_side_effects(predicted_actions, ground_truth_actions)


def test_has_side_effects_no_action():
    predicted_actions = []
    ground_truth_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)",
    ]
    assert not has_side_effects(predicted_actions, ground_truth_actions)


def test_has_side_effects_complex_scenario():
    predicted_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)",
        "calendar.delete_event.func(event_id='00000347')",
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='Team Meeting', participant_email='alex@company.com', event_start='2023-10-05 09:00:00', duration=60)"
    ]
    assert has_side_effects(predicted_actions, ground_truth_actions)

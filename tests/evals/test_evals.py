import pytest
from src.tools.toolkits import tool_information
from src.evals.utils import is_correct


def test_is_correct_single_action():
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    assert is_correct(predicted_actions, ground_truth_actions)
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event2', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)"
    ]
    assert not is_correct(predicted_actions, ground_truth_actions)


def test_is_correct_multiple_actions():
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
        "calendar.create_event.func(event_name='My event 2', participant_email='olly@company.com', event_start='2023-10-03 12:00:00', duration=60)",
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
        "calendar.create_event.func(event_name='My event 2', participant_email='olly@company.com', event_start='2023-10-03 12:00:00', duration=60)",
    ]
    assert is_correct(predicted_actions, ground_truth_actions)
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
        "calendar.create_event.func(event_name='My event 2', participant_email='olly@company.com', event_start='2023-10-03 12:00:00', duration=60)",
        "calendar.create_event.func(event_name='My event 3', participant_email='tommy@company.com', event_start='2023-10-04 12:00:00', duration=60)",
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
        "calendar.create_event.func(event_name='My even2t', participant_email='olly@company.com', event_start='2023-10-03 12:00:00', duration=60)",
    ]
    assert not is_correct(predicted_actions, ground_truth_actions)


def test_is_correct_different_action_path():
    """
    Tests if the function can handle different action paths that lead to the same state.
    """
    predicted_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
        "calendar.delete_event.func(event_id='00000500')",
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
    ]
    ground_truth_actions = [
        "calendar.create_event.func(event_name='My event', participant_email='sam@company.com', event_start='2023-10-02 12:00:00', duration=60)",
    ]
    assert is_correct(predicted_actions, ground_truth_actions)

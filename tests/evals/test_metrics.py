import pandas as pd

from src.evals.metrics import ResultsSummary, compute_metrics, get_output


def test_results_summary_construction():
    summary = ResultsSummary(
        num_correct=10,
        num_incorrect=5,
        num_side_effects=2,
        num_correct_no_actions=3,
        num_incorrect_no_actions=1,
        num_correct_non_zero_actions=7,
        num_incorrect_non_zero_actions=4,
        num_correct_two_or_more_actions=5,
        num_incorrect_two_or_more_actions=3,
        num_context_window_errors=0,
    )
    assert summary.num_correct == 10
    assert summary.num_incorrect == 5


def test_get_output_single_quote_format():
    response = "AgentResult(output='The answer is 42', intermediate_steps=[])"
    assert get_output(response) == "The answer is 42"


def test_get_output_json_format():
    response = '{"output": "The answer is 42"}'
    assert get_output(response) == "The answer is 42"


def test_get_output_fallback():
    response = "plain text response"
    assert get_output(response) == "plain text response"


def test_compute_metrics_correct_prediction():
    create_event = "calendar.create_event.func(event_name='Test', participant_email='test@atlas.com', event_start='2023-10-02 12:00:00', duration='60')"
    ground_truth_df = pd.DataFrame(
        {
            "task": ["Create a test event"],
            "outcome": [[create_event]],
        }
    )
    predictions_df = pd.DataFrame(
        {
            "task": ["Create a test event"],
            "function_calls": [[create_event]],
            "full_response": ["done"],
            "error": [""],
        }
    )
    df = compute_metrics(ground_truth_df, predictions_df)
    assert df["correct"].iloc[0]
    assert df["exact_match"].iloc[0]
    assert not df["unwanted_side_effects"].iloc[0]


def test_compute_metrics_incorrect_prediction():
    gt_action = "calendar.create_event.func(event_name='Meeting A', participant_email='a@atlas.com', event_start='2023-10-02 12:00:00', duration='60')"
    pred_action = "calendar.create_event.func(event_name='Meeting B', participant_email='b@atlas.com', event_start='2023-10-03 12:00:00', duration='60')"
    ground_truth_df = pd.DataFrame(
        {
            "task": ["Create meeting"],
            "outcome": [[gt_action]],
        }
    )
    predictions_df = pd.DataFrame(
        {
            "task": ["Create meeting"],
            "function_calls": [[pred_action]],
            "full_response": ["done"],
            "error": [""],
        }
    )
    df = compute_metrics(ground_truth_df, predictions_df)
    assert not df["correct"].iloc[0]
    assert not df["exact_match"].iloc[0]


def test_compute_metrics_no_actions():
    ground_truth_df = pd.DataFrame(
        {
            "task": ["Do nothing"],
            "outcome": [[]],
        }
    )
    predictions_df = pd.DataFrame(
        {
            "task": ["Do nothing"],
            "function_calls": [[]],
            "full_response": ["done"],
            "error": [""],
        }
    )
    df = compute_metrics(ground_truth_df, predictions_df)
    assert df["correct"].iloc[0]
    assert df["no_actions"].iloc[0]

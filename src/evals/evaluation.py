import pandas as pd

from src.evals.actions import execute_actions_and_reset_state
from src.tools.state import get_state, reset_state
from src.tools.toolkits import tools_with_side_effects

BENCHMARK_END_DATE = "2023-11-29"
BENCHMARK_END_DATE_OFF_BY_ONE = "2023-11-30"
NEXT_FREE_TIME_GROUND_TRUTH = "13:00:00"
COMMON_ERROR_TIMES = ["09:00:00", "11:00:00", "15:00:00", "15:30:00"]

CASE_SENSITIVE_FIELDS = ["status", "list_name", "board"]

SIDE_EFFECT_STATE_FIELDS = ("calendar_events", "emails", "project_tasks", "crm_data")


def get_function_name(action: str) -> str:
    """Extracts the function name from a string"""
    return ".".join(action.split("(")[0].split(".")[:2])


def end_date_minor_error(ground_truth: list[str], prediction: list[str]) -> bool:
    """Function to check if the end date is off by one day in the prediction

    Parameters
    ----------
    ground_truth : list
        List of ground truth actions as strings.
    prediction : list
        List of predicted actions as strings.

    Returns
    -------
    bool
        True if the end date is off by one day in the prediction.
    """
    if not ground_truth:
        return False
    return all(
        BENCHMARK_END_DATE in func and func.replace(BENCHMARK_END_DATE, BENCHMARK_END_DATE_OFF_BY_ONE) in prediction
        for func in ground_truth
    )


def _has_common_time_error(func: str, prediction: list[str]) -> bool:
    return any(func.replace(NEXT_FREE_TIME_GROUND_TRUTH, t) in prediction for t in COMMON_ERROR_TIMES)


def meeting_start_time_error(ground_truth: list[str], prediction: list[str]) -> bool:
    """Function to check if the meeting start time is off where the agent predicts the wrong first available time

    Parameters
    ----------
    ground_truth : list
        List of ground truth actions as strings.
    prediction : list
        List of predicted actions as strings.

    Returns
    -------
    bool
        True if the meeting start time is off by one hour in the prediction.
    """
    if not ground_truth:
        return False
    return all(
        NEXT_FREE_TIME_GROUND_TRUTH in func and _has_common_time_error(func, prediction) for func in ground_truth
    )


def is_exact_match(predicted_actions: list[str], ground_truth_actions: list[str]) -> bool:
    """
    Checks if the predicted actions are an exact match to the ground truth actions.

    Parameters
    ----------
    predicted_actions : list
        List of predicted actions as strings.
    ground_truth_actions : list
        List of ground truth actions as strings.

    Returns
    -------
    bool
        True if the predicted actions are an exact match to the ground truth actions.

    """
    side_effect_names = {t.name for t in tools_with_side_effects}
    predicted_with_side_effects = sorted(
        action.lower() for action in predicted_actions if get_function_name(action) in side_effect_names
    )
    expected = sorted(action.lower() for action in ground_truth_actions)

    return predicted_with_side_effects == expected


def _convert_strs_to_lowercase(df: pd.DataFrame) -> pd.DataFrame:
    # For some fields the case matters, so we don't convert them to lowercase
    for col in df.columns:
        if col not in CASE_SENSITIVE_FIELDS:
            df[col] = df[col].str.lower()
    return df


def _execute_and_normalize(actions: list[str]) -> tuple[bool, dict[str, pd.DataFrame]]:
    success, states = execute_actions_and_reset_state(actions)
    # We allow for case-insensitive comparison of strings for most fields
    return success, {name: _convert_strs_to_lowercase(s) for name, s in states.items()}


def _states_match(predicted: pd.DataFrame, ground_truth: pd.DataFrame) -> bool:
    """
    Compares two final states as an unordered set of rows.

    Additive tools such as create_plot and send_email append rows in call order,
    so a correct answer that produces the same rows in a different order must
    still be counted as a match. Row order is therefore ignored.

    Parameters
    ----------
    predicted : pd.DataFrame
        Final state produced by the predicted actions.
    ground_truth : pd.DataFrame
        Final state produced by the ground truth actions.

    Returns
    -------
    bool
        True if both states contain the same rows regardless of order.
    """
    if list(predicted.columns) != list(ground_truth.columns):
        return False
    if len(predicted) != len(ground_truth):
        return False
    columns = list(ground_truth.columns)
    predicted_sorted = predicted.sort_values(by=columns).reset_index(drop=True)
    ground_truth_sorted = ground_truth.sort_values(by=columns).reset_index(drop=True)
    return predicted_sorted.equals(ground_truth_sorted)


def is_correct(predicted_actions: list[str], ground_truth_actions: list[str], error: str) -> bool:
    """
    Checks if the prediction is correct by comparing the state change after executing the actions.

    Parameters
    ----------
    predicted_actions : list
        List of predicted actions as strings.
    ground_truth_actions : list
        List of ground truth actions as strings.
    error : str
        Error message from the prediction.

    Returns
    -------
    bool
        True if the predicted actions result in the same state change as the ground truth actions.

    """
    if error:
        return False
    successful_execution, predicted_states = _execute_and_normalize(predicted_actions)
    ground_truth_success, ground_truth_states = _execute_and_normalize(ground_truth_actions)
    assert ground_truth_success, f"Ground truth actions failed to execute cleanly: {ground_truth_actions}"

    return successful_execution and all(
        _states_match(predicted_states[name], ground_truth_states[name]) for name in predicted_states
    )


def has_side_effects(predicted_actions: list[str], correct: bool) -> bool:
    """
    Checks if the predicted actions have side effects by comparing the state change after executing the actions.

    Only the states in SIDE_EFFECT_STATE_FIELDS are compared: creating a plot
    is harmless, so plots_data is excluded.

    Parameters
    ----------
    predicted_actions : list
        List of predicted actions as strings.
    correct : bool
        Whether the prediction was already determined to be correct.

    Returns
    -------
    bool
        True if the predicted actions result in a state change without matching the ground truth.

    """
    reset_state()
    state = get_state()
    original_states = {name: getattr(state, name).copy() for name in SIDE_EFFECT_STATE_FIELDS}
    _, predicted_states = execute_actions_and_reset_state(predicted_actions)

    state_changed = any(
        not _states_match(predicted_states[name], original_states[name]) for name in SIDE_EFFECT_STATE_FIELDS
    )
    return state_changed and not correct

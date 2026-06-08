import ast
import csv
import os
import re
import sys
from dataclasses import dataclass

import pandas as pd

from src.evals.evaluation import (
    end_date_minor_error,
    has_side_effects,
    is_correct,
    is_exact_match,
    meeting_start_time_error,
)

csv.field_size_limit(sys.maxsize)


@dataclass
class ResultsSummary:
    num_correct: int
    num_incorrect: int
    num_side_effects: int
    num_correct_no_actions: int
    num_incorrect_no_actions: int
    num_correct_non_zero_actions: int
    num_incorrect_non_zero_actions: int
    num_correct_two_or_more_actions: int
    num_incorrect_two_or_more_actions: int
    num_context_window_errors: int


def get_output(full_response: str) -> str:
    """Get the output from the full response"""
    match = re.search(r"output='(.*?)'(?:,|\))", full_response, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r'"output":\s*"(.*?)"', full_response)
    if match:
        return match.group(1)
    return full_response


_SKIP_FIELDS = ["wrong_email", "no_actions", "end_date_minor_error", "meeting_start_time_error"]


def _print_error_section(title: str, df: pd.DataFrame) -> None:
    print("--------------------------------------------")
    print("--------------------------------------------")
    print(f"{title}:")
    print("--------------------------------------------")
    print("--------------------------------------------")
    for _, row in df.iterrows():
        if not any(row[field] for field in _SKIP_FIELDS):
            print("--------------------------------------------")
            print("Task:")
            print(f"    {row['task']}")
            print()
            print("Prediction:")
            for action in row["prediction"]:
                print(f"    {action}")
            print()
            print("Ground truth:")
            for action in row["ground_truth"]:
                print(f"    {action}")
            print()
            print(f"Unwanted side effects: {row['unwanted_side_effects']}")
            print()
            if "meeting_start_time_error" in row and row["unwanted_side_effects"]:
                print(f"Meeting start time error: {row['meeting_start_time_error']}")
            print(f"Error: {row['error']}")
            print("")
            print("Output:")
            output = get_output(row["full_response"])
            print(f"    {output}")


def compute_metrics(ground_truth_df: pd.DataFrame, predictions_df: pd.DataFrame) -> pd.DataFrame:
    predictions = predictions_df.rename(columns={"function_calls": "prediction"})
    predictions = predictions.fillna("")

    ground_truth = ground_truth_df.rename(columns={"outcome": "ground_truth"})
    df = predictions.merge(ground_truth, on="task")
    assert len(predictions) == len(ground_truth) == len(df), (
        f"{len(predictions)} predictions does not match {len(ground_truth_df)} ground truth outcomes. Check that the predictions and ground truth are for the same tasks."
    )

    # Replace all newlines with "\\n" for all actions
    df["prediction"] = df["prediction"].apply(lambda actions: [action.replace("\n", "\\n") for action in actions])
    df["ground_truth"] = df["ground_truth"].apply(lambda actions: [action.replace("\n", "\\n") for action in actions])

    df["exact_match"] = [is_exact_match(pred, gt) for pred, gt in zip(df["prediction"], df["ground_truth"])]
    correct_state = [is_correct(pred, gt, "") for pred, gt in zip(df["prediction"], df["ground_truth"])]
    df["correct"] = [cs and not err for cs, err in zip(correct_state, df["error"])]
    df["unwanted_side_effects"] = [has_side_effects(pred, cs) for pred, cs in zip(df["prediction"], correct_state)]
    df["no_actions"] = [len(pred) == 0 for pred in df["prediction"]]
    # wrong email if @example is in the prediction and @atlas is not in the prediction. Prediction is a list so needs to be converted to a string
    df["wrong_email"] = [("@example" in str(pred)) and ("@atlas" not in str(pred)) for pred in df["prediction"]]
    df["wrong_email"] = df["wrong_email"] & ~df["correct"]
    # Puts in end of November to plot instead of 29th november, but everything else matches
    df["end_date_minor_error"] = [
        end_date_minor_error(gt, pred) for gt, pred in zip(df["ground_truth"], df["prediction"])
    ]
    df["end_date_minor_error"] = df["end_date_minor_error"] & ~df["correct"]
    df["meeting_start_time_error"] = [
        meeting_start_time_error(gt, pred) for gt, pred in zip(df["ground_truth"], df["prediction"])
    ]
    df["meeting_start_time_error"] = df["meeting_start_time_error"] & ~df["correct"]

    return df


def print_error_report(df: pd.DataFrame) -> None:
    _print_error_section("ERRORS without unwanted side effects", df[~df["correct"] & ~df["unwanted_side_effects"]])
    _print_error_section("ERRORS with unwanted side effects", df[~df["correct"] & df["unwanted_side_effects"]])

    _print_accuracy_summary(df)

    incorrect = ~df["correct"]
    no_side = ~df["unwanted_side_effects"]
    with_side = df["unwanted_side_effects"]
    total = len(df)

    num_failed_to_follow_react = len(df[incorrect & no_side & df["no_actions"]])
    num_wrong_email_no_side_effects = len(df[incorrect & df["wrong_email"] & no_side])
    num_meeting_start_time_error_no_side_effects = len(df[incorrect & df["meeting_start_time_error"] & no_side])

    print(
        f"Wrong email, no side effects: {round(num_wrong_email_no_side_effects / total * 100, 2)}% ({num_wrong_email_no_side_effects} out of {total})"
    )
    print(
        f"Didn't follow REACT framework, no side effects: {round(num_failed_to_follow_react / total * 100, 2)}% ({num_failed_to_follow_react} out of {total})"
    )
    print(
        f"Meeting start time error, no side effects: {round(num_meeting_start_time_error_no_side_effects / total * 100, 2)}% ({num_meeting_start_time_error_no_side_effects} out of {total})"
    )

    num_wrong_email_with_side_effects = len(
        df[incorrect & df["wrong_email"] & with_side & ~df["end_date_minor_error"] & ~df["meeting_start_time_error"]]
    )
    num_end_date_minor_error = len(
        df[incorrect & df["end_date_minor_error"] & with_side & ~df["wrong_email"] & ~df["meeting_start_time_error"]]
    )
    num_meeting_start_time_error_with_side_effects = len(df[incorrect & df["meeting_start_time_error"] & with_side])
    print(
        f"Wrong email, with side effects: {round(num_wrong_email_with_side_effects / total * 100, 2)}% ({num_wrong_email_with_side_effects} out of {total})"
    )
    print(
        f"End date minor error, with side effects: {round(num_end_date_minor_error / total * 100, 2)}% ({num_end_date_minor_error} out of {total})"
    )
    print(
        f"Meeting start time error, with side effects: {round(num_meeting_start_time_error_with_side_effects / total * 100, 2)}% ({num_meeting_start_time_error_with_side_effects} out of {total})"
    )
    print("--------------------------------------------")
    print("--------------------------------------------")
    print("Correct but not exact match:")
    print("--------------------------------------------")
    print("--------------------------------------------")
    for _, row in df[df["correct"] & ~df["exact_match"]].iterrows():
        print("--------------------------------------------")
        print("Task:")
        print(f"    {row['task']}")
        print()
        print("Prediction:")
        for action in row["prediction"]:
            print(f"    {action}")
        print()
        print("Ground truth:")
        for action in row["ground_truth"]:
            print(f"    {action}")
        print()
        print(f"Unwanted side effects: {row['unwanted_side_effects']}")
        print()
        print(f"Error: {row['error']}")
        print("")
        print("Output:")
        output = get_output(row["full_response"])
        print(f"    {output}")


def _print_accuracy_summary(df: pd.DataFrame) -> None:
    num_errors_without_side_effects = len(df[(~df["correct"]) & ~df["unwanted_side_effects"]])
    num_errors_with_side_effects = len(df[(~df["correct"]) & df["unwanted_side_effects"]])
    print(f"Accuracy: {round(df['correct'].mean() * 100, 2)}% ({df['correct'].sum()} out of {len(df)})")
    print(
        f"Errors without unwanted side effects: {round(num_errors_without_side_effects / len(df) * 100, 2)}% ({num_errors_without_side_effects} out of {len(df)})"
    )
    print(
        f"Errors with unwanted side effects: {round(num_errors_with_side_effects / len(df) * 100, 2)}% ({num_errors_with_side_effects} out of {len(df)})"
    )


def calculate_metrics(
    ground_truth_df: pd.DataFrame, predictions_df: pd.DataFrame, print_errors: bool = True
) -> pd.DataFrame:
    df = compute_metrics(ground_truth_df, predictions_df)
    if print_errors:
        print_error_report(df)
    else:
        _print_accuracy_summary(df)
    return df


def get_latest_results_path(
    results_root_dir: str, model: str, tool: str, all_tools_in_prompt: bool = True
) -> tuple[str, str] | None:
    """Get the latest results file path and ground truth path for a given model and tool.

    Result files are named ``{model}_{tool_selection}_{YYYY-MM-DD}_{HH-MM-SS}.csv``.
    We match the model and tool_selection as exact filename components (not
    substrings) and pick the most recent run by its timestamp suffix, which sorts
    lexicographically because it is zero-padded.
    """
    results_dir = os.path.join(results_root_dir, tool)
    tool_selection = "all" if all_tools_in_prompt else "domains"
    prefix = f"{model}_{tool_selection}_"
    timestamps = [
        file[len(prefix) : -len(".csv")]
        for file in os.listdir(results_dir)
        if file.startswith(prefix) and file.endswith(".csv")
    ]
    ground_truth_path = os.path.join("data", "processed", "tasks_and_outcomes", f"{tool}_tasks_and_outcomes.csv")
    if not timestamps:
        return None
    latest = os.path.join(results_dir, f"{prefix}{max(timestamps)}.csv")
    return latest, ground_truth_path


def get_latest_results_from_dir(
    results_root_dir: str, model: str, tool: str, print_errors: bool = False, all_tools_in_prompt: bool = True
) -> ResultsSummary | None:
    """Get the latest results for each model in the results directory"""
    results = get_latest_results_path(results_root_dir, model, tool, all_tools_in_prompt)
    if not results:
        print(f"\nNo results found for {tool} with {model}")
        return None

    model_results_path, ground_truth_path = results
    predictions = pd.read_csv(model_results_path, dtype=str, engine="python", on_bad_lines="warn")
    ground_truth = pd.read_csv(ground_truth_path, dtype=str)
    ground_truth["outcome"] = ground_truth["outcome"].apply(ast.literal_eval)
    predictions["function_calls"] = predictions["function_calls"].apply(ast.literal_eval)
    print(f"\nCalculating metrics for {tool} with {model}")
    df = calculate_metrics(ground_truth, predictions, print_errors=print_errors)

    gt_lengths = df["ground_truth"].apply(len)
    return ResultsSummary(
        num_correct=df["correct"].sum(),
        num_incorrect=len(df) - df["correct"].sum(),
        num_side_effects=df["unwanted_side_effects"].sum(),
        num_correct_no_actions=df[gt_lengths == 0]["correct"].sum(),
        num_incorrect_no_actions=len(df[gt_lengths == 0]) - df[gt_lengths == 0]["correct"].sum(),
        num_correct_non_zero_actions=df[gt_lengths > 0]["correct"].sum(),
        num_incorrect_non_zero_actions=len(df[gt_lengths > 0]) - df[gt_lengths > 0]["correct"].sum(),
        num_correct_two_or_more_actions=df[gt_lengths > 1]["correct"].sum(),
        num_incorrect_two_or_more_actions=len(df[gt_lengths > 1]) - df[gt_lengths > 1]["correct"].sum(),
        num_context_window_errors=len(df[df["error"] == "Context window exceeded"]),
    )

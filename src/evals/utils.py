from src.tools.toolkits import tool_information
import re
import os
import pandas as pd


def convert_agent_action_to_function_call(action):
    """Converts langchain_core.agents.AgentAction to an API call"""
    return action.tool + "(" + str(action.tool_input) + ")"


def has_side_effects(row):
    """
    Checks if there are any side effect functions in the prediction.
    If a side effect function is present, it must match the ground truth exactly.
    """
    side_effect_functions = [
        tool["name"] for tool in tool_information if tool["side_effects"]
    ]

    prediction_funcs = extract_function_names(row["prediction"])
    ground_truth_funcs = extract_function_names(row["ground_truth"])

    for func in prediction_funcs:
        if func in side_effect_functions:
            if func not in ground_truth_funcs or row["prediction"].count(func) != row[
                "ground_truth"
            ].count(func):
                return True
    return False


def is_correct(row):
    """
    Checks if the prediction is correct.
    A prediction is correct if:
        1. The prediction contains the ground truth.
        2. Any side effect function in the prediction also appears in the ground truth with the same arguments.
        3. The agent did not stop.
    """
    # Extract side effect functions from tool information

    # If no conflicting side effect function, check if ground truth is in prediction
    return (
        row["ground_truth"] in row["prediction"]
        and not row["stopped"]
        and not has_side_effects(row)
    )


def extract_function_names(s):
    """Extracts function names from a string"""
    return re.findall(r"(\b\w+\.\w+)\(", s)

def calculate_metrics(ground_truth_df, predictions_df, print_errors=True):
    """"""
    predictions = predictions_df.rename(columns={"function_calls": "prediction"})
    predictions = predictions.fillna("")

    ground_truth = ground_truth_df.rename(columns={"answer": "ground_truth"})
    df = predictions.merge(ground_truth, on="question")
    assert (
        len(predictions) == len(ground_truth) == len(df)
    ), "Number of predictions does not match number of ground truth answers. Check that the predictions and ground truth are for the same questions."

    df["correct"] = df.apply(is_correct, axis=1)
    df["has_side_effects"] = df.apply(has_side_effects, axis=1)

    # print out the questions that were not answered correctly
    if print_errors:
        for index, row in df[~df["correct"]].iterrows():
            print(f"Question: {row['question']}")
            print(f"Prediction: {row['prediction']}")
            print(f"Ground truth: {row['ground_truth']}")
            print(f"Has side effects: {row['has_side_effects']}")
            print("")

    # print accuracy as a percentage to 2dp
    print(f"Accuracy: {round(df['correct'].mean() * 100, 2)}%")
    # print number of side effects as a percentage to 2dp
    print(f"Side effects: {round(df['has_side_effects'].mean() * 100, 2)}% of predictions")
    
def get_latest_results_from_dir(results_root_dir, tool, action, model_list):
    """Get the latest results for each model in the results directory"""
    results_dir = os.path.join(results_root_dir, tool, action)
    results_files = os.listdir(results_dir)
    for model in model_list:
        model_results_files = [os.path.join(results_dir, file) for file in results_files if model in file]
        if not len(model_results_files):
            print(f"\nNo results found for {tool}, {action} action with {model}")
            return
        
        latest_results_file = max(model_results_files, key=os.path.getctime)
        ground_truth_path = os.path.join("data", "processed", f"{tool}_questions_and_answers_{action}_action.csv")
        predictions = pd.read_csv(latest_results_file)
        ground_truth = pd.read_csv(ground_truth_path, dtype=str)
        print(f"\nCalculating metrics for {tool}, {action} action with {model}")
        calculate_metrics(ground_truth, predictions, print_errors=False)

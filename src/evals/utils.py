from src.tools.toolkits import tool_information
import re


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

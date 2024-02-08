from src.tools.toolkits import tool_information
import re
import os
import pandas as pd
from langchain_openai import ChatOpenAI, OpenAI
from langchain.agents import initialize_agent, AgentType
import csv
from src.tools import calendar, email
from src.tools.toolkits import calendar_toolkit, email_toolkit


OPENAI_KEY = open("openai_key.txt", "r").read()


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


def execute_actions_and_reset_state(actions):
    """
    Executes a list of actions on the calendar and returns the resulting calendar events.

    Parameters
    ----------
    actions : list
        List of actions to be executed. Each action should be a function call.

    Returns
    -------
    success bool
        True if the actions were executed successfully.
    new_calendar_state pd.DataFrame
        The resulting calendar events after executing the actions.
    new_email_state pd.DataFrame
        The resulting emails after executing the actions.
    """
    # Execute the actions
    for action in actions:
        try:
            eval(action)
        except:
            return False, None, None
    new_calendar_state = calendar.CALENDAR_EVENTS.copy()
    new_email_state = email.EMAILS.copy()

    # Reset the state of the tools
    for domain in [calendar, email]:
        domain.reset_state()
    return True, new_calendar_state, new_email_state


def is_correct(predicted_actions, ground_truth_actions):
    """
    Checks if the prediction is correct by comparing the state change after executing the actions.

    Parameters
    ----------
    predicted_actions : list
        List of predicted actions as strings.
    ground_truth_actions : list
        List of ground truth actions as strings.

    Returns
    -------
    bool
        True if the predicted actions result in the same state change as the ground truth actions.

    """
    successful_execution, predicted_calendar_state, predicted_email_state = (
        execute_actions_and_reset_state(predicted_actions)
    )
    _, ground_truth_calendar_state, ground_truth_email_state = (
        execute_actions_and_reset_state(ground_truth_actions)
    )
    return (
        successful_execution
        and predicted_calendar_state.equals(ground_truth_calendar_state)
        and predicted_email_state.equals(ground_truth_email_state)
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
    print(
        f"Side effects: {round(df['has_side_effects'].mean() * 100, 2)}% of predictions"
    )


def get_latest_results_from_dir(
    results_root_dir, tool, action, model_list, print_errors=False
):
    """Get the latest results for each model in the results directory"""
    results_dir = os.path.join(results_root_dir, tool, action)
    results_files = os.listdir(results_dir)
    for model in model_list:
        model_results_files = [
            os.path.join(results_dir, file) for file in results_files if model in file
        ]
        if not len(model_results_files):
            print(f"\nNo results found for {tool}, {action} action with {model}")
        else:
            latest_results_file = max(model_results_files, key=os.path.getctime)
            ground_truth_path = os.path.join(
                "data", "processed", f"{tool}_questions_and_answers_{action}_action.csv"
            )
            predictions = pd.read_csv(latest_results_file)
            ground_truth = pd.read_csv(ground_truth_path, dtype=str)
            print(f"\nCalculating metrics for {tool}, {action} action with {model}")
            calculate_metrics(ground_truth, predictions, print_errors=print_errors)


def generate_results(questions_path, model_name):
    """Generates results for a given model and set of questions. Saves the results to a csv file."""
    questions = pd.read_csv(
        questions_path,
        usecols=["question"],
    )["question"].tolist()

    results = pd.DataFrame(
        columns=["question", "function_calls", "full_response", "stopped"]
    )

    if model_name == "gpt-3.5-turbo-instruct":
        llm = OpenAI(
            model_name="gpt-3.5-turbo-instruct",
            openai_api_key=OPENAI_KEY,
            temperature=0,
            model_kwargs={"seed": 42},
        )
    elif model_name == "gpt-4-0125-preview":
        llm = ChatOpenAI(
            model_name="gpt-4-0125-preview",
            openai_api_key=OPENAI_KEY,
            temperature=0,
            model_kwargs={"seed": 42},
        )
    else:
        raise ValueError(
            "Invalid --model_name. Must be gpt-3.5-turbo-instruct or gpt-4-0125-preview."
        )

    agent = initialize_agent(
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        tools=email_toolkit + calendar_toolkit,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=5,
    )
    agent.agent.llm_chain.prompt.messages[0].prompt.template = (
        "The year is 2023. " + agent.agent.llm_chain.prompt.messages[0].prompt.template
    )

    for question in questions:
        response = agent({"input": question})
        function_calls = []
        for step in response["intermediate_steps"]:
            function_calls.append(convert_agent_action_to_function_call(step[-2]))

        agent_stopped = (
            True
            if response["output"]
            == "Agent stopped due to iteration limit or time limit."
            else False
        )

        print(f"### Question: {question}")
        print(f"### Answer: {function_calls}")

        results = pd.concat(
            [
                results,
                pd.DataFrame(
                    [
                        [
                            question,
                            ",".join(function_calls),
                            str(response),
                            agent_stopped,
                        ]
                    ],
                    columns=["question", "function_calls", "full_response", "stopped"],
                ),
            ],
            ignore_index=True,
        )
        # Reset all data after each question
        calendar.CALENDAR_EVENTS = pd.read_csv(
            "data/processed/calendar_events.csv", dtype=str
        )
        email.EMAILS = pd.read_csv("data/processed/emails.csv", dtype=str)

    question_type = (
        questions_path.split("/")[-1]
        .split(".")[0]
        .replace("questions_and_answers_", "")
    )
    domain, action_length = question_type.split("_")[:2]
    save_dir = os.path.join("data", "results", domain, action_length)
    os.makedirs(save_dir, exist_ok=True)

    # Removes microseconds and makes it more readable
    current_datetime = (
        str(pd.Timestamp.now()).split(".")[0].replace(" ", "_").replace(":", "-")
    )
    save_path = os.path.join(save_dir, model_name + "_" + current_datetime + ".csv")
    results.to_csv(save_path, index=False, quoting=csv.QUOTE_ALL)
    return results

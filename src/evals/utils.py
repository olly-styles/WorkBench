import re
import os
import pandas as pd
from langchain_openai import ChatOpenAI, OpenAI
from langchain.agents import initialize_agent, AgentType
import csv
from src.tools import calendar, email, analytics
from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME
from src.tools.toolkits import (
    calendar_toolkit,
    email_toolkit,
    analytics_toolkit,
)


OPENAI_KEY = open("openai_key.txt", "r").read()
DOMAINS = [calendar, email, analytics]


def convert_agent_action_to_function_call(action):
    """Converts langchain_core.agents.AgentAction to an API call"""
    args = []
    for k, v in action.tool_input.items():
        args.append(f"{k}='{v}'")
    return action.tool + ".func(" + ", ".join(args) + ")"


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
    new_analytics_state pd.DataFrame
        The resulting analytics data after executing the actions.
    """
    for domain in DOMAINS:
        domain.reset_state()

    # Execute the actions
    for action in actions:
        try:
            eval(action)
        except:
            return False, None, None, None
    new_calendar_state = calendar.CALENDAR_EVENTS.copy()
    new_email_state = email.EMAILS.copy()
    new_analytics_state = analytics.PLOTS_DATA.copy()

    # Reset the state of the tools
    for domain in DOMAINS:
        domain.reset_state()
    return True, new_calendar_state, new_email_state, new_analytics_state


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
    (
        successful_execution,
        predicted_calendar_state,
        predicted_email_state,
        predicted_analytics_state,
    ) = execute_actions_and_reset_state(predicted_actions)
    (
        _,
        ground_truth_calendar_state,
        ground_truth_email_state,
        ground_truth_analytics_state,
    ) = execute_actions_and_reset_state(ground_truth_actions)
    return (
        successful_execution
        and predicted_calendar_state.equals(ground_truth_calendar_state)
        and predicted_email_state.equals(ground_truth_email_state)
        and predicted_analytics_state.equals(ground_truth_analytics_state)
    )


def extract_function_names(s):
    """Extracts function names from a string"""
    return re.findall(r"(\b\w+\.\w+)\(", s)


def has_side_effects(predicted_actions, ground_truth_actions):
    """
    Checks if the predicted actions have side effects by comparing the state change after executing the actions.

    Parameters
    ----------
    predicted_actions : list
        List of predicted actions as strings.
    ground_truth_actions : list
        List of ground truth actions as strings.

    Returns
    -------
    bool
        True if the predicted actions result in different state change than the ground truth actions.

    """
    for domain in DOMAINS:
        domain.reset_state()
    original_state = {
        "calendar": calendar.CALENDAR_EVENTS.copy(),
        "email": email.EMAILS.copy(),
        "analytics": analytics.PLOTS_DATA.copy(),
    }
    (
        successful_execution,
        predicted_calendar_state,
        predicted_email_state,
        predicted_analytics_state,
    ) = execute_actions_and_reset_state(predicted_actions)

    if not successful_execution:
        return False
    state_changed = not predicted_calendar_state.equals(original_state["calendar"])
    state_changed |= not predicted_email_state.equals(original_state["email"])
    state_changed |= not predicted_analytics_state.equals(original_state["analytics"])

    correct = is_correct(predicted_actions, ground_truth_actions)
    return state_changed and not correct


def generate_question_and_answer(template):
    """Generates question and answer from template."""
    logic = template["logic"]()
    question = template["question"].format(**logic)
    stop = logic.get("no_action", False)
    if stop:
        answer = []
    if template["answer"] == "in_logic":
        answer = logic["answer"]
    else:
        answer = [step.format(**logic) for step in template["answer"]]
    return {"question": question, "answer": answer, "template": {k: template[k] for k in template if k != "logic"}}


def generate_all_questions_and_answers(templates, max_questions_per_template, print=True):
    """Generates a limited number of unique questions and answers for each template."""
    generated_questions_and_answers = []
    for template in templates:
        for _ in range(max_questions_per_template):
            q_and_a = generate_question_and_answer(template)
            questions = [q["question"] for q in generated_questions_and_answers]
            if q_and_a["question"] not in questions:
                generated_questions_and_answers.append(q_and_a)

    if print:
        for question_and_answer in generated_questions_and_answers:
            print(question_and_answer["question"])
            print(question_and_answer["answer"])
            print(question_and_answer["template"])
        
    return generated_questions_and_answers

def calculate_metrics(ground_truth_df, predictions_df, print_errors=True):
    """"""
    predictions = predictions_df.rename(columns={"function_calls": "prediction"})
    predictions = predictions.fillna("")

    ground_truth = ground_truth_df.rename(columns={"answer": "ground_truth"})
    df = predictions.merge(ground_truth, on="question")
    assert (
        len(predictions) == len(ground_truth) == len(df)
    ), f"{len(predictions)} predictions does not match {len(ground_truth_df)} ground truth answers. Check that the predictions and ground truth are for the same questions."
    df["correct"] = [
        is_correct(pred, gt) for pred, gt in zip(df["prediction"], df["ground_truth"])
    ]
    df["unwanted_side_effects"] = [
        has_side_effects(pred, gt)
        for pred, gt in zip(df["prediction"], df["ground_truth"])
    ]

    # print out the questions that were not answered correctly
    if print_errors:
        for _, row in df[~df["correct"]].iterrows():
            print(f"Question: {row['question']}")
            print(f"Prediction: {row['prediction']}")
            print(f"Ground truth: {row['ground_truth']}")
            print(f"Unwanted side effects: {row['unwanted_side_effects']}")
            print("")

    print(f"Accuracy: {round(df['correct'].mean() * 100, 2)}%")


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
        tools=email_toolkit + calendar_toolkit + analytics_toolkit,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=5,
    )
    agent.agent.llm_chain.prompt.messages[0].prompt.template = (
        f"Today's date is {HARDCODED_CURRENT_TIME.date()}. Remember the current date when answering queries."
        + agent.agent.llm_chain.prompt.messages[0].prompt.template
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
                            function_calls,
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
    if "multi" in domain:  # exception handler for multi-domain questions
        save_dir = os.path.join("data", "results", "multi_domain", "multi")
    else:
        save_dir = os.path.join("data", "results", domain, action_length)
    os.makedirs(save_dir, exist_ok=True)

    # Removes microseconds and makes it more readable
    current_datetime = (
        str(pd.Timestamp.now()).split(".")[0].replace(" ", "_").replace(":", "-")
    )
    save_path = os.path.join(save_dir, model_name + "_" + current_datetime + ".csv")
    results.to_csv(save_path, index=False, quoting=csv.QUOTE_ALL)
    return results

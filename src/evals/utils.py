import re
import os
import pandas as pd
from langchain_openai import ChatOpenAI, OpenAI
from langchain_community.chat_models.anthropic import ChatAnthropic
from langchain_community.chat_models.anyscale import ChatAnyscale

from langchain.agents import initialize_agent, AgentType
import csv
from src.tools import calendar, email, analytics, project_management, customer_relationship_manager
from src.data_generation.data_generation_utils import HARDCODED_CURRENT_TIME
from src.tools.toolkits import (
    calendar_toolkit,
    email_toolkit,
    analytics_toolkit,
    project_management_toolkit,
    customer_relationship_manager_toolkit,
)


OPENAI_KEY = open("openai_key.txt", "r").read()
ANTHROPIC_KEY = open("anthropic_key.txt", "r").read()
ANYSCALE_KEY = open("anyscale_key.txt", "r").read()
DOMAINS = [calendar, email, analytics, project_management, customer_relationship_manager]
AVAILABLE_LLMS = [
    "gpt-3.5",
    "gpt-4",
    "claude-2",
    "llama2-70b",
    "mistral-7B",
]


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
            eval(action.lower())
        except:
            continue
    new_calendar_state = calendar.CALENDAR_EVENTS.copy()
    new_email_state = email.EMAILS.copy()
    new_analytics_state = analytics.PLOTS_DATA.copy()
    new_project_management_state = project_management.PROJECT_TASKS.copy()
    new_customer_relationship_manager_state = customer_relationship_manager.CRM_DATA.copy()

    # Reset the state of the tools
    for domain in DOMAINS:
        domain.reset_state()
    return (
        True,
        new_calendar_state,
        new_email_state,
        new_analytics_state,
        new_project_management_state,
        new_customer_relationship_manager_state,
    )


def is_correct(predicted_actions, ground_truth_actions, error):
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
    (
        successful_execution,
        predicted_calendar_state,
        predicted_email_state,
        predicted_analytics_state,
        predicted_project_management_state,
        predicted_customer_relationship_manager_state,
    ) = execute_actions_and_reset_state(predicted_actions)
    (
        _,
        ground_truth_calendar_state,
        ground_truth_email_state,
        ground_truth_analytics_state,
        ground_truth_project_management_state,
        ground_truth_customer_relationship_manager_state,
    ) = execute_actions_and_reset_state(ground_truth_actions)
    return (
        successful_execution
        and predicted_calendar_state.equals(ground_truth_calendar_state)
        and predicted_email_state.equals(ground_truth_email_state)
        and predicted_analytics_state.equals(ground_truth_analytics_state)
        and predicted_project_management_state.equals(ground_truth_project_management_state)
        and predicted_customer_relationship_manager_state.equals(ground_truth_customer_relationship_manager_state)
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
        "project_management": project_management.PROJECT_TASKS.copy(),
        "customer_relationship_manager": customer_relationship_manager.CRM_DATA.copy(),
    }
    (
        successful_execution,
        predicted_calendar_state,
        predicted_email_state,
        predicted_analytics_state,
        predicted_project_management_state,
        predicted_customer_relationship_manager_state,
    ) = execute_actions_and_reset_state(predicted_actions)

    state_changed = not predicted_calendar_state.equals(original_state["calendar"])
    state_changed |= not predicted_email_state.equals(original_state["email"])
    state_changed |= not predicted_analytics_state.equals(original_state["analytics"])
    state_changed |= not predicted_project_management_state.equals(original_state["project_management"])
    state_changed |= not predicted_customer_relationship_manager_state.equals(
        original_state["customer_relationship_manager"]
    )

    errors = ""  # Errors like exceeding the context window or running out of time don't have side effects, so we assume no errors
    correct = is_correct(predicted_actions, ground_truth_actions, errors)
    return state_changed and not correct


def generate_query_and_answer(template):
    """Generates query and answer from template."""
    logic = template["logic"]()
    query = template["query"].format(**logic)
    answer = logic["answer"]
    return {
        "query": query,
        "answer": answer,
        "template": {k: template[k] for k in template if k != "logic"},
    }


def generate_all_queries_and_answers(templates, max_queries_per_template, verbose=True):
    """Generates a limited number of unique queries and answers for each template."""
    generated_queries_and_answers = []
    for template in templates:
        for _ in range(max_queries_per_template):
            q_and_a = generate_query_and_answer(template)
            queries = [q["query"] for q in generated_queries_and_answers]
            if q_and_a["query"] not in queries:
                generated_queries_and_answers.append(q_and_a)

    if verbose:
        for query_and_answer in generated_queries_and_answers:
            print(query_and_answer["query"])
            print(query_and_answer["answer"])
            print(query_and_answer["template"])

    return generated_queries_and_answers


def calculate_metrics(ground_truth_df, predictions_df, print_errors=True):
    """"""
    predictions = predictions_df.rename(columns={"function_calls": "prediction"})
    predictions = predictions.fillna("")

    ground_truth = ground_truth_df.rename(columns={"answer": "ground_truth"})
    df = predictions.merge(ground_truth, on="query")
    assert (
        len(predictions) == len(ground_truth) == len(df)
    ), f"{len(predictions)} predictions does not match {len(ground_truth_df)} ground truth answers. Check that the predictions and ground truth are for the same queries."
    df["correct"] = [
        is_correct(pred, gt, error) for pred, gt, error in zip(df["prediction"], df["ground_truth"], df["error"])
    ]
    df["unwanted_side_effects"] = [has_side_effects(pred, gt) for pred, gt in zip(df["prediction"], df["ground_truth"])]

    # print out the queries that were not answered correctly
    if print_errors:
        for _, row in df[~df["correct"]].iterrows():
            # full response string to dict
            print("--------------------------------------------")
            print(f"Query:")
            print(f"    {row['query']}")
            print()
            print(f"Prediction:")
            for action in row["prediction"]:
                print(f"    {action}")
            print()
            print(f"Ground truth:")
            for action in row["ground_truth"]:
                print(f"    {action}")
            print()
            print(f"Unwanted side effects: {row['unwanted_side_effects']}")
            print()
            print(f"Error: {row['error']}")
            print("")

    print(f"Accuracy: {round(df['correct'].mean() * 100, 2)}%")


def get_latest_results_from_dir(results_root_dir, tool, action, model_list, print_errors=False):
    """Get the latest results for each model in the results directory"""
    results_dir = os.path.join(results_root_dir, tool, action)
    results_files = os.listdir(results_dir)
    for model in model_list:
        model_results_files = [os.path.join(results_dir, file) for file in results_files if model in file]
        if not len(model_results_files):
            print(f"\nNo results found for {tool}, {action} action with {model}")
        else:
            latest_results_file = max(model_results_files, key=os.path.getctime)
            ground_truth_path = os.path.join("data", "processed", f"{tool}_queries_and_answers_{action}_action.csv")
            predictions = pd.read_csv(latest_results_file)
            ground_truth = pd.read_csv(ground_truth_path, dtype=str)
            print(f"\nCalculating metrics for {tool}, {action} action with {model}")
            calculate_metrics(ground_truth, predictions, print_errors=print_errors)


def get_toolkits(toolkits):
    """Get the toolkits to be used for the agent."""
    tools = []
    if "email" in toolkits:
        tools += email_toolkit
    if "calendar" in toolkits:
        tools += calendar_toolkit
    if "analytics" in toolkits:
        tools += analytics_toolkit
    if "project_management" in toolkits:
        tools += project_management_toolkit
    if "customer_relationship_manager" in toolkits:
        tools += customer_relationship_manager_toolkit
    return tools


def generate_results(
    queries_path,
    model_name,
    toolkits=["email", "calendar", "analytics", "project_management", "customer_relationship_manager"],
):
    """Generates results for a given model and set of queries. Saves the results to a csv file."""
    queries = pd.read_csv(
        queries_path,
        usecols=["query"],
    )["query"].tolist()

    results = pd.DataFrame(columns=["query", "function_calls", "full_response", "error"])
    if model_name == "gpt-3.5":
        llm = OpenAI(
            model_name="gpt-3.5-turbo-instruct",
            openai_api_key=OPENAI_KEY,
            temperature=0,
            model_kwargs={"seed": 42},
        )
    elif model_name == "gpt-4":
        llm = ChatOpenAI(
            model_name="gpt-4-0125-preview",
            openai_api_key=OPENAI_KEY,
            temperature=0,
            model_kwargs={"seed": 42},
        )
    elif model_name == "claude-2":
        llm = ChatAnthropic(
            model_name="claude-2",
            anthropic_api_key=ANTHROPIC_KEY,
            temperature=0,
        )
    elif model_name == "llama2-70b":
        llm = ChatAnyscale(
            model="meta-llama/Llama-2-70b-chat-hf",
            anyscale_api_key=ANYSCALE_KEY,
            temperature=0,
        )
    elif model_name == "mistral-7B":
        llm = ChatAnyscale(
            model="mistralai/Mistral-7B-Instruct-v0.1",
            anyscale_api_key=ANYSCALE_KEY,
            temperature=0,
        )

    else:
        raise ValueError("Invalid --model_name. Must be one of " + ", ".join(AVAILABLE_LLMS))

    tools = get_toolkits(toolkits)

    agent = initialize_agent(
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        tools=tools,
        verbose=True,
        return_intermediate_steps=True,
        max_iterations=15,
        max_execution_time=60,
    )
    agent.agent.llm_chain.prompt.messages[0].prompt.template = (
        f"Today's date is {HARDCODED_CURRENT_TIME.strftime('%A')}, {HARDCODED_CURRENT_TIME.date()} and the current time is {HARDCODED_CURRENT_TIME.time()}. Remember the current date and time when answering queries. Meetings must not start before 9am or end after 6pm."
        + agent.agent.llm_chain.prompt.messages[0].prompt.template
    )

    for query in queries:
        error = ""
        function_calls = []
        response = ""
        try:
            response = agent({"input": query})
            for step in response["intermediate_steps"]:
                function_calls.append(convert_agent_action_to_function_call(step[-2]))

            error = (
                response["output"]
                if response["output"] == "Agent stopped due to iteration limit or time limit."
                else error
            )

        except Exception as e:
            # APIs for the LLMs we support have different error messages for when the context window is exceeded
            context_window_error_messages = [
                "maximum input length",
                "maximum context length",
                "prompt is too long",
                "Request too large",
            ]
            if any([msg in str(e) for msg in context_window_error_messages]):
                print(f"Error with query: {query}")
                error = "Context window exceeded"
            else:
                print(f"Unknown error with query: {query}")
                error = str(e)

        print(f"### Query: {query}")
        print(f"### Answer: {function_calls}")

        results = pd.concat(
            [
                results,
                pd.DataFrame(
                    [
                        [
                            query,
                            function_calls,
                            str(response),
                            error,
                        ]
                    ],
                    columns=["query", "function_calls", "full_response", "error"],
                ),
            ],
            ignore_index=True,
        )
        # Reset all data after each query
        for domain in DOMAINS:
            domain.reset_state()

    domain = queries_path.split("/")[-1].split(".")[0].replace("_queries_and_answers", "")
    save_dir = os.path.join("data", "results", domain)
    os.makedirs(save_dir, exist_ok=True)

    # Removes microseconds and makes it more readable
    current_datetime = str(pd.Timestamp.now()).split(".")[0].replace(" ", "_").replace(":", "-")
    save_path = os.path.join(save_dir, model_name + "_" + str(toolkits) + current_datetime + ".csv")
    results.to_csv(save_path, index=False, quoting=csv.QUOTE_ALL)
    return results

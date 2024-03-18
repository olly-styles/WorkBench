import re
import os
import pandas as pd
import random
import ast
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
    company_directory_toolkit,
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
        args.append(f'{k}="{v}"')
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

    def convert_strs_to_lowercase(df):
        # For some fields the case matters, so we don't convert them to lowercase
        fields_not_to_convert = ["status", "list_name", "board"]
        for col in df.columns:
            if col not in fields_not_to_convert:
                df[col] = df[col].str.lower()
        return df

    # We allow for case-insensitive comparison of strings for most fields
    predicted_calendar_state = convert_strs_to_lowercase(predicted_calendar_state)
    predicted_email_state = convert_strs_to_lowercase(predicted_email_state)
    predicted_analytics_state = convert_strs_to_lowercase(predicted_analytics_state)
    predicted_project_management_state = convert_strs_to_lowercase(predicted_project_management_state)
    predicted_customer_relationship_manager_state = convert_strs_to_lowercase(
        predicted_customer_relationship_manager_state
    )

    ground_truth_calendar_state = convert_strs_to_lowercase(ground_truth_calendar_state)
    ground_truth_email_state = convert_strs_to_lowercase(ground_truth_email_state)
    ground_truth_analytics_state = convert_strs_to_lowercase(ground_truth_analytics_state)
    ground_truth_project_management_state = convert_strs_to_lowercase(ground_truth_project_management_state)
    ground_truth_customer_relationship_manager_state = convert_strs_to_lowercase(
        ground_truth_customer_relationship_manager_state
    )

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
    if "alternative_queries" in template:
        possible_queries = [template["query"]] + template["alternative_queries"]
        query_template = random.choice(possible_queries)
        query = query_template.format(**logic)
    else:
        query_template = template["query"]
        query = query_template.format(**logic)
    answer = logic["answer"]
    domains = template.get("domains", [])
    return {
        "query": query,
        "answer": answer,
        "base_template": template["query"],
        "chosen_template": query_template,
        "domains": domains,
    }


def generate_all_queries_and_answers(templates, max_queries_per_template, verbose=True):
    """Generates a limited number of unique queries and answers for each template."""
    generated_queries_and_answers = []
    for template in templates:
        queries_generated_for_template = 0
        while queries_generated_for_template < max_queries_per_template:
            q_and_a = generate_query_and_answer(template)
            queries = [q["query"] for q in generated_queries_and_answers]
            if q_and_a["query"] not in queries:
                generated_queries_and_answers.append(q_and_a)
                queries_generated_for_template += 1

    if verbose:
        for query_and_answer in generated_queries_and_answers:
            print(f"Base template:   {query_and_answer['base_template']}")
            print(f"Chosen template: {query_and_answer['chosen_template']}")
            print(f"Query:           {query_and_answer['query']}")
            print(f"Answer:          {query_and_answer['answer']}")
            print("--------------------------------------------")

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
    df["no_actions"] = [not len(pred) for pred in df["prediction"]]
    # wrong email if @example is in the prediction and @atlas is not in the prediction. Prediction is a list so needs to be converted to a string
    df["wrong_email"] = [("@example" in str(pred)) and ("@atlas" not in str(pred)) for pred in df["prediction"]]
    # as above but it also needs to not be correct
    df["wrong_email"] = df["wrong_email"] & ~df["correct"]

    # print out the queries that were not answered correctly
    if print_errors:
        print("--------------------------------------------")
        print("--------------------------------------------")
        print("ERRORS:")
        print("--------------------------------------------")
        print("--------------------------------------------")
        for _, row in df[~df["correct"]].iterrows():
            if not row["wrong_email"] and not row["no_actions"]:
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
                # print the full response
                print(f"Output:")
                output = get_output(row["full_response"])
                print(f"    {output}")

    print(f"Accuracy: {round(df['correct'].mean() * 100, 2)}% ({df['correct'].sum()} out of {len(df)})")
    print(
        f"Errors without unwanted side effects: {round((~df['correct'] & ~df['unwanted_side_effects']).mean() * 100, 2)}% ({(~df['correct'] & ~df['unwanted_side_effects']).sum()} out of {len(df)})"
    )
    print(
        f"Wrong email, no side effects: {round((df['wrong_email'] & ~df['unwanted_side_effects']).mean() * 100, 2)}% ({(df['wrong_email'] & ~df['unwanted_side_effects']).sum()} out of {len(df)})"
    )
    print(
        f"Didn't follow REACT framework: {round(df['no_actions'].mean() * 100, 2)}% ({df['no_actions'].sum()} out of {len(df)})"
    )
    print(
        f"Errors with unwanted side effects: {round(df['unwanted_side_effects'].mean() * 100, 2)}% ({df['unwanted_side_effects'].sum()} out of {len(df)})"
    )
    print(
        f"Wrong email with side effects: {round((df['wrong_email'] & df['unwanted_side_effects']).mean() * 100, 2)}% ({(df['wrong_email'] & df['unwanted_side_effects']).sum()} out of {len(df)})"
    )
    return df


def get_output(full_response):
    """Get the output from the full response"""
    pattern = r"AgentAction\(.*?\)"
    array_pattern = r"array\((.*?)\)"

    def quote_match(match):
        escaped_match = match.group().replace('"', '\\"')
        return f'"{escaped_match}"'

    simplified_string = re.sub(pattern, quote_match, full_response)
    simplified_string = re.sub(array_pattern, quote_match, simplified_string)
    simplified_string = simplified_string.replace("nan", "None")

    # Remove everything after "intermediate_steps" and add a curl bracket at close the dict
    simplified_string = simplified_string.split("intermediate_steps")[0]
    simplified_string = simplified_string[:-3] + "}"

    a = ast.literal_eval(simplified_string)
    return a["output"]


def get_latest_results_path(results_root_dir, model, tool):
    """Get the latest results file path and ground truth path for a given model and tool"""
    results_dir = os.path.join(results_root_dir, tool)
    results_files = os.listdir(results_dir)
    model_results_files = [os.path.join(results_dir, file) for file in results_files if model in file]
    ground_truth_path = os.path.join("data", "processed", "queries_and_answers", f"{tool}_queries_and_answers.csv")
    if not len(model_results_files):
        return None
    else:
        return max(model_results_files, key=os.path.getctime), ground_truth_path


def get_latest_results_from_dir(results_root_dir, model, tool, print_errors=False):
    """Get the latest results for each model in the results directory"""
    model_results_path, ground_truth_path = get_latest_results_path(results_root_dir, model, tool)
    if not model_results_path:
        print(f"\nNo results found for {tool} with {model}")
        return None
    else:
        predictions = pd.read_csv(model_results_path, dtype=str)
        ground_truth = pd.read_csv(ground_truth_path, dtype=str)
        ground_truth["answer"] = ground_truth["answer"].apply(ast.literal_eval)
        predictions["function_calls"] = predictions["function_calls"].apply(ast.literal_eval)
        print(f"\nCalculating metrics for {tool} with {model}")
        df = calculate_metrics(ground_truth, predictions, print_errors=print_errors)
        num_correct = df["correct"].sum()
        num_incorrect = len(df) - num_correct
        num_side_effects = df["unwanted_side_effects"].sum()
        return num_correct, num_incorrect, num_side_effects


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
    # The company directory toolkit is always included in order to find email addresses by name
    tools += company_directory_toolkit
    return tools


def generate_results(queries_path, model_name, tool_selection="all"):
    """Generates results for a given model and set of queries. Saves the results to a csv file."""
    toolkits = ["email", "calendar", "analytics", "project_management", "customer_relationship_manager"]
    queries_df = pd.read_csv(queries_path)
    queries = queries_df["query"].tolist()

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
    elif model_name == "mistral-8x7B":
        llm = ChatAnyscale(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            anyscale_api_key=ANYSCALE_KEY,
            temperature=0,
        )

    else:
        raise ValueError("Invalid --model_name. Must be one of " + ", ".join(AVAILABLE_LLMS))

    tools = get_toolkits(toolkits)

    for i, query in enumerate(queries):
        if tool_selection == "domains":
            toolkits = queries_df["domains"].iloc[i].strip("][").replace("'", "").split(", ")
            tools = get_toolkits(toolkits)

        agent = initialize_agent(
            llm=llm,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            tools=tools,
            verbose=True,
            return_intermediate_steps=True,
            max_iterations=20,
            max_execution_time=120,
        )
        agent.agent.llm_chain.prompt.messages[0].prompt.template = (
            f"Today's date is {HARDCODED_CURRENT_TIME.strftime('%A')}, {HARDCODED_CURRENT_TIME.date()} and the current time is {HARDCODED_CURRENT_TIME.time()}. Remember the current date and time when answering queries. Meetings must not start before 9am or end after 6pm."
            + agent.agent.llm_chain.prompt.messages[0].prompt.template
        )
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
    save_path = os.path.join(save_dir, model_name + "_" + tool_selection + "_" + current_datetime + ".csv")
    results.to_csv(save_path, index=False, quoting=csv.QUOTE_ALL)
    return results

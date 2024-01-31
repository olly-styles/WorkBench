import pandas as pd
import argparse
import warnings
from langchain_openai import ChatOpenAI, OpenAI
from langchain.agents import initialize_agent, AgentType
import sys
import os
import csv

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.evals.utils import convert_agent_action_to_function_call
from src.tools.toolkits import calendar_toolkit, email_toolkit
from src.tools import calendar, email

warnings.filterwarnings("ignore")  # supress langchain deprication warnings

parser = argparse.ArgumentParser()
parser.add_argument(
    "--model_name",
    type=str,
    help="model name, either gpt-3.5-turbo-instruct or gpt-4-0125-preview",
    required=True,
)
parser.add_argument(
    "--questions_path",
    type=str,
    help="path to questions and answers csv. By default this is stored in data/processed/",
    required=True,
)

args = parser.parse_args()

OPENAI_KEY = open("openai_key.txt", "r").read()

questions = pd.read_csv(
    args.questions_path,
    usecols=["question"],
)["question"].tolist()

results = pd.DataFrame(
    columns=["question", "function_calls", "full_response", "stopped"]
)

if args.model_name == "gpt-3.5-turbo-instruct":
    llm = OpenAI(
        model_name="gpt-3.5-turbo-instruct",
        openai_api_key=OPENAI_KEY,
        temperature=0,
        model_kwargs={"seed": 42},
    )
elif args.model_name == "gpt-4-0125-preview":
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
        if response["output"] == "Agent stopped due to iteration limit or time limit."
        else False
    )

    print(f"### Question: {question}")
    print(f"### Answer: {function_calls}")

    results = pd.concat(
        [
            results,
            pd.DataFrame(
                [[question, ",".join(function_calls), str(response), agent_stopped]],
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


current_datetime = str(pd.Timestamp.now())
results.to_csv(
    "data/results/answers_" + args.model_name + current_datetime + ".csv",
    index=False,
    quoting=csv.QUOTE_ALL,
)

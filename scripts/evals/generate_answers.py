import pandas as pd
from langchain_openai import ChatOpenAI, OpenAI
from langchain.agents import initialize_agent, AgentType
from src.eval.utils import convert_agent_action_to_function_call
from src.tools.toolkits import calendar_toolkit, email_toolkit
from src.tools import calendar, email

# supress langchain warnings
import warnings

warnings.filterwarnings("ignore")


OPENAI_KEY = open("openai_key.txt", "r").read()
questions = pd.read_csv(
    "data/processed/calendar_questions_and_answers_multi_action.csv",
    usecols=["question"],
)["question"].tolist()

results = pd.DataFrame(
    columns=["question", "function_calls", "full_response", "stopped"]
)
llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_KEY, temperature=0)
# llm = OpenAI(
#     model_name="gpt-3.5-turbo-instruct", openai_api_key=OPENAI_KEY, temperature=0
# )


agent = initialize_agent(
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    tools=email_toolkit + calendar_toolkit,
    verbose=True,
    return_intermediate_steps=True,
    max_iterations=5,
)

print(
    "Prompt template length (approx):",
    int(
        len(agent.agent.llm_chain.prompt[0].__dict__["prompt"].__dict__["template"]) / 4
    ),
    "tokens",
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
    # convert function_calls to string
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
results.to_csv("data/results/answers" + current_datetime + ".csv", index=False)

import pandas as pd
from langchain_openai import ChatOpenAI, OpenAI
from langchain.agents import initialize_agent, AgentType
from src.eval.utils import convert_agent_action_to_function_call
from src.tools import calendar


OPENAI_KEY = open("openai_key.txt", "r").read()
questions = pd.read_csv(
    "data/processed/questions_and_answers.csv", usecols=["question"]
)["question"].tolist()

results = pd.DataFrame(columns=["question", "answer"])
llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_KEY, temperature=0)
# llm = OpenAI(
#     model_name="gpt-3.5-turbo-instruct", openai_api_key=OPENAI_KEY, temperature=0
# )
# llm = ChatOpenAI(
#     model_name="gpt-3.5-turbo-1106", openai_api_key=OPENAI_KEY, temperature=0
# )


agent = initialize_agent(
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    tools=[calendar.get_event_information_by_id, calendar.search_events],
    verbose=True,
    return_intermediate_steps=True,
)

for question in questions:
    response = agent({"input": question})
    last_function_call = convert_agent_action_to_function_call(
        response["intermediate_steps"][0][-2]
    )
    print(f"### Question: {question}")
    print(f"### Answer: {last_function_call}")
    results = pd.concat(
        [
            results,
            pd.DataFrame(
                [[question, last_function_call]],
                columns=["question", "answer"],
            ),
        ],
        ignore_index=True,
    )

current_datetime = str(pd.Timestamp.now())
results.to_csv("data/results/answers" + current_datetime + ".csv", index=False)

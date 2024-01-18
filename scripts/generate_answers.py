import pandas as pd
from langchain_openai import ChatOpenAI, OpenAI
from langchain.agents import initialize_agent, AgentType
from src.eval.utils import convert_agent_action_to_function_call
from src.tools import calendar


OPENAI_KEY = open("openai_key.txt", "r").read()
questions = pd.read_csv(
    "data/processed/questions_and_answers.csv", usecols=["question"]
)["question"].tolist()

results = pd.DataFrame(
    columns=["question", "answer", "function_calls", "full_response"]
)
# llm = ChatOpenAI(model_name="gpt-4", openai_api_key=OPENAI_KEY, temperature=0)
llm = OpenAI(
    model_name="gpt-3.5-turbo-instruct", openai_api_key=OPENAI_KEY, temperature=0
)
# # Note the the latest version of GPT3.5 (below) does not show it's chain of thoughts for some reason
# llm = ChatOpenAI(
#     model_name="gpt-3.5-turbo-1106", openai_api_key=OPENAI_KEY, temperature=0
# )


agent = initialize_agent(
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    tools=[
        calendar.get_event_information_by_id,
        calendar.search_events,
        calendar.create_event,
        calendar.delete_event,
        calendar.update_event,
    ],
    verbose=True,
    return_intermediate_steps=True,
)

for question in questions:
    response = agent({"input": question})
    function_calls = []
    for step in response["intermediate_steps"]:
        function_calls.append(convert_agent_action_to_function_call(step[-2]))

    final_function_call = "" if not function_calls else function_calls[-1]
    other_function_calls = [] if len(function_calls) < 2 else function_calls[:-1]

    print(f"### Question: {question}")
    print(f"### Answer: {final_function_call}")
    # convert function_calls to string
    results = pd.concat(
        [
            results,
            pd.DataFrame(
                [
                    [
                        question,
                        final_function_call,
                        ",".join(other_function_calls),
                        str(response),
                    ]
                ],
                columns=["question", "answer", "function_calls", "full_response"],
            ),
        ],
        ignore_index=True,
    )
    # Reset calendar events after each question
    calendar.CALENDAR_EVENTS = pd.read_csv(
        "data/processed/calender_events.csv", dtype=str
    )


current_datetime = str(pd.Timestamp.now())
results.to_csv("data/results/answers" + current_datetime + ".csv", index=False)

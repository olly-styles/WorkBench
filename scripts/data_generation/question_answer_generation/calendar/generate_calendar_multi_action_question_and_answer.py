import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.data_generation_utils import (
    generate_end_time,
    get_natural_language_date,
    generate_event_duration_minutes,
    format_event_duration,
)
from src.tools import calendar

random.seed(42)

MULTI_ACTION_TEMPLATES = [
    {
        "question": "Delete the first event on {date}",
        "answer": """calendar.delete_event({{'event_id': '{first_event_id}'}})""",
    },
    {
        "question": "Change the name of the last event on {date} to {event_name}",
        "answer": """calendar.update_event({{'event_id': '{last_event_id}', 'field': 'event_name', 'new_value': '{event_name}'}})""",
    },
    {
        "question": "Push back my first meeting with {name} on {date} by {duration}s",
        "answer": """calendar.update_event({{'event_id': '{first_event_with_name_id}', 'field': 'event_start', 'new_value': '{new_start}'}})""",
    },
    {
        "question": "Delete the {event_name} event",
        "answer": """calendar.delete_event({{'event_id': '{event_id}'}})""",
    },
    {
        "question": "Change the name of the {event_name} event to {new_event_name}",
        "answer": """calendar.update_event({{'event_id': '{event_id}', 'field': 'event_name', 'new_value': '{new_event_name}'}})""",
    },
]

calendar_events = pd.read_csv("data/processed/calendar_events.csv", dtype=str)
dates = list(calendar_events["event_start"].str.split(" ").str[0].unique())
times = list(calendar_events["event_start"].str.split(" ").str[1].unique())
events = list(calendar_events["event_name"].unique())
emails = list(calendar_events["participant_email"].unique())
event_ids = list(calendar_events["event_id"].unique())

# Generate a limited number of unique multi-action questions and answers
generated_questions_and_answers = []
max_questions_per_template = 3  # Limit the number of questions per template

for template in MULTI_ACTION_TEMPLATES:
    for _ in range(max_questions_per_template):
        date = random.choice(dates)
        natural_language_date = get_natural_language_date(date)
        duration_minutes = generate_event_duration_minutes()
        duration = format_event_duration(duration_minutes)
        event_id = random.choice(event_ids)
        event_name = calendar_events.set_index("event_id").loc[event_id, "event_name"]
        new_event_name = random.choice(events)
        while new_event_name == event_name:
            new_event_name = random.choice(events)

        first_event_id = calendar.search_events.func(
            time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59"
        )[0]["event_id"]
        last_event_id = calendar.search_events.func(
            time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59"
        )[-1]["event_id"]
        events_on_date = calendar.search_events.func(
            query="", time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59"
        )
        name = random.choice(events_on_date)["participant_email"].split(".")[0]
        first_event_with_name = calendar.search_events.func(
            query=name, time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59"
        )[0]
        first_event_with_name_id = first_event_with_name["event_id"]

        new_start = generate_end_time(first_event_with_name["event_start"], duration)

        question = template["question"].format(
            date=natural_language_date,
            duration=duration,
            name=name,
            event_name=event_name,
            new_event_name=new_event_name,
        )
        answer = template["answer"].format(
            first_event_id=first_event_id,
            last_event_id=last_event_id,
            first_event_with_name_id=first_event_with_name_id,
            new_start=new_start,
            event_name=event_name,
            event_id=event_id,
            new_event_name=new_event_name,
        )

        if question not in generated_questions_and_answers:
            generated_questions_and_answers.append(
                {"question": question, "answer": answer, "template": template}
            )
for question_and_answer in generated_questions_and_answers:
    print(question_and_answer["question"])
    print(question_and_answer["answer"])
    print(question_and_answer["template"])

df = pd.DataFrame(generated_questions_and_answers)
df.to_csv(
    "data/processed/calendar_questions_and_answers_multi_action.csv",
    index=False,
    quoting=csv.QUOTE_ALL,
)

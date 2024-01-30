import pandas as pd
import random
import csv
import sys
import os
project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.calendar.data_generation_utils import (
    generate_end_time,
    generate_event_duration,
)

random.seed(42)

SINGLE_ACTION_TEMPLATES = [
    {
        "question": "How many events are there on {date} with Carlos?",
        "answer": """calendar.search_events({{'query': 'Carlos', 'time_min': '{date} 00:00:00', 'time_max': '{date} 23:59:59'}})""",
    },
    {
        "question": "Create a {duration} event called {event_name} on {date} at {time} with {email}",
        "answer": """calendar.create_event({{'event_name': '{event_name}', 'participant_email': '{email}', 'event_start': '{date} {time}', 'duration': '{duration_minutes}'}})""",
    },
    {
        "question": "Delete the event {event_id}",
        "answer": """calendar.delete_event({{'event_id': '{event_id}'}})""",
    },
    {
        "question": "Change the name of the event {event_id} to {event_name}",
        "answer": """calendar.update_event({{'event_id': '{event_id}', 'field': 'event_name', 'new_value': '{event_name}'}})""",
    },
]

calendar_events = pd.read_csv("data/processed/calendar_events.csv", dtype=str)
dates = list(calendar_events["event_start"].str.split(" ").str[0].unique())
times = list(calendar_events["event_start"].str.split(" ").str[1].unique())
events = list(calendar_events["event_name"].unique())
emails = list(calendar_events["participant_email"].unique())
event_ids = list(calendar_events["event_id"].unique())


# Generate a limited number of unique single-action questions and answers
generated_questions_and_answers = []
max_questions_per_template = 3  # Limit the number of questions per template

for template in SINGLE_ACTION_TEMPLATES:
    for _ in range(max_questions_per_template):
        date = random.choice(dates)
        time = random.choice(times)
        duration_minutes = int(generate_event_duration() * 60)
        duration = "{length} hour".format(
            length=int(duration_minutes / 60)
            if duration_minutes / 60 > 1
            else duration_minutes / 60
        )
        event_name = random.choice(events)
        email = random.choice(emails)
        end_time = generate_end_time(f"{date} {time}", duration)
        event_id = random.choice(event_ids)

        question = template["question"].format(
            date=date,
            time=time,
            duration=duration,
            event_name=event_name,
            email=email,
            end_time=end_time,
            event_id=event_id,
        )
        answer = template["answer"].format(
            date=date,
            time=time,
            duration=duration,
            event_name=event_name,
            email=email,
            end_time=end_time,
            event_id=event_id,
            duration_minutes=duration_minutes,
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
    "data/processed/calendar_questions_and_answers_single_action.csv",
    index=False,
    quoting=csv.QUOTE_ALL,
)

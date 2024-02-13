import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.evals.utils import generate_all_questions_and_answers
from src.data_generation.data_generation_utils import (
    generate_event_duration_minutes,
    format_event_duration,
    get_natural_language_time,
    get_natural_language_date,
)

random.seed(42)

def template_1_logic():
    duration_minutes = generate_event_duration_minutes()
    duration = format_event_duration(duration_minutes)
    email = random.choice(emails)
    event_name = random.choice(events)
    date = random.choice(dates)
    natural_language_date = get_natural_language_date(date)
    time = random.choice(times)
    natural_language_time = get_natural_language_time(time)
    return {
        "duration_minutes": duration_minutes,
        "duration": duration,
        "email": email,
        "event_name": event_name,
        "date": date,
        "natural_language_date": natural_language_date,
        "time": time,
        "natural_language_time": natural_language_time,
    }


SINGLE_ACTION_TEMPLATES = [
    {
        "question": "Create a {duration} event called {event_name} on {natural_language_date} at {time} with {email}",
        "answer": [
            """calendar.create_event.func(event_name='{event_name}', participant_email='{email}', event_start='{date} {time}', duration='{duration_minutes}')"""
        ],
        "logic": template_1_logic
    },
]

calendar_events = pd.read_csv("data/processed/calendar_events.csv", dtype=str)
dates = list(calendar_events["event_start"].str.split(" ").str[0].unique())
times = list(calendar_events["event_start"].str.split(" ").str[1].unique())
events = list(calendar_events["event_name"].unique())
emails = list(calendar_events["participant_email"].unique())
event_ids = list(calendar_events["event_id"].unique())
names = [email.split(".")[0] for email in emails]

# Generate a limited number of unique single-action questions and answers
generated_questions_and_answers = []
max_questions_per_template = 10  # Limit the number of questions per template

if __name__ == "__main__":
    generated_questions_and_answers = generate_all_questions_and_answers(SINGLE_ACTION_TEMPLATES, max_questions_per_template)
    df = pd.DataFrame(generated_questions_and_answers)
    df.to_csv(
        "data/processed/calendar_questions_and_answers_single_action.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )

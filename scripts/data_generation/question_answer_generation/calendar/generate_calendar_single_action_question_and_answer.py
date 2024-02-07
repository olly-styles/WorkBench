import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.data_generation_utils import (
    generate_end_time,
    generate_event_duration_minutes,
    format_event_duration,
    get_natural_language_time,
    get_natural_language_date,
)

random.seed(42)

SINGLE_ACTION_TEMPLATES = [
    {
        "question": "How many events are there on {natural_language_date} with {name}?",
        "answer": """calendar.search_events({{'query': '{name}', 'time_min': '{date} 00:00:00', 'time_max': '{date} 23:59:59'}})""",
    },
    {
        "question": "Create a {duration} event called {event_name} on {natural_language_date} at {time} with {email}",
        "answer": """calendar.create_event({{'event_name': '{event_name}', 'participant_email': '{email}', 'event_start': '{date} {time}', 'duration': '{duration_minutes}'}})""",
    },
    {
        "question": "How long is the {event_name} on {natural_language_date}?",
        "answer": """calendar.search_events({{'query': '{event_name}', 'time_min': '{date} 00:00:00', 'time_max': '{date} 23:59:59'}})""",
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

for template in SINGLE_ACTION_TEMPLATES:
    for _ in range(max_questions_per_template):
        date = random.choice(dates)
        natural_language_date = get_natural_language_date(date)
        time = random.choice(times)
        natural_language_time = get_natural_language_time(time)
        duration_minutes = generate_event_duration_minutes()
        duration = format_event_duration(duration_minutes)
        email = random.choice(emails)
        end_time = generate_end_time(f"{date} {time}", duration)
        event_name = random.choice(events)
        name = random.choice(names)

        question = template["question"].format(
            natural_language_date=natural_language_date,
            time=natural_language_time,
            duration=duration,
            event_name=event_name,
            email=email,
            end_time=end_time,
            name=name,
        )
        answer = template["answer"].format(
            date=date,
            time=time,
            name=name,
            duration=duration_minutes,
            event_name=event_name,
            email=email,
            end_time=end_time,
            duration_minutes=duration_minutes,
        )
        questions = [q["question"] for q in generated_questions_and_answers]
        if question not in questions:
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

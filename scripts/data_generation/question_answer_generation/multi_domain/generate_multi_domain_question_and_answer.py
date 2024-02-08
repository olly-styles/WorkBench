import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.data_generation_utils import (
    format_event_duration,
    generate_event_duration_minutes,
    get_natural_language_date,
    get_natural_language_time,
)
from src.tools import calendar

random.seed(42)

emails_data = pd.read_csv("data/processed/emails.csv", dtype=str)
calendar_events = pd.read_csv("data/processed/calendar_events.csv", dtype=str)

MULTI_DOMAIN_ACTION_TEMPLATES = [
    {
        "question": """Find the email from {natural_language_email_date} about '{subject}' and schedule a {natural_language_duration} meeting called '{subject}' at {natural_language_time} with the sender for {natural_language_meeting_date}.""",
        "answer": """calendar.create_event.func(event_name='{subject}', participant_email='{sender}', event_start='{meeting_datetime}', duration='{duration}')""",
    },
    {
        "question": "Find the first event on {natural_language_event_date} and send an email to the participant with the event name as the subject and the body 'Remember to attend this event.'",
        "answer": "email.send_email.func(recipient='{participant}', subject='{event_name}', body='Remember to attend this event.')",
    },
]

generated_questions_and_answers = []
max_questions_per_template = 5


for template in MULTI_DOMAIN_ACTION_TEMPLATES:
    for _ in range(max_questions_per_template):
        # select an index for the email and calendar events
        email_index = random.randint(0, len(emails_data) - 1)
        calendar_index = random.randint(0, len(calendar_events) - 1)

        natural_language_email_date = get_natural_language_date(
            emails_data["sent_date"][email_index].split(" ")[0]
        )
        subject = emails_data["subject"][email_index]
        sender = emails_data["sender"][email_index]
        duration_minutes = generate_event_duration_minutes()
        natural_language_duration = format_event_duration(duration_minutes)
        meeting_datetime = random.choice(calendar_events["event_start"])
        meeting_date = meeting_datetime.split(" ")[0]
        natural_language_meeting_date = get_natural_language_date(meeting_date)
        natural_language_time = get_natural_language_time(
            meeting_datetime.split(" ")[1]
        )

        date = random.choice(calendar_events["event_start"].str.split(" ").str[0])
        first_event_id = calendar.search_events.func(
            time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59"
        )[0]["event_id"]
        natural_language_event_date = get_natural_language_date(date)
        participant = calendar_events.set_index("event_id").loc[
            first_event_id, "participant_email"
        ]
        event_name = calendar_events.set_index("event_id").loc[
            first_event_id, "event_name"
        ]

        question = template["question"].format(
            subject=subject,
            natural_language_email_date=natural_language_email_date,
            natural_language_duration=natural_language_duration,
            natural_language_time=natural_language_time,
            natural_language_meeting_date=natural_language_meeting_date,
            natural_language_event_date=natural_language_event_date,
        )
        answer = template["answer"].format(
            subject=subject,
            sender=sender,
            meeting_datetime=meeting_datetime,
            duration=duration_minutes,
            participant=participant,
            event_name=event_name,
        )

        generated_questions_and_answers.append(
            {"question": question, "answer": answer, "template": template}
        )

for qa in generated_questions_and_answers:
    print(qa["question"])
    print(qa["answer"])
    print()


df = pd.DataFrame(generated_questions_and_answers)
df.to_csv(
    "data/processed/multi_domain_questions_and_answers_multi_action.csv",
    index=False,
    quoting=csv.QUOTE_ALL,
)

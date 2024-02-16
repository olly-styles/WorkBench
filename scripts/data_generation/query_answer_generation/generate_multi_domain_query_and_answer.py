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
    get_random_future_date,
    get_random_future_datetime,
)
from src.tools import calendar
from src.evals.utils import generate_all_queries_and_answers

random.seed(42)

emails_data = pd.read_csv("data/processed/emails.csv", dtype=str)
calendar_events = pd.read_csv("data/processed/calendar_events.csv", dtype=str)
dates = list(calendar_events["event_start"].str.split(" ").str[0].unique())


def find_email_schedule_meeting_sender_logic():
    email_index = random.randint(0, len(emails_data) - 1)
    natural_language_email_date = get_natural_language_date(emails_data["sent_datetime"][email_index].split(" ")[0])
    subject = emails_data["subject"][email_index]
    sender = emails_data["sender/recipient"][email_index]
    duration_minutes = generate_event_duration_minutes()
    natural_language_duration = format_event_duration(duration_minutes)
    meeting_datetime = str(get_random_future_datetime(dates))
    meeting_date = meeting_datetime.split(" ")[0]
    natural_language_meeting_date = get_natural_language_date(meeting_date)
    natural_language_meeting_time = get_natural_language_time(meeting_datetime.split(" ")[1])

    return {
        "natural_language_email_date": natural_language_email_date,
        "subject": subject,
        "sender": sender,
        "natural_language_duration": natural_language_duration,
        "meeting_datetime": meeting_datetime,
        "meeting_date": meeting_date,
        "natural_language_meeting_date": natural_language_meeting_date,
        "natural_language_time": natural_language_meeting_time,
        "duration": duration_minutes,
    }


def find_event_send_email_logic():
    date = get_random_future_date(dates)
    first_event_id = calendar.search_events.func(time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59")[0][
        "event_id"
    ]
    natural_language_event_date = get_natural_language_date(date)
    participant = calendar_events.set_index("event_id").loc[first_event_id, "participant_email"]
    event_name = calendar_events.set_index("event_id").loc[first_event_id, "event_name"]
    return {
        "natural_language_event_date": natural_language_event_date,
        "participant": participant,
        "event_name": event_name,
    }


MULTI_DOMAIN_TEMPLATES = [
    {
        "query": """Find the email from {natural_language_email_date} about '{subject}' and schedule a {natural_language_duration} meeting called '{subject}' at {natural_language_time} with the sender for {natural_language_meeting_date}.""",
        "answer": [
            """calendar.create_event.func(event_name='{subject}', participant_email='{sender}', event_start='{meeting_datetime}', duration='{duration}')"""
        ],
        "logic": find_email_schedule_meeting_sender_logic,
    },
    {
        "query": "Find the first event on {natural_language_event_date} and send an email to the participant with the event name as the subject and the body 'Remember to attend this event.'",
        "answer": [
            """email.send_email.func(recipient='{participant}', subject='{event_name}', body='Remember to attend this event.')"""
        ],
        "logic": find_event_send_email_logic,
    },
]

max_queries_per_template = 5
if __name__ == "__main__":
    generated_queries_and_answers = generate_all_queries_and_answers(
        MULTI_DOMAIN_TEMPLATES, max_queries_per_template
    )
    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/multi_domain_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )

import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.data_generation_utils import (
    HARDCODED_CURRENT_TIME,
    format_event_duration,
    generate_event_duration_minutes,
    get_natural_language_date,
    get_natural_language_time,
    get_random_future_date,
    get_random_future_datetime,
)
from src.tools import calendar
from src.evals.utils import generate_all_queries_and_answers
from scripts.data_generation.query_answer_generation.generate_calendar_query_and_answer import (
    create_event_on_first_free_slot_tomorrow,
)

random.seed(42)

emails_data = pd.read_csv("data/processed/emails.csv", dtype=str)
calendar_events = pd.read_csv("data/processed/calendar_events.csv", dtype=str)
dates = list(calendar_events["event_start"].str.split(" ").str[0].unique())
times = list(calendar_events["event_start"].str.split(" ").str[1].unique())
project_tasks = pd.read_csv("data/processed/project_tasks.csv", dtype=str)


def get_base_email_dict():
    email_index = random.randint(0, len(emails_data) - 1)
    natural_language_email_date = get_natural_language_date(emails_data["sent_datetime"][email_index].split(" ")[0])
    subject = emails_data["subject"][email_index]
    sender = emails_data["sender/recipient"][email_index]
    return {
        "natural_language_email_date": natural_language_email_date,
        "subject": subject,
        "sender": sender,
        "sender_name": sender.split(".")[0],
    }


def get_base_event_dict():
    duration_minutes = generate_event_duration_minutes()
    natural_language_duration = format_event_duration(duration_minutes)
    event_datetime = str(get_random_future_datetime(dates))
    event_date = event_datetime.split(" ")[0]
    natural_language_event_date = get_natural_language_date(event_date)
    event_time = event_datetime.split(" ")[1]
    natural_language_event_time = get_natural_language_time(event_time)
    return {
        "natural_language_duration": natural_language_duration,
        "event_datetime": event_datetime,
        "event_date": event_date,
        "natural_language_event_date": natural_language_event_date,
        "event_time": event_time,
        "natural_language_time": natural_language_event_time,
        "duration": duration_minutes,
    }

def new_event_string(event_name, email, event_datetime, duration):
    return f"""calendar.create_event.func(event_name="{event_name}", participant_email="{email}", event_start="{event_datetime}", duration="{duration}")"""


def new_email_string(email, subject, body):
    return f"""email.send_email.func(recipient="{email}", subject="{subject}", body="{body}")"""


def get_first_event_id_on_date(date):
    return calendar.search_events.func(time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59")[0]["event_id"]


def find_email_schedule_event_sender_logic():
    email_dict = get_base_email_dict()
    event_dict = get_base_event_dict()
    answer = [new_event_string(email_dict["subject"], email_dict["sender"], event_dict["event_datetime"], event_dict["duration"])]
    return {**email_dict, **event_dict, "answer": answer}


def find_event_send_email_logic():
    event_dict = get_base_event_dict()
    first_event_id = get_first_event_id_on_date(event_dict["event_date"])
    event_dict["participant"] = calendar_events.set_index("event_id").loc[first_event_id, "participant_email"]
    event_dict["event_name"] = calendar_events.set_index("event_id").loc[first_event_id, "event_name"]
    answer = [new_email_string(event_dict["participant"], event_dict["event_name"], "Remember to attend this event.")]
    return {**event_dict, "answer": answer}


def schedule_event_if_no_emails_logic():
    """If {sender_name} hasn't sent me any emails in the past {days} days, schedule a 30 minute meeting with them for {day_of_week} at {natural_language_time} called 'Catch up with {sender_name}'""",
    email_dict = get_base_email_dict()
    event_dict = get_base_event_dict()
    days_since_email = random.randint(2, 4)
    dates_up_to_6_days_in_the_future = [str(HARDCODED_CURRENT_TIME.date() + pd.Timedelta(days=i)) for i in range(1, 7)]
    no_weekend_dates = [date for date in dates_up_to_6_days_in_the_future if pd.to_datetime(date).dayofweek < 5]
    event_dict["event_date"] = random.choice(no_weekend_dates)
    event_datetime = f"{event_dict['event_date']} {event_dict['event_time']}"
    day_of_week = pd.to_datetime(event_dict["event_date"]).day_name()
    answer = []
    if emails_data[
        (emails_data["sender/recipient"] == email_dict["sender"])
        & (emails_data["sent_datetime"] > str(HARDCODED_CURRENT_TIME - pd.Timedelta(days=days_since_email)))
    ].empty:
        answer.append(new_event_string(f"Catch up with {email_dict['sender_name']}", email_dict["sender"], event_datetime, event_dict["duration"]))

    return {**email_dict, **event_dict, "days": days_since_email, "answer": answer, "day_of_week": day_of_week}


def send_email_if_no_past_meetings_logic():
    """If I haven't met with {name} in the past {days} days, send them an email titled 'Catch up soon?' saying 'We haven't caught up in a while - can you send some availability over next week?'"""
    email = random.choice(calendar_events["participant_email"].unique())
    name = email.split(".")[0]
    threshold_days_since_last_meeting = random.randint(2, 4)
    last_event_date = (
        calendar_events[
            (calendar_events["participant_email"] == email)
            & (calendar_events["event_start"] < str(HARDCODED_CURRENT_TIME))
        ]
        .sort_values("event_start", ascending=False)
        .iloc[0]["event_start"]
        .split(" ")[0]
    )
    threshold_date = str((HARDCODED_CURRENT_TIME - pd.Timedelta(days=threshold_days_since_last_meeting)).date())

    answer = []
    if last_event_date < threshold_date:
        answer.append(new_email_string(email, "Catch up soon?", f"We haven't caught up in a while - can you send some availability over next week?"))
    return {
        "name": name,
        "days": threshold_days_since_last_meeting,
        "last_event_date": last_event_date,
        "answer": answer,
    }


def send_email_if_no_future_meetings_logic():
    """If I don't have any meetings scheduled with {name} in the next {days} days, send them an email titled 'Catch up soon?' saying 'We have not caught up in a while - can you send some availability over next week?'""",
    email = random.choice(calendar_events["participant_email"].unique())
    threshold_days_until_next_meeting = random.randint(2, 4)
    next_event_date = (
        calendar_events[
            (calendar_events["participant_email"] == email)
            & (calendar_events["event_start"] > str(HARDCODED_CURRENT_TIME))
        ]
        .sort_values("event_start", ascending=True)
        .iloc[0]["event_start"]
        .split(" ")[0]
    )
    threshold_date = str((HARDCODED_CURRENT_TIME + pd.Timedelta(days=threshold_days_until_next_meeting)).date())
    answer = []
    if next_event_date > threshold_date:
        answer.append(new_email_string(email, "Catch up soon?", "We have not caught up in a while - can you send some availability over next week?"))
    return {
        "email": email,
        "days": threshold_days_until_next_meeting,
        "next_event_date": next_event_date,
        "answer": answer,
    }


def send_email_for_overdue_tasks_logic():
    """If {name} has any overdue tasks, send them an email titled 'Overdue tasks' saying 'You have a few overdue tasks - can you update me on them?'.
    Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"""
    email = random.choice(emails_data["sender/recipient"].unique())
    name = email.split(".")[0]
    overdue_tasks = project_tasks[
        (project_tasks["assigned_to_email"] == email) & (project_tasks["due_date"] < str(HARDCODED_CURRENT_TIME.date()))
    ]
    if len(overdue_tasks):
        answer = [(new_email_string(email, "Overdue tasks", "You have a few overdue tasks - can you update me on them?"))]
    else:
        answer = [(new_email_string(email, "Good work this sprint", "Nice work keeping on top of your tasks this sprint!"))]
    return {
        "email": email,
        "name": name,
        "overdue_tasks": overdue_tasks,
        "answer": answer,
    }


def overdue_tasks_base_dict():
    email = random.choice(emails_data["sender/recipient"].unique())
    name = email.split(".")[0]
    overdue_tasks = project_tasks[
        (project_tasks["assigned_to_email"] == email) & (project_tasks["due_date"] < str(HARDCODED_CURRENT_TIME.date()))
    ]
    return {"email": email, "name": name, "overdue_tasks": overdue_tasks}


def book_event_send_email_if_overdue_tasks_logic():
    """If {name} has any overdue tasks, book a half hour meeting with them called 'Catch up on overdue tasks' at the earliest time I'm free tomorrow and
    send them an email titled 'Discuss overdue tasks' saying 'I noticed you have a few overdue tasks - lets catch up tomorrow.
    Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"""
    base_dict = overdue_tasks_base_dict()
    answer = []
    if len(base_dict["overdue_tasks"]):
        event_name = "Catch up on overdue tasks"
        create_event_action = create_event_on_first_free_slot_tomorrow(event_name, base_dict["email"], 30)
        email_action = new_email_string(base_dict["email"], "Discuss overdue tasks", "I noticed you have a few overdue tasks - let's catch up tomorrow.")
        answer = [create_event_action, email_action]
    else:
        answer = [new_email_string(base_dict["email"], "Good work this sprint", "Nice work keeping on top of your tasks this sprint!")]
    return {**base_dict, "answer": answer}


MULTI_DOMAIN_TEMPLATES = [
    {
        "query": """Find the email from {natural_language_email_date} about {subject} and schedule a {natural_language_duration} meeting called '{subject}' at {natural_language_time} with the sender for {natural_language_event_date}.""",
        "logic": find_email_schedule_event_sender_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """Send an email to attendees of the first event on {natural_language_event_date}. Title it with the event name and tell them 'Remember to attend this event.'""",
        "logic": find_event_send_email_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """If {sender_name} hasn't sent me any emails in the past {days} days, schedule a 30 minute meeting with them for {day_of_week} at {natural_language_time} called 'Catch up with {sender_name}'""",
        "logic": schedule_event_if_no_emails_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """If I haven't met with {name} in the past {days} days, send them an email titled 'Catch up soon?' saying 'We haven't caught up in a while - can you send some availability over next week?'""",
        "logic": send_email_if_no_past_meetings_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """If I don't have any meetings scheduled with {email} in the next {days} days, send them an email titled 'Catch up soon?' saying 'We have not caught up in a while - can you send some availability over next week?'""",
        "logic": send_email_if_no_future_meetings_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": (
            "If {name} has any overdue tasks, send them an email titled 'Overdue tasks' saying 'You have a few overdue tasks - can you update me on them?'. "
            "Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
        ),
        "logic": send_email_for_overdue_tasks_logic,
        "domains": ["email", "project_management"],
    },
    # 3 domain
    {
        "query": (
            "If {name} has any overdue tasks, book a half hour meeting with them called 'Catch up on overdue tasks' at the earliest time I'm free tomorrow and "
            "send them an email titled 'Discuss overdue tasks' saying 'I noticed you have a few overdue tasks - let's catch up tomorrow.' "
            "Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
        ),
        "logic": book_event_send_email_if_overdue_tasks_logic,
        "domains": ["email", "calendar", "project_management"],
    },
]

max_queries_per_template = 3
if __name__ == "__main__":
    generated_queries_and_answers = generate_all_queries_and_answers(MULTI_DOMAIN_TEMPLATES, max_queries_per_template)
    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/multi_domain_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )

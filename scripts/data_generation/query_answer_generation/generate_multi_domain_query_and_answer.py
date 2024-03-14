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
from scripts.data_generation.query_answer_generation.generate_analytics_query_and_answer import get_metric_fell_vs_grew
from scripts.data_generation.query_answer_generation.generate_project_management_query_and_answer import (
    get_random_task_dict,
    get_new_task_string,
)
from scripts.data_generation.query_answer_generation.generate_calendar_query_and_answer import (
    create_event_on_first_free_slot_tomorrow,
)

random.seed(42)

emails_data = pd.read_csv("data/processed/emails.csv", dtype=str)
calendar_events = pd.read_csv("data/processed/calendar_events.csv", dtype=str)
dates = list(calendar_events["event_start"].str.split(" ").str[0].unique())
times = list(calendar_events["event_start"].str.split(" ").str[1].unique())
project_tasks = pd.read_csv("data/processed/project_tasks.csv", dtype=str)


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
    answer = [
        f"""calendar.create_event.func(event_name="{subject}", participant_email="{sender}", event_start="{meeting_datetime}", duration="{duration_minutes}")"""
    ]
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
        "answer": answer,
    }


def find_event_send_email_logic():
    date = get_random_future_date(dates)
    first_event_id = calendar.search_events.func(time_min=f"{date} 00:00:00", time_max=f"{date} 23:59:59")[0][
        "event_id"
    ]
    natural_language_event_date = get_natural_language_date(date)
    participant = calendar_events.set_index("event_id").loc[first_event_id, "participant_email"]
    event_name = calendar_events.set_index("event_id").loc[first_event_id, "event_name"]
    answer = [
        f"""email.send_email.func(recipient="{participant}", subject="{event_name}", body="Remember to attend this event.")"""
    ]
    return {
        "natural_language_event_date": natural_language_event_date,
        "participant": participant,
        "event_name": event_name,
        "answer": answer,
    }


def get_metric_fell_create_task_logic():
    fell_vs_grew = get_metric_fell_vs_grew()
    new_task_dict = get_random_task_dict()
    new_task_dict["task_name"] = f"Improve {fell_vs_grew['natural_language_metric']}"
    if fell_vs_grew["fell_vs_grew"] == "fell":
        answer = [
            get_new_task_string(
                new_task_dict["task_name"], new_task_dict["email"], new_task_dict["board"], new_task_dict["due_date"]
            )
        ]
    else:
        answer = []
    return {**fell_vs_grew, **new_task_dict, "answer": answer}


def get_metric_fell_create_task_book_meeting_logic():
    create_task_dict = get_metric_fell_create_task_logic()
    event_name = f"Catch up on {create_task_dict['natural_language_metric']}"
    create_event_action = create_event_on_first_free_slot_tomorrow(event_name, create_task_dict["email"], 30)

    if create_task_dict["answer"] == []:
        answer = []
    else:
        answer = create_task_dict["answer"] + [create_event_action]
    return {**create_task_dict, "answer": answer}


def get_metric_fell_create_task_book_meeting_send_email_logic():
    create_task_book_meeting_dict = get_metric_fell_create_task_book_meeting_logic()
    if create_task_book_meeting_dict["answer"] == []:
        answer = []
    else:
        subject = f"Discuss {create_task_book_meeting_dict['natural_language_metric']}"
        body = f"I need you to look at {create_task_book_meeting_dict['natural_language_metric']} - more details on the task I just made."
        email_action = f"""email.send_email.func(recipient="{create_task_book_meeting_dict["email"]}", subject="{subject}", body="{body}")"""
        answer = create_task_book_meeting_dict["answer"] + [email_action]
    return {**create_task_book_meeting_dict, "answer": answer}


def schedule_meeting_if_no_emails_logic():
    email = random.choice(emails_data["sender/recipient"])
    name = email.split(".")[0]
    days_since_email = random.randint(2, 4)
    dates_up_to_6_days_in_the_future = [str(HARDCODED_CURRENT_TIME.date() + pd.Timedelta(days=i)) for i in range(1, 7)]
    meeting_date = random.choice(dates_up_to_6_days_in_the_future)

    # while this date is a weekend, pick another date
    while pd.to_datetime(meeting_date).dayofweek >= 5:
        meeting_date = random.choice(dates_up_to_6_days_in_the_future)
    time = random.choice(times)
    natural_language_time = get_natural_language_time(time)

    answer = []
    if emails_data[
        (emails_data["sender/recipient"] == email)
        & (emails_data["sent_datetime"] > str(HARDCODED_CURRENT_TIME - pd.Timedelta(days=days_since_email)))
    ].empty:
        answer.append(
            f"""calendar.create_event.func(event_name="Catch up with {name}", participant_email="{email}", event_start="{meeting_date} {time}", duration="30")"""
        )

    return {
        "name": name,
        "days": days_since_email,
        "day_of_week": pd.to_datetime(meeting_date).day_name(),
        "natural_language_time": natural_language_time,
        "answer": answer,
    }


def send_email_if_no_past_meetings_logic():
    """If I haven't met with {name} in the past {days} days, send them an email titled 'Catch up soon?' saying 'We haven't caught up since {last_meeting_date} - can you send some availability over next week?'"""
    email = random.choice(calendar_events["participant_email"].unique())
    name = email.split(".")[0]
    threshold_days_since_last_meeting = random.randint(2, 4)
    last_meeting_date = (
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
    if last_meeting_date < threshold_date:
        subject = "Catch up soon?"
        body = f"We have not caught up in over {threshold_days_since_last_meeting} days - can you send some availability over next week?"
        answer.append(f"""email.send_email.func(recipient="{email}", subject="{subject}", body="{body}")""")
    return {
        "name": name,
        "days": threshold_days_since_last_meeting,
        "last_meeting_date": last_meeting_date,
        "answer": answer,
    }


def send_email_if_no_future_meetings_logic():
    """If I don't have any meetings scheduled with {name} in the next {days} days, send them an email titled 'Catch up soon?' saying 'We have not caught up in a while - can you send some availability over next week?'""",
    email = random.choice(calendar_events["participant_email"].unique())
    name = email.split(".")[0]
    threshold_days_until_next_meeting = random.randint(2, 4)
    next_meeting_date = (
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
    if next_meeting_date > threshold_date:
        subject = "Catch up soon?"
        body = f"We have not caught up in a while - can you send some availability over next week?"
        answer.append(f"""email.send_email.func(recipient="{email}", subject="{subject}", body="{body}")""")
    return {
        "email": email,
        "days": threshold_days_until_next_meeting,
        "next_meeting_date": next_meeting_date,
        "answer": answer,
        "name": name,
    }


def send_email_for_overdue_tasks_logic():
    """If {name} has any overdue tasks, send them an email titled 'Overdue tasks' saying 'You have a few overdue tasks - can you update me on them?'.
    Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"""
    email = random.choice(emails_data["sender/recipient"].unique())
    name = email.split(".")[0]
    overdue_tasks = project_tasks[
        (project_tasks["assigned_to_email"] == email) & (project_tasks["due_date"] < str(HARDCODED_CURRENT_TIME.date()))
    ]
    answer = []
    if len(overdue_tasks):
        subject = "Overdue tasks"
        body = "You have a few overdue tasks - can you update me on them?"
        answer.append(f"""email.send_email.func(recipient="{email}", subject="{subject}", body="{body}")""")
    else:
        subject = "Good work this sprint"
        body = "Nice work keeping on top of your tasks this sprint!"
        answer.append(f"""email.send_email.func(recipient="{email}", subject="{subject}", body="{body}")""")
    return {
        "email": email,
        "name": name,
        "overdue_tasks": overdue_tasks,
        "answer": answer,
    }


def book_meeting_send_email_if_overdue_tasks_logic():
    """If {name} has any overdue tasks, book a half hour meeting with them called 'Catch up on overdue tasks' at the earliest time I'm free tomorrow and
    send them an email titled 'Discuss overdue tasks' saying 'I noticed you have a few overdue tasks - lets catch up tomorrow.
    Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"""
    email = random.choice(emails_data["sender/recipient"].unique())
    name = email.split(".")[0]
    overdue_tasks = project_tasks[
        (project_tasks["assigned_to_email"] == email) & (project_tasks["due_date"] < str(HARDCODED_CURRENT_TIME.date()))
    ]
    answer = []
    if len(overdue_tasks):
        event_name = "Catch up on overdue tasks"
        create_event_action = create_event_on_first_free_slot_tomorrow(event_name, email, 30)
        subject = "Discuss overdue tasks"
        body = "I noticed you have a few overdue tasks - let's catch up tomorrow."
        email_action = f"""email.send_email.func(recipient="{email}", subject="{subject}", body="{body}")"""
        answer.append(create_event_action)
        answer.append(email_action)
    else:
        subject = "Good work this sprint"
        body = "Nice work keeping on top of your tasks this sprint!"
        answer.append(f"""email.send_email.func(recipient="{email}", subject="{subject}", body="{body}")""")
    return {
        "email": email,
        "name": name,
        "overdue_tasks": overdue_tasks,
        "answer": answer,
    }


MULTI_DOMAIN_TEMPLATES = [
    {
        "query": """Find the email from {natural_language_email_date} about '{subject}' and schedule a {natural_language_duration} meeting called '{subject}' at {natural_language_time} with the sender for {natural_language_meeting_date}.""",
        "alternative_queries": [
            "I need to schedule a meeting called '{subject}' at {natural_language_time} for {natural_language_meeting_date}. It's with the sender of the email from {natural_language_email_date} about '{subject}'. Can you do that?",
            "Can you find the email from {natural_language_email_date} about '{subject}' and schedule a {natural_language_duration} meeting called '{subject}' at {natural_language_time} with the sender for {natural_language_meeting_date}?",
        ],
        "logic": find_email_schedule_meeting_sender_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """Send an email to attendees of the first event on {natural_language_event_date}. Title it with the event name and tell them 'Remember to attend this event.'""",
        "alternative_queries": [
            "Can you send an email to attendees of the first event on {natural_language_event_date}? Title it with the event name and tell them 'Remember to attend this event.'",
            "I need to make sure everyone remembers to attend the first event on {natural_language_event_date}. Can you send an email to the attendees with the event name as the title and 'Remember to attend this event.' in the email?",
        ],
        "logic": find_event_send_email_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """If {name} hasn't sent me any emails in the past {days} days, schedule a 30 minute meeting with them for {day_of_week} at {natural_language_time} called 'Catch up with {name}'""",
        "alternative_queries": [
            "I can't remember the last time I heard from {name}. Can you check if they've sent me any emails in the past {days} days? If not, schedule a 30 minute meeting with them for {day_of_week} at {natural_language_time} called 'Catch up with {name}'",
            "if {name} hasn't sent me any emails in the past {days} days, schedule a half hour meeting with them for {day_of_week} at {natural_language_time} and call it 'Catch up with {name}'",
        ],
        "logic": schedule_meeting_if_no_emails_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """If I haven't met with {name} in the past {days} days, send them an email titled 'Catch up soon?' saying 'We have not caught up in over {days} days - can you send some availability over next week?'""",
        "alternative_queries": [
            "can't remember the last time I met with {name}. Can you check if it's been over {days} days? If so, send them an email titled 'Catch up soon?' saying 'We have not caught up in over {days} days - can you send some availability over next week?'",
            "I haven't met with {name} in a while. if it's been longer than {days} days can you send them an email titled 'Catch up soon?' saying 'We have not caught up in over {days} days - can you send some availability over next week?'",
        ],
        "logic": send_email_if_no_past_meetings_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": """If I don't have any meetings scheduled with {name} in the next {days} days, send them an email titled 'Catch up soon?' saying 'We have not caught up in a while - can you send some availability over next week?'""",
        "alternative_queries": [
            "Did I already schedule a meeting with {name} in the next {days} days? If not, send them an email titled 'Catch up soon?' saying 'We have not caught up in a while - can you send some availability over next week?'",
            "I need to check if I have any meetings scheduled with {name} in the next {days} days. If not, send them an email titled 'Catch up soon?' saying 'We have not caught up in a while - can you send some availability over next week?'",
        ],
        "logic": send_email_if_no_future_meetings_logic,
        "domains": ["email", "calendar"],
    },
    {
        "query": (
            "If {name} has any overdue tasks, send them an email titled 'Overdue tasks' saying 'You have a few overdue tasks - can you update me on them?'. "
            "Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
        ),
        "alternative_queries": [
            (
                "can you check if {name} has any overdue tasks? If so, send them an email titled 'Overdue tasks' saying 'You have a few overdue tasks"
                "- can you update me on them?'. Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
            ),
            (
                "I think {name} might have some overdue tasks. Can you check and if so, send them an email titled 'Overdue tasks' saying 'You have a few overdue "
                "tasks - can you update me on them?'. Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
            ),
        ],
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
        "alternative_queries": [
            (
                "can you check if {name} has any overdue tasks? If so, book a 30 minute meeting with them called 'Catch up on overdue tasks' at the earliest time "
                "I'm free tomorrow and send them an email titled 'Discuss overdue tasks' saying 'I noticed you have a few overdue tasks - let's catch up tomorrow.' "
                "Otherwise send them an email saying 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
            ),
            (
                "I think {name} might have some overdue tasks. Can you check and if so, book a half hour meeting with them called 'Catch up on overdue tasks' at the "
                "earliest time I'm free tomorrow and send them an email titled 'Discuss overdue tasks' saying 'I noticed you have a few overdue tasks - let's catch up "
                "tomorrow.' Otherwise email them with 'Nice work keeping on top of your tasks this sprint!' titled 'Good work this sprint'"
            ),
        ],
        "logic": book_meeting_send_email_if_overdue_tasks_logic,
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

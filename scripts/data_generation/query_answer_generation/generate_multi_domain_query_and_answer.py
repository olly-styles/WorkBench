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
        f"""calendar.create_event.func(event_name='{subject}', participant_email='{sender}', event_start='{meeting_datetime}', duration='{duration_minutes}')"""
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
        f"""email.send_email.func(recipient='{participant}', subject='{event_name}', body='Remember to attend this event.')"""
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
                new_task_dict["task_name"], new_task_dict["name"], new_task_dict["board"], new_task_dict["due_date"]
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
        email_action = f"""email.send_email.func(recipient='{create_task_book_meeting_dict['email']}', subject='{subject}', body='{body}"""
        answer = create_task_book_meeting_dict["answer"] + [email_action]
    return {**create_task_book_meeting_dict, "answer": answer}


MULTI_DOMAIN_TEMPLATES = [
    {
        "query": """Find the email from {natural_language_email_date} about '{subject}' and schedule a {natural_language_duration} meeting called '{subject}' at {natural_language_time} with the sender for {natural_language_meeting_date}.""",
        "logic": find_email_schedule_meeting_sender_logic,
    },
    {
        "query": """Send an email to attendees of the first event on {natural_language_event_date}. Title it with the event name and tell them 'Remember to attend this event.'""",
        "logic": find_event_send_email_logic,
    },
    {
        "query": """If {name} hasn't sent me any emails in the past {days} days, schedule a {duration} meeting with them for {day_of_week} at {natural_language_time}.""",
    },
    {
        "query": """If I haven't met with {name} in the past {days} days, send them an email titled 'Catch up soon?' saying 'We haven't caught up since {last_meeting_date} - can you send some availability over next week?'""",
    },
    {
        "query": """If I don't have any meetings scheduled with {name} in the next {days} days, send them an email titled 'Catch up soon?' saying 'We haven't caught up since {last_meeting_date} - can you send some availability over next week?'""",
    },
    {
        "query": """If my next meeting with {name} is more than {days} days away, send them an email titled 'Can we meet sooner?' saying 'We're not meeting until {next_meeting_date} - can we meet sooner?'""",
    },
    {
        "query": """Send an email to {name} titled '{natural_language_metric}' and tell them 'There were {number} {natural_language_metric} on {natural_language_date}'""",
    },
    {
        "query": """If {natural_language_metric} {fell_or_grew} since {date_min}, 
        make a task for {name} called 'Improve {natural_language_metric}'. It's due in a week.""",
    },
    {
        "query": """If {name} has any overdue tasks, send them an email titled 'Overdue tasks' saying 'You have {number} overdue tasks - can you update me on them?'.
        Otherwise email them with 'Nice work keeping on top of your tasks this sprint - {number_of_tasks} is a lot!' titled 'Good work this sprint'""",
    },
    {
        "query": """Find the correlation between {natural_language_metric_1} and {natural_language_metric_2},
        then send an email to {name} titled '{natural_language_metric_1} and {natural_language_metric_2}'.
        If there's a positive correlation, tell them 'Their correlation is {correlation}. We should discuss.'
        Otherwise, tell them 'They're unrelated, no need to discuss.'""",
    },
    {
        "query": """If {natural_language_metric} was {more_or_less} than {threshold} at any time between {date_min} and {date_max}, 
        book a meeting with {name} for {day_of_week} at {natural_language_time} titled 'Discuss {natural_language_metric}'""",
    },
    {
        "query": """If {natural_language_metric} {fell_or_grew} by more than {threshold} from {date_min} to {date_max},
        book a meeting with {name} for {day_of_week} at {natural_language_time} titled 'Discuss {natural_language_metric}'""",
    },
    {
        "query": """If there's a {positive_or_negative} correlation between {natural_language_metric_1} and {natural_language_metric_2} since {date_min},
        book a meeting with {name} for {day_of_week} at {natural_language_time} titled 'Discuss {natural_language_metric_1} and {natural_language_metric_2}'""",
    },
    {
        "query": """If {natural_language_metric} {fell_or_grew} since {date_min},
        email {name} saying 'I noticed {natural_language_metric} {fell_or_grew} recently - can we discuss?'
        and title it  'Discuss {natural_language_metric}'""",
    },
    {
        "query": """If {natural_language_metric} fell since {date_min}, make a task for {name} called 'Improve {natural_language_metric}', which is due in a week.""",
        "logic": get_metric_fell_create_task_logic,
    },
    {
        "query": """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {date_min}, 
        email {name} saying 'I noticed {natural_language_metric} was {more_or_less} than {threshold} recently - can we discuss?' 
        and title it 'Discuss {natural_language_metric}'""",
    },
    {  # examples of 3-domain query
        "query": """If {netural_language_metric} {fell_or_grew} since {date_min},
        email {name} saying 'We'r e not doing well on {natural_language_metric} recently - can we discuss?'
        and title it 'Discuss {natural_language_metric}'. 
        then also book a meeting with them called 'Catch up on {natural_language_metric}' at the earliest time I'm free tomorrow""",
    },
    {
        "query": """If {natural_language_metric} fell since {natural_language_date}, make a {board} backlog task for {name} called 'Improve {natural_language_metric}', which is due in a week, and then book a meeting with them called 'Catch up on {natural_language_metric}' for the earliest time I'm free tomorrow.""",
        "logic": get_metric_fell_create_task_book_meeting_logic,
    },
    {
        "query": """If {name} has any overdue tasks, book a meeting with them called 'Catch up on overdue tasks' at the earliest time I'm free tomorrow.
        Otherwise email them with 'Nice work keeping on top of your tasks this sprint - {number_of_tasks} is a lot!' titled 'Good work this sprint'""",
    },
    {
        "query": """If {natural_language_metric} was {more_or_less} than {threshold} at any time since {date_min},
        email {name} saying 'We're not doing well on {natural_language_metric} recently - can we discuss?'
        and title it 'Discuss {natural_language_metric}', 
        and also book a meeting with them called 'Catch up on {natural_language_metric}' at the earliest time I'm free {day_of_week}.
        Otherwise, email {name} saying 'I just checked {natural_language_metric} since {date_min} and they're doing great - nice work!' 
        Title it 'Nice work on {natural_language_metric}'""",
    },
    # examples of 4-domain query
    {
        "query": """If {natural_language_metric} fell since {natural_language_date}, \
make a task for {name} called 'Improve {natural_language_metric}', which is due in a week. \
Also send them an email saying 'I need you to look at {natural_language_metric} - more details on the task I just made.' \
and title it 'Discuss {natural_language_metric}'. \
then also book a 30-minute meeting with them called 'Catch up on {natural_language_metric}' at the earliest time I'm free tomorrow""",
        "logic": get_metric_fell_create_task_book_meeting_send_email_logic,
    },
    {
        "query": """If {natural_language_metric} was {more_or_less} than {threshold} on {natural_language_date},
        take the person with the fewest backlog tasks on {board} and book a meeting with them
        called 'Discuss {natural_language_metric}' at the earliest time I'm free tomorrow.
        Then also make a task for them called 'Improve {natural_language_metric}' on {board}, which is due in a week.
        Otherwise, email {name} saying 'I just checked {natural_language_metric} and you're doing doing great - nice work!' 
        Title it 'Nice work on {natural_language_metric}'
        """,
    },
]

max_queries_per_template = 1
if __name__ == "__main__":
    MULTI_DOMAIN_TEMPLATES = [t for t in MULTI_DOMAIN_TEMPLATES if "logic" in t.keys()]
    generated_queries_and_answers = generate_all_queries_and_answers(MULTI_DOMAIN_TEMPLATES, max_queries_per_template)
    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/multi_domain_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )

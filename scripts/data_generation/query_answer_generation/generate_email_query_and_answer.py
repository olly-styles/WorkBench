import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.data_generation_utils import get_natural_language_date
from src.tools import email
from src.evals.utils import generate_all_queries_and_answers

random.seed(42)


emails_data = pd.read_csv("data/processed/emails.csv", dtype=str)
email_ids = list(emails_data["email_id"].unique())
subjects = list(emails_data["subject"].unique())
senders = list(emails_data["sender/recipient"].unique())
dates = list(emails_data["sent_datetime"].str.split(" ").str[0].unique())
bodies = list(emails_data["body"].unique())
datetimes = list(emails_data["sent_datetime"].str.split(" ").str[0].unique())


def delete_first_email_logic():
    date = random.choice(dates)
    natural_language_date = get_natural_language_date(date)
    first_email_id = email.search_emails.func(date_min=date, date_max=date)[0][
        "email_id"
    ]
    return {
        "natural_language_date": natural_language_date,
        "first_email_id": first_email_id,
    }


def send_email_to_last_sender_logic():
    date = random.choice(dates)
    natural_language_date = get_natural_language_date(date)
    index = random.randint(0, len(subjects) - 1)
    body = bodies[index]
    subject = subjects[index]
    last_email_sender = email.search_emails.func(
        date_min=f"{date}", date_max=f"{date}"
    )[-1]["sender/recipient"]
    return {
        "natural_language_date": natural_language_date,
        "subject": subject,
        "body": body,
        "last_email_sender": last_email_sender,
    }


def forward_email_logic():
    date = random.choice(dates)
    natural_language_date = get_natural_language_date(date)
    last_email_id = email.search_emails.func(date_min=f"{date}", date_max=f"{date}")[
        -1
    ]["email_id"]
    recipient = random.choice(senders)
    return {
        "natural_language_date": natural_language_date,
        "last_email_id": last_email_id,
        "recipient": recipient,
    }


def send_email_logic():
    # get a random index from the list of subjects
    index = random.randint(0, len(subjects) - 1)
    body = bodies[index]
    subject = subjects[index]
    name = senders[index].split("@")[0].split(".")[0]
    recipient = random.choice(senders)
    query = random.choice(subjects)
    datetime = random.choice(datetimes)
    date = datetime.split(" ")[0]
    natural_language_date = get_natural_language_date(date)
    return {
        "body": body,
        "subject": subject,
        "name": name,
        "recipient": recipient,
        "query": query,
        "date": date,
        "natural_language_date": natural_language_date,
    }


MULTI_ACTION_EMAIL_TEMPLATES = [
    {
        "query": "Delete the first email on {natural_language_date}",
        "answer": ["""email.delete_email.func(email_id='{first_email_id}')"""],
        "logic": delete_first_email_logic,
    },
    {
        "query": "Find the last email on {natural_language_date} and send an email to the sender with the subject '{subject}' and body '{body}'",
        "answer": [
            """email.send_email.func(recipient='{last_email_sender}', subject='{subject}', body='{body}')"""
        ],
        "logic": send_email_to_last_sender_logic,
    },
    {
        "query": "Find the last email on {natural_language_date} and forward it to {recipient}",
        "answer": [
            """email.forward_email.func(email_id='{last_email_id}', recipient='{recipient}')"""
        ],
        "logic": forward_email_logic,
    },
    {
        "query": "Send an email to {recipient} saying '{body}' and title it '{subject}'",
        "answer": [
            """email.send_email.func(recipient='{recipient}', subject='{subject}', body='{body}')"""
        ],
        "logic": send_email_logic,
    },
]

# Generate a limited number of unique multi-action queries and answers
generated_queries_and_answers = []
max_queries_per_template = 3  # Limit the number of queries per template


if __name__ == "__main__":
    generated_queries_and_answers = generate_all_queries_and_answers(
        MULTI_ACTION_EMAIL_TEMPLATES, max_queries_per_template
    )
    df = pd.DataFrame(generated_queries_and_answers)
    df.to_csv(
        "data/processed/queries_and_answers/email_queries_and_answers.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )

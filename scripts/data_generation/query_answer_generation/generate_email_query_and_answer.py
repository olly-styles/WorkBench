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


def delete_last_email_logic():
    sender = random.choice(senders)
    name = sender.split("@")[0].split(".")[0]
    last_email_id = emails_data[emails_data["sender/recipient"] == sender].iloc[-1]["email_id"]
    return {
        "name": name,
        "last_email_id": last_email_id,
    }


def forward_email_logic():
    sender_email = random.choice(senders)
    sender_name = sender_email.split("@")[0].split(".")[0]
    last_email_id = emails_data[emails_data["sender/recipient"] == sender_email].iloc[-1]["email_id"]
    recipient_email = random.choice(senders)
    while recipient_email == sender_email:
        recipient_email = random.choice(senders)
    recipient_name = recipient_email.split("@")[0].split(".")[0]
    return {
        "sender_name": sender_name,
        "recipient_name": recipient_name,
        "last_email_id": last_email_id,
        "recipient_email": recipient_email,
    }


def send_email_logic():
    index = random.randint(0, len(subjects) - 1)
    body = bodies[index]
    subject = subjects[index]
    recipient_email = random.choice(senders)
    name = recipient_email.split("@")[0].split(".")[0]
    return {
        "body": body,
        "subject": subject,
        "name": name,
        "recipient_email": recipient_email,
    }


MULTI_ACTION_EMAIL_TEMPLATES = [
    {
        "query": "Delete my last email from {name}",
        "answer": ["""email.delete_email.func(email_id='{last_email_id}')"""],
        "logic": delete_last_email_logic,
    },
    {
        "query": "Forward my most recent email from {sender_name} to {recipient_name}",
        "answer": ["""email.forward_email.func(email_id='{last_email_id}', recipient='{recipient_email}')"""],
        "logic": forward_email_logic,
    },
    {
        "query": "Send an email to {name} saying '{body}' and title it '{subject}'",
        "answer": ["""email.send_email.func(recipient='{recipient_email}', subject='{subject}', body='{body}')"""],
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

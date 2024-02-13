import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.data_generation_utils import (
    get_natural_language_date,
)
from src.evals.utils import generate_all_questions_and_answers
random.seed(42)

emails_data = pd.read_csv("data/processed/emails.csv", dtype=str)
email_ids = list(emails_data["email_id"].unique())
subjects = list(emails_data["subject"].unique())
senders = list(emails_data["sender/recipient"].unique())
bodies = list(emails_data["body"].unique())
datetimes = list(emails_data["sent_datetime"].str.split(" ").str[0].unique())


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

SINGLE_ACTION_TEMPLATES = [
    {
        "question": "Send an email to {recipient} saying '{body}' and title it '{subject}'",
        "answer": [
            """email.send_email.func(recipient='{recipient}', subject='{subject}', body='{body}')"""
        ],
        "logic": send_email_logic
    },
]

# Generate a limited number of unique email action questions and answers
generated_questions_and_answers = []
max_questions_per_template = 10  # Limit the number of questions per template

if __name__ == "__main__":
    generated_questions_and_answers = generate_all_questions_and_answers(SINGLE_ACTION_TEMPLATES, max_questions_per_template)
    df = pd.DataFrame(generated_questions_and_answers)
    df.to_csv(
        "data/processed/email_questions_and_answers_single_action.csv",
        index=False,
        quoting=csv.QUOTE_ALL,
    )

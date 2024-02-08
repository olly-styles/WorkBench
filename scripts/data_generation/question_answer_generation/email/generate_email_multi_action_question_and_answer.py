import pandas as pd
import random
import csv
import sys
import os

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.data_generation_utils import get_natural_language_date
from src.tools import email

random.seed(42)

MULTI_ACTION_EMAIL_TEMPLATES = [
    {
        "question": "Find the first email on {natural_language_date} and delete it",
        "answer": """email.delete_email.func(email_id='{first_email_id}')""",
    },
    {
        "question": "Find the last email on {natural_language_date} and send an email to the sender with the subject '{subject}' and body '{body}'",
        "answer": """email.send_email.func(recipient='{last_email_sender}', subject='{subject}', body='{body}')""",
    },
    {
        "question": "Find the last email on {natural_language_date} and forward it to {recipient}",
        "answer": """email.forward_email.func(email_id='{last_email_id}', recipient='{recipient}')""",
    },
]

emails_data = pd.read_csv("data/processed/emails.csv", dtype=str)
email_ids = list(emails_data["email_id"].unique())
subjects = list(emails_data["subject"].unique())
senders = list(emails_data["sender"].unique())
dates = list(emails_data["sent_date"].str.split(" ").str[0].unique())
bodies = list(emails_data["body"].unique())

# Generate a limited number of unique multi-action questions and answers
generated_email_questions_and_answers = []
max_questions_per_template = 3  # Limit the number of questions per template

for template in MULTI_ACTION_EMAIL_TEMPLATES:
    for _ in range(max_questions_per_template):
        index = random.randint(0, len(subjects) - 1)
        body = bodies[index]
        subject = subjects[index]
        date = random.choice(dates)
        natural_language_date = get_natural_language_date(date)
        recipient = random.choice(senders)
        first_email_id = email.search_emails.func(date_min=date, date_max=date)[0][
            "email_id"
        ]
        last_email_id = email.search_emails.func(
            date_min=f"{date}", date_max=f"{date}"
        )[-1]["email_id"]
        last_email_sender = email.search_emails.func(
            date_min=f"{date}", date_max=f"{date}"
        )[-1]["sender"]

        question = template["question"].format(
            natural_language_date=natural_language_date,
            date=date,
            subject=subject,
            body=body,
            recipient=recipient,
        )
        answer = template["answer"].format(
            last_email_sender=last_email_sender,
            date=date,
            subject=subject,
            body=body,
            recipient=recipient,
            first_email_id=first_email_id,
            last_email_id=last_email_id,
        )
        questions = [q["question"] for q in generated_email_questions_and_answers]
        if question not in questions:
            generated_email_questions_and_answers.append(
                {"question": question, "answer": answer, "template": template}
            )


for question_and_answer in generated_email_questions_and_answers:
    print(question_and_answer["question"])
    print(question_and_answer["answer"])
    print(question_and_answer["template"])

df = pd.DataFrame(generated_email_questions_and_answers)
df.to_csv(
    "data/processed/email_questions_and_answers_multi_action.csv",
    index=False,
    quoting=csv.QUOTE_ALL,
)

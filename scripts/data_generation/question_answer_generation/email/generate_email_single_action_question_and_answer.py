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

random.seed(42)

SINGLE_ACTION_TEMPLATES = [
    {
        "question": "Search for emails containing '{query}'",
        "answer": """email.search_emails({{'query': '{query}'}})""",
    },
    {
        "question": "Send an email to {recipient} with subject '{subject}' and body '{body}'",
        "answer": """email.send_email({{'recipient': '{recipient}', 'subject': '{subject}', 'body': '{body}'}})""",
    },
    {
        "question": "Search for emails sent on {natural_language_date}",
        "answer": """email.search_emails({{'date_min': '{date}', 'date_max': '{date}'}})""",
    },
]

emails_data = pd.read_csv("data/processed/emails.csv", dtype=str)
email_ids = list(emails_data["email_id"].unique())
subjects = list(emails_data["subject"].unique())
senders = list(emails_data["sender"].unique())
bodies = list(emails_data["body"].unique())
dates = list(emails_data["sent_date"].str.split(" ").str[0].unique())

# Generate a limited number of unique email action questions and answers
generated_email_questions_and_answers = []
max_questions_per_template = 10  # Limit the number of questions per template

for template in SINGLE_ACTION_TEMPLATES:
    for _ in range(max_questions_per_template):
        # get a random index from the list of subjects
        index = random.randint(0, len(subjects) - 1)
        body = bodies[index]
        subject = subjects[index]
        recipient = random.choice(senders)
        query = random.choice(subjects)
        date = random.choice(dates)
        natural_language_date = get_natural_language_date(date)

        question = template["question"].format(
            subject=subject,
            recipient=recipient,
            body=body,
            query=query,
            natural_language_date=natural_language_date,
        )
        answer = template["answer"].format(
            subject=subject,
            recipient=recipient,
            body=body,
            query=query,
            date=date,
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
    "data/processed/email_questions_and_answers_single_action.csv",
    index=False,
    quoting=csv.QUOTE_ALL,
)

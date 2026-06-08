import random
from typing import Any

import numpy as np
import pandas as pd

from src.data_generation.data_generation_utils import (
    HARDCODED_CURRENT_TIME,
    get_first_name,
    random_choice_excluding,
    write_task_outcome_csv,
)
from src.evals.utils import generate_all_tasks_and_outcomes

emails_data: Any = None
subjects: Any = None
senders: Any = None
bodies: Any = None


def load_data() -> None:
    global emails_data, subjects, senders, bodies
    if emails_data is not None:
        return
    emails_data = pd.read_csv("data/processed/emails.csv", dtype=str)
    subjects = list(emails_data["subject"].unique())
    senders = list(emails_data["sender/recipient"].unique())
    bodies = list(emails_data["body"].unique())


def delete_last_email_logic() -> dict:
    sender = random.choice(senders)
    name = get_first_name(sender)
    last_email_id = emails_data[emails_data["sender/recipient"] == sender].iloc[-1]["email_id"]
    answer = [f"""email.delete_email.func(email_id="{last_email_id}")"""]
    return {
        "name": name,
        "last_email_id": last_email_id,
        "outcome": answer,
    }


def delete_last_days_emails_logic() -> dict:
    sender = random.choice(senders)
    name = get_first_name(sender)
    days = random.randint(2, 7)
    last_days_emails = emails_data[
        emails_data["sent_datetime"] >= str(HARDCODED_CURRENT_TIME - pd.Timedelta(days=days))
    ]
    last_days_emails = last_days_emails[last_days_emails["sender/recipient"] == sender]
    last_days_email_ids = last_days_emails["email_id"].tolist()
    answer = [f"""email.delete_email.func(email_id="{email_id}")""" for email_id in last_days_email_ids]
    return {
        "name": name,
        "days": days,
        "outcome": answer,
    }


def forward_recent_email_from_sender_logic() -> dict:
    sender_email = random.choice(senders)
    sender_name = get_first_name(sender_email)
    last_email_id = emails_data[emails_data["sender/recipient"] == sender_email].iloc[-1]["email_id"]
    recipient_email = random_choice_excluding(senders, sender_email)
    recipient_name = get_first_name(recipient_email)
    answer = [f"""email.forward_email.func(email_id="{last_email_id}", recipient="{recipient_email}")"""]
    return {
        "sender_name": sender_name,
        "recipient_name": recipient_name,
        "last_email_id": last_email_id,
        "recipient_email": recipient_email,
        "outcome": answer,
    }


def forward_recent_email_about_topic_logic() -> dict:
    email_subject = random.choice(subjects)
    email = emails_data[emails_data["subject"] == email_subject].iloc[-1]
    recipient_email = random_choice_excluding(senders, email["sender/recipient"])
    recipient_name = get_first_name(recipient_email)
    answer = [f"""email.forward_email.func(email_id="{email["email_id"]}", recipient="{recipient_email}")"""]
    return {
        "recipient_name": recipient_name,
        "recipient_email": recipient_email,
        "subject": email_subject,
        "outcome": answer,
    }


def forward_recent_email_about_topic_to_multiple_logic() -> dict:
    email_subject = random.choice(subjects)
    email = emails_data[emails_data["subject"] == email_subject].iloc[-1]
    recipient_emails = random.sample([e for e in senders if e != email["sender/recipient"]], k=2)
    recipient_names = [get_first_name(e) for e in recipient_emails]
    recipient_name1, recipient_name2 = recipient_names
    answer = [
        f"""email.forward_email.func(email_id="{email["email_id"]}", recipient="{recipient_email}")"""
        for recipient_email in recipient_emails
    ]
    return {
        "recipient_name1": recipient_name1,
        "recipient_name2": recipient_name2,
        "subject": email_subject,
        "outcome": answer,
    }


def reply_to_email_logic() -> dict:
    emails_data["name"] = emails_data["sender/recipient"].apply(get_first_name)
    email_subject = random.choice(subjects)
    name = get_first_name(random.choice(senders))
    selected_email_data = emails_data[(emails_data["subject"] == email_subject) & (emails_data["name"] == name)]

    # Keep looping until we find a subject and name that exists in the emails data and isn't a meeting reschedule
    while (len(selected_email_data) == 0) or (email_subject == "Meeting Rescheduled"):
        email_subject = random.choice(subjects)
        name = get_first_name(random.choice(senders))
        selected_email_data = emails_data[(emails_data["subject"] == email_subject) & (emails_data["name"] == name)]
    email_id = selected_email_data.sort_values("sent_datetime", ascending=False).iloc[0]["email_id"]

    del emails_data["name"]
    answer = [
        f"""email.reply_email.func(email_id="{email_id}", body="Thanks for the update - I will get back to you tomorrow.")"""
    ]
    return {
        "name": name,
        "email_id": email_id,
        "subject": email_subject,
        "outcome": answer,
    }


def reply_to_latest_email_logic() -> dict:
    sender_email = random.choice(senders)
    sender_name = get_first_name(sender_email)
    last_email_id = emails_data[emails_data["sender/recipient"] == sender_email].iloc[-1]["email_id"]
    answer = [f"""email.reply_email.func(email_id="{last_email_id}", body="Got it, thank you!")"""]
    return {
        "sender_name": sender_name,
        "outcome": answer,
    }


def replace_name(body: str, name: str) -> str:
    """Replaced the first occurance of "Sam" with the name of the email recipient. And replace the sign off with "Sam"."""
    lines = body.split("\\n")
    lines[-1] = "\\nSam"
    body = "\\n".join(lines)
    return body.replace("Sam", name, 1)


def send_email_logic() -> dict:
    index = random.randint(0, len(subjects) - 1)
    subject = subjects[index]
    recipient_email = random.choice(senders)
    name = get_first_name(recipient_email)
    body = bodies[index]
    body = replace_name(body, name)
    answer = [f"""email.send_email.func(recipient="{recipient_email}", subject="{subject}", body="{body}")"""]
    return {
        "body": body.replace("\\n", "\n"),
        "subject": subject,
        "name": name,
        "recipient_email": recipient_email,
        "outcome": answer,
    }


def forward_last_weeks_email_logic() -> dict:
    last_week_email = emails_data[
        (emails_data["sent_datetime"] >= "2023-11-20") & (emails_data["sent_datetime"] <= "2023-11-26")
    ]
    email = random.choice(last_week_email["sender/recipient"].unique())
    last_week_email = last_week_email[last_week_email["sender/recipient"] == email]
    subject = random.choice(last_week_email["subject"].unique())
    last_week_email = last_week_email[last_week_email["subject"] == subject]
    recipient_email = random_choice_excluding(senders, email)
    recipient_name = get_first_name(recipient_email)
    answer = [
        f"""email.forward_email.func(email_id="{email_id}", recipient="{recipient_email}")"""
        for email_id in last_week_email["email_id"]
    ]
    return {
        "name": get_first_name(email),
        "recipient_name": recipient_name,
        "recipient_email": recipient_email,
        "subject": subject,
        "outcome": answer,
    }


EMAIL_TEMPLATES = [
    {
        "task": "Delete my last email from {name}",
        "alternative_tasks": [
            "I need to delete my last email from {name}. Can you do that?",
            "{name} just sent me an email that I need to delete. Can you get rid of of the most recent email they sent me?",
        ],
        "logic": delete_last_email_logic,
    },
    {
        "task": "Delete all my emails from {name} from the last {days} days",
        "alternative_tasks": [
            "I need to get rid of all my emails from {name} from the last {days} days. Can you do delete them?",
            "All my emails from {name} from the last {days} days need to be deleted. Can you do that?",
        ],
        "logic": delete_last_days_emails_logic,
    },
    {
        "task": "Send an email to {name} saying '{body}' and title it '{subject}'",
        "alternative_tasks": [
            "please send an email to {name} saying '{body}' and title it '{subject}'",
            "I need to send an email to {name} saying '{body}' and title it '{subject}'. Can you do that?",
        ],
        "logic": send_email_logic,
    },
    {
        "task": "Reply to {name}'s last email about '{subject}' with 'Thanks for the update - I will get back to you tomorrow.'",
        "alternative_tasks": [
            "can you reply to {name}'s last email about '{subject}' with 'Thanks for the update - I will get back to you tomorrow.'",
            "I need to get back to {name}'s last email about '{subject}' with 'Thanks for the update - I will get back to you tomorrow. Can you send the reply for me?",
        ],
        "logic": reply_to_email_logic,
    },
    {
        "task": "Forward all the emails from {name} last week about '{subject}' to {recipient_name}",
        "alternative_tasks": [
            "{recipient_name} needs all the emails from {name} last week about '{subject}'. Can you forward them?",
            "can you forward all the emails from {name} last week about '{subject}' to {recipient_name}",
        ],
        "logic": forward_last_weeks_email_logic,
    },
    {
        "task": "Forward the latest email about '{subject}' to {recipient_name}",
        "alternative_tasks": [
            "{recipient_name} needs the latest email about '{subject}'. Can you forward it?",
            "can you forward the latest email about '{subject}' to {recipient_name}",
        ],
        "logic": forward_recent_email_about_topic_logic,
    },
    {
        "task": "Forward my most recent email from {sender_name} to {recipient_name}",
        "alternative_tasks": [
            "{recipient_name} needs my most recent email from {sender_name}. Can you forward it?",
            "can you forward my most recent email from {sender_name} to {recipient_name}",
        ],
        "logic": forward_recent_email_from_sender_logic,
    },
    {
        "task": "Forward the last email about '{subject}' to {recipient_name1} and {recipient_name2}",
        "alternative_tasks": [
            "{recipient_name1} and {recipient_name2} need the last email about '{subject}'. Can you forward it?",
            "can you forward the last email about '{subject}' to {recipient_name1} and {recipient_name2}",
        ],
        "logic": forward_recent_email_about_topic_to_multiple_logic,
    },
    {
        "task": "Reply to the latest email from {sender_name} with 'Got it, thank you!'",
        "alternative_tasks": [
            "can you reply to the latest email from {sender_name} with 'Got it, thank you!'",
            "I need to reply to the latest email from {sender_name} with 'Got it, thank you!'. Can you do that?",
        ],
        "logic": reply_to_latest_email_logic,
    },
]
for d in EMAIL_TEMPLATES:
    d["domains"] = ["email"]


def generate_task_and_outcome() -> None:
    load_data()
    np.random.seed(42)
    random.seed(42)
    max_tasks_per_template = 10  # Limit the number of tasks per template
    generated_tasks_and_outcomes = generate_all_tasks_and_outcomes(EMAIL_TEMPLATES, max_tasks_per_template)
    df = pd.DataFrame(generated_tasks_and_outcomes)
    write_task_outcome_csv(df, "data/processed/tasks_and_outcomes/email_tasks_and_outcomes.csv")


if __name__ == "__main__":
    generate_task_and_outcome()

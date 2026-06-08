import csv
import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

from src.data_generation.data_generation_utils import get_first_name

SEED_DATA_DIR = Path(__file__).parent.parent / "seed_data"
EMAIL_SEED = json.loads((SEED_DATA_DIR / "email.json").read_text())


# Update generate_email_content to include both events and tasks
def generate_email_content_updated(
    sender_email: str,
    event: str | None,
    is_long: bool = False,
    task: str | None = None,
    contains_typo: bool = False,
) -> str:
    greetings = ["Hi Sam,", "Hey Sam,", "Dear Sam,", "Sam,"]
    sender = get_first_name(sender_email).capitalize()
    bodies_event = [
        f"I'm reaching out to discuss our upcoming {event}. Can we schedule a meeting to go over the details?",
        f"I wanted to let you know that I've completed the tasks for the {event}. Looking forward to your feedback.",
        f"Could you provide your input on the {event} planning? Your insights would be really valuable.",
        f"Reminder about the {event} next week. Let's make sure we're all prepared.",
        f"I have some ideas for the {event} that I'd like to run by you. When are you free?",
        f"Encountered a few challenges while working on the {event}. Could use your advice.",
        "Thanks for the invite. Looking forward to it!",
    ]
    bodies_task = [
        f"Regarding task '{task}', I've made significant progress but have hit a snag with {random.choice(['database integration', 'UI responsiveness', 'third-party API compatibility'])}. Could use a brainstorm session.",
        f"Completed task '{task}' ahead of schedule. Please review and let me know if any tweaks are needed.",
        f"Starting on '{task}' today. Any preliminary thoughts or resources you recommend before I dive in?",
        f"I've been assigned '{task}'. Excited to work on this and confident it will greatly improve our {random.choice(['user experience', 'backend efficiency', 'security protocols'])}.",
    ]
    closings = ["Best,", "Regards,", "Cheers,", "Thanks,"]

    main_body = random.choice(bodies_task if task else bodies_event)
    if is_long:
        additional_content = [
            "\n\nAdditionally, I wanted to touch base on some other areas we've been focusing on lately. Our team has been working tirelessly on improving our project management workflows and enhancing collaboration across departments. This effort includes adopting new tools, refining our communication strategies, and ensuring that all team members are fully aligned with our objectives.",
            "\n\nI also wanted to share some exciting news about our upcoming team-building event. We've been planning a fun and engaging day for everyone, and I'm confident it will be a great opportunity for everyone to unwind and bond with their colleagues. I'll be sending out more details soon, so keep an eye out for that!",
            "\n\nI've been meaning to discuss the recent changes in our project timelines. We've had to make some adjustments to accommodate new client requirements and to ensure that we're delivering the best possible results. I'll be reaching out to you soon to discuss this in more detail, so please keep an eye out for my next email.",
        ]
        main_body += random.choice(additional_content)
    body = f"{random.choice(greetings)}\n\n{main_body}\n\n{random.choice(closings)}\n{sender}"
    possible_typos = EMAIL_SEED["typo_pairs"]
    if contains_typo:
        typos_in_body = [typo for typo in possible_typos if typo[0] in body]
        typo = random.choice(typos_in_body)
        body = body.replace(typo[0], typo[1])

    return body


def generate_data() -> None:
    random.seed(42)
    np.random.seed(42)
    tasks = EMAIL_SEED["tasks"]
    events = pd.read_csv("data/raw/events.csv", header=None)[0].tolist()

    sender_emails = pd.read_csv("data/raw/email_addresses.csv", header=None)[0].tolist()

    # Update the CSV file generation with these improvements
    filename_updated = "data/raw/email_content_pairs.csv"

    with open(filename_updated, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Subject", "Content", "Sender"])

        for i in range(500):
            sender_email = random.choice(sender_emails)
            if i % 2 == 0:  # Alternate between events and tasks
                event = random.choice(events)
                subject = f"Update on {event}"
                content = generate_email_content_updated(
                    sender_email, event, is_long=(i % 5 == 0), contains_typo=(i % 5 == 0)
                )
            else:
                task = random.choice(tasks)
                subject = f"Task Update on {task}"
                content = generate_email_content_updated(
                    sender_email, event=None, is_long=(i % 5 == 0), task=task, contains_typo=(i % 5 == 0)
                )
            writer.writerow([subject, content, sender_email])


if __name__ == "__main__":
    generate_data()

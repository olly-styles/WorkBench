import os
import random

import numpy as np
import pandas as pd
from tqdm import tqdm

from src.data_generation.data_generation_utils import create_email

CONTENT_PAIRS_PATH = "data/raw/email_content_pairs.csv"


def generate_data() -> None:
    random.seed(42)
    np.random.seed(42)
    if not os.path.exists(CONTENT_PAIRS_PATH):
        raise FileNotFoundError(
            f"Required email-content seed '{CONTENT_PAIRS_PATH}' is missing. The email sandbox data is sampled "
            f"from this committed corpus; regenerate it by running "
            f"scripts/data_generation/sandbox_databases/generate_email_content_pairs.py first "
            f"(note: regenerating it changes the email corpus and every downstream email/multi-domain task)."
        )
    email_content = pd.read_csv(CONTENT_PAIRS_PATH)

    # Create a DataFrame for the fake emails
    num_emails = 500
    emails_df = pd.DataFrame(
        columns=pd.Index(
            [
                "email_id",
                "inbox/outbox",
                "sender/recipient",
                "subject",
                "sent_datetime",
                "body",
            ]
        )
    )

    for _ in tqdm(range(num_emails)):
        email_id, sender, subject, sent_datetime, body = create_email(emails_df, email_content)
        emails_df.loc[len(emails_df)] = [
            email_id,
            "inbox",
            sender,
            subject,
            sent_datetime,
            body,
        ]

    emails_df = emails_df.sort_values(by="sent_datetime").reset_index(drop=True)
    emails_df["body"] = emails_df["body"].str.replace("\n", "\\n")  # replace newlines in bodies with \n
    emails_df.to_csv("data/processed/emails.csv", index=False)


if __name__ == "__main__":
    generate_data()

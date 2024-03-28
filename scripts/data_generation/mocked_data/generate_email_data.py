import pandas as pd
from tqdm import tqdm
import os
import sys
import numpy as np

project_root = os.path.abspath(os.path.curdir)
sys.path.append(project_root)

from src.data_generation.data_generation_utils import create_email


def generate_data():
    np.random.seed(42)
    email_content = pd.read_csv("data/raw/email_content_pairs.csv")

    # Create a DataFrame for the fake emails
    num_emails = 500
    emails_df = pd.DataFrame(
        columns=[
            "email_id",
            "inbox/outbox",
            "sender/recipient",
            "subject",
            "sent_datetime",
            "body",
        ]
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

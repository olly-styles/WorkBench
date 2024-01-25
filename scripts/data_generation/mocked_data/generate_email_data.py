import pandas as pd
import numpy as np
from tqdm import tqdm

from src.data_generation.calendar.data_generation_utils import create_email

sample_emails = pd.read_csv("data/raw/email_addresses.csv", header=None)
email_content_pairs = pd.read_csv("data/raw/email_content_pairs.csv")
email_content_pairs = dict(
    zip(email_content_pairs["Subject"], email_content_pairs["Content"])
)

# Create a DataFrame for the fake emails
num_emails = 500
emails_df = pd.DataFrame(columns=["email_id", "sender", "subject", "sent_date", "body"])

for _ in tqdm(range(num_emails)):
    email_id, sender, subject, sent_date, body = create_email(
        emails_df["email_id"], sample_emails, email_content_pairs
    )
    emails_df.loc[len(emails_df)] = [email_id, sender, subject, sent_date, body]

emails_df = emails_df.sort_values(by="sent_date").reset_index(drop=True)
emails_df.to_csv("data/processed/emails.csv", index=False)

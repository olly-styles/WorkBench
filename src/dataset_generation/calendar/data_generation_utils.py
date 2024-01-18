import pandas as pd
import numpy as np


def is_overlapping(new_start, new_end, existing_events):
    starts_during_existing = (new_start >= existing_events["event_start"]) & (
        new_start < existing_events["event_end"]
    )
    ends_during_existing = (new_end > existing_events["event_start"]) & (
        new_end <= existing_events["event_end"]
    )
    encompasses_existing = (new_start <= existing_events["event_start"]) & (
        new_end >= existing_events["event_end"]
    )

    overlap = starts_during_existing | ends_during_existing | encompasses_existing
    return overlap.any()


def create_calendar_event(event_names, emails, existing_events):
    while True:
        event_name = event_names.sample().iloc[0, 0]
        email = emails.sample().iloc[0, 0]
        event_start = generate_datetime_between(
            start=pd.to_datetime("2023-10-01T00:00:00"),
            end=pd.to_datetime("2023-12-31T23:59:59"),
        )
        event_end = event_start + pd.Timedelta(hours=generate_event_duration())
        event_id = str(len(existing_events)).zfill(8)

        # Check if the event time overlaps with an existing event time.
        # Note that this method is not very efficient, but it is good enough for this purpose. If you want to
        # generate a large dataset, you should use a more efficient method.
        if not is_overlapping(event_start, event_end, existing_events):
            return event_id, event_name, email, event_start, event_end


def generate_datetime_between(start, end):
    month = np.random.randint(start.month, end.month + 1)
    if month in [1, 3, 5, 7, 8, 10, 12]:
        day = np.random.randint(1, 31)
    elif month in [4, 6, 9, 11]:
        day = np.random.randint(1, 30)
    else:
        day = np.random.randint(1, 28)
    hour = np.random.randint(9, 16)
    minute = np.random.choice([0, 30])
    return pd.to_datetime(f"2023-{month}-{day}T{hour}:{minute}:00")


def generate_event_duration():
    return np.random.choice([1, 2, 3, 4, 5, 6]) * 0.5


def create_email(email_ids, sample_emails, email_content_pairs):
    email_id = str(len(email_ids)).zfill(8)
    recipient = sample_emails.sample().iloc[0, 0]
    subject = np.random.choice(list(email_content_pairs.keys()))
    body = email_content_pairs[subject]
    sent_date = generate_datetime_between(
        start=pd.to_datetime("2023-10-01T00:00:00"),
        end=pd.to_datetime("2023-12-31T23:59:59"),
    )
    return email_id, recipient, subject, sent_date, body

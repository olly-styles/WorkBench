import pandas as pd
import numpy as np

np.random.seed(42)


def is_overlapping(new_start, duration, existing_events):
    duration = pd.Timedelta(duration, unit="m")
    starts_during_existing = (new_start >= existing_events["event_start"]) & (
        new_start
        < existing_events["event_start"]
        + existing_events["duration"].apply(lambda x: pd.Timedelta(x, unit="m"))
    )
    ends_during_existing = (new_start + duration > existing_events["event_start"]) & (
        new_start + duration
        <= existing_events["event_start"]
        + existing_events["duration"].apply(lambda x: pd.Timedelta(x, unit="m"))
    )
    encompasses_existing = (new_start <= existing_events["event_start"]) & (
        new_start + duration
        >= existing_events["event_start"]
        + existing_events["duration"].apply(lambda x: pd.Timedelta(x, unit="m"))
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
        duration_minutes = generate_event_duration_minutes()
        event_id = str(len(existing_events)).zfill(8)

        # Check if the event time overlaps with an existing event time.
        # Note that this method is not very efficient, but it is good enough for this purpose. If you want to
        # generate a large dataset, you should use a more efficient method.
        if not is_overlapping(event_start, duration_minutes, existing_events):
            return event_id, event_name, email, event_start, duration_minutes


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


def get_natural_language_date(str_date):
    """Transforms a datetime string into just natural language date.

    Example: 2023-01-01 -> January 1
    """
    date = pd.to_datetime(str_date)
    return date.strftime("%B %d").lstrip("0").replace(" 0", " ")


def generate_event_duration():
    return np.random.choice([1, 2, 3, 4, 5, 6]) * 0.5


def generate_event_duration_minutes():
    duration_hours = generate_event_duration()
    return int(duration_hours * 60)


def format_event_duration(duration_minutes):
    """Format the duration of an event in natural language.

    Examples: 180 -> 3 hour, 30 -> 30 minute
    """
    if duration_minutes < 60:
        return f"{duration_minutes} minute"
    else:
        duration_hours = duration_minutes / 60
        duration_hours = (
            int(duration_hours)
            if int(duration_hours) == duration_hours
            else duration_hours
        )
        return f"{duration_hours} hour"


def generate_end_time(start_time, duration):
    """
    Generate the end time of an event given the start time and duration.
    """
    start = pd.to_datetime(start_time)
    duration_td = pd.Timedelta(duration)
    end_time = (start + duration_td).strftime("%Y-%m-%d %H:%M:%S")
    return end_time


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


def get_natural_language_time(str_time):
    """Transforms a datetime string into just natural language time.

    For example: 2023-01-01 09:30:00 -> 9.30, 2023-01-01 09:00:00 -> 9
    """
    str_time = str_time.split(":")
    if int(str_time[1]) > 0:
        new_start = str(int(str_time[0])) + "." + str_time[1]
    else:
        new_start = str(int(str_time[0]))
    return new_start

import pandas as pd
import numpy as np
from datetime import datetime

np.random.seed(42)
HARDCODED_CURRENT_TIME = pd.to_datetime("2023-11-30T00:00:00")
calendar_days_in_future = 31 # end date is 31 december
calendar_days_in_past = 90 # start date is 1 september


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


def event_on_the_same_day(new_start, event_name, existing_events):
    new_start_date = pd.to_datetime(new_start).date()
    same_day = existing_events[
        existing_events["event_start"].apply(lambda x: pd.to_datetime(x).date())
        == new_start_date
    ]
    return (same_day["event_name"] == event_name).any()


def create_calendar_event(event_names, emails, existing_events):
    while True:
        event_name = event_names.sample().iloc[0, 0]
        email = emails.sample().iloc[0, 0]
        event_start = generate_datetime_between(
            start=HARDCODED_CURRENT_TIME - pd.Timedelta(calendar_days_in_past, unit="d"),
            end=HARDCODED_CURRENT_TIME + pd.Timedelta(calendar_days_in_future, unit="d"),
        )
        duration_minutes = generate_event_duration_minutes()
        event_id = str(len(existing_events)).zfill(8)

        # Check if the event time overlaps with an existing event time and that there is no event with the same name on the same day.
        # Note that this method is not very efficient, but it is good enough for this purpose. If you want to
        # generate a large dataset, you should use a more efficient method.
        if (not is_overlapping(event_start, duration_minutes, existing_events)) and (
            not event_on_the_same_day(event_start, event_name, existing_events)
        ):
            return event_id, event_name, email, event_start, duration_minutes


# generate_datetime_between option do nearest 30 minutes or not
def generate_datetime_between(start, end, nearest_30_minutes=True):
    month = np.random.randint(start.month, end.month + 1)
    if month in [1, 3, 5, 7, 8, 10, 12]:
        day = np.random.randint(1, 31)
    elif month in [4, 6, 9, 11]:
        day = np.random.randint(1, 30)
    else:
        day = np.random.randint(1, 28)
    hour = np.random.randint(9, 16)
    if nearest_30_minutes:
        minute = np.random.choice([0, 30])
        seconds = "00"
    else:
        minute = np.random.randint(0, 60)
        seconds = str(np.random.randint(0, 60)).zfill(2)
    return pd.to_datetime(f"2023-{month}-{day}T{hour}:{minute}:{seconds}")


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


def create_email(existing_emails, sample_emails, email_content_pairs):
    email_id = str(len(existing_emails)).zfill(8)
    recipient = sample_emails.sample().iloc[0, 0]
    subject = np.random.choice(list(email_content_pairs.keys()))
    body = email_content_pairs[subject]
    sent_datetime = generate_datetime_between(
        start=pd.to_datetime("2023-10-01T00:00:00"),
        end=pd.to_datetime("2023-12-31T23:59:59"),
        nearest_30_minutes=False,
    )
    sent_date = sent_datetime.strftime("%Y-%m-%d")
    # generate another date if it's already in the emails or if there is already an email with the same subject on the same day
    if (
        sent_date
        in existing_emails["sent_datetime"].apply(lambda x: x.strftime("%Y-%m-%d"))
        or subject
        in existing_emails[
            existing_emails["sent_datetime"].apply(lambda x: x.strftime("%Y-%m-%d"))
            == sent_date
        ]["subject"].values
    ):
        return create_email(existing_emails, sample_emails, email_content_pairs)

    return email_id, recipient, subject, sent_datetime, body


def get_natural_language_time(str_time):
    """Transforms a datetime string into just natural language time.

    For example: 09:30:00 -> 9:30am, 13:00:00 -> 1pm
    """
    dt = datetime.strptime(str_time, "%H:%M:%S")
    if dt.minute == 0:
        return dt.strftime("%-I%p").lower()
    else:
        return dt.strftime("%-I:%M%p").lower()

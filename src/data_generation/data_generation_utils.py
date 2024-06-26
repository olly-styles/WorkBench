import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

np.random.seed(42)
HARDCODED_CURRENT_TIME = pd.to_datetime("2023-11-30T00:00:00")
calendar_days_in_future = 21  # end date is 21 december
calendar_days_in_past = 121  # start date is 1 august


def get_first_free_slot(date, original_events_on_date, duration_minutes):
    if original_events_on_date.empty:
        return pd.to_datetime(date).replace(hour=9, minute=0, second=0)

    events_df = original_events_on_date.copy()

    events_df["duration"] = pd.to_numeric(events_df["duration"])
    events_df["event_start"] = pd.to_datetime(events_df["event_start"])
    events_df["event_end"] = events_df["event_start"] + pd.to_timedelta(events_df["duration"], unit="m")

    # Define work hours
    work_start = events_df["event_start"].iloc[0].replace(hour=9, minute=0, second=0)
    work_end = events_df["event_start"].iloc[0].replace(hour=18, minute=0, second=0)

    # Sort events by start time
    events_df = events_df.sort_values(by="event_start")

    # Start checking from the beginning of the work day
    current_time = work_start
    for _, row in events_df.iterrows():
        if current_time + timedelta(minutes=duration_minutes) <= row["event_start"]:
            # Found a slot
            return current_time
        # Move to the end of the current meeting before checking the next slot
        current_time = max(current_time, row["event_end"])

    # Check if there's a slot at the end of the day
    if current_time + timedelta(minutes=duration_minutes) <= work_end:
        return current_time

    # If no slot found
    return None


def get_random_future_date(dates):
    date = random.choice(dates)
    while date < str(HARDCODED_CURRENT_TIME).split(" ")[0]:
        date = random.choice(dates)
    return date


def get_random_future_datetime(dates):
    date = get_random_future_date(dates)
    time = generate_datetime_between(
        start=pd.to_datetime(f"{date}T00:00:00"),
        end=pd.to_datetime(f"{date}T23:59:59"),
        nearest_30_minutes=True,
    )
    return time


def is_overlapping(new_start, duration, existing_events):
    duration = pd.Timedelta(duration, unit="m")
    starts_during_existing = (new_start >= existing_events["event_start"]) & (
        new_start
        < existing_events["event_start"] + existing_events["duration"].apply(lambda x: pd.Timedelta(x, unit="m"))
    )
    ends_during_existing = (new_start + duration > existing_events["event_start"]) & (
        new_start + duration
        <= existing_events["event_start"] + existing_events["duration"].apply(lambda x: pd.Timedelta(x, unit="m"))
    )
    encompasses_existing = (new_start <= existing_events["event_start"]) & (
        new_start + duration
        >= existing_events["event_start"] + existing_events["duration"].apply(lambda x: pd.Timedelta(x, unit="m"))
    )

    overlap = starts_during_existing | ends_during_existing | encompasses_existing
    return overlap.any()


def event_on_the_same_day(new_start, event_name, existing_events):
    new_start_date = pd.to_datetime(new_start).date()
    same_day = existing_events[
        existing_events["event_start"].apply(lambda x: pd.to_datetime(x).date()) == new_start_date
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
        # continue if the event start is on a weekend
        if event_start.weekday() in [5, 6]:
            continue
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
    min_day = start.day if month == start.month else 1
    max_day = end.day if month == end.month else 31
    # get max day accounting for months with different number of days
    max_day = min(max_day, 30) if month in [4, 6, 9, 11] else max_day
    max_day = min(max_day, 28) if month == 2 else max_day
    day = np.random.randint(min_day, max_day + 1)
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
    return np.random.choice([1, 2, 3, 4]) * 0.5


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
        duration_hours = int(duration_hours) if int(duration_hours) == duration_hours else duration_hours
        return f"{duration_hours} hour"


def generate_end_time(start_time, duration):
    """
    Generate the end time of an event given the start time and duration.
    """
    start = pd.to_datetime(start_time)
    duration_td = pd.Timedelta(duration)
    end_time = (start + duration_td).strftime("%Y-%m-%d %H:%M:%S")
    return end_time


def create_email(existing_emails, email_content):
    email_id = str(len(existing_emails)).zfill(8)
    email_content_pairs = email_content.sample().iloc[0].to_dict()
    recipient = email_content_pairs["Sender"]
    subject = email_content_pairs["Subject"]
    body = email_content_pairs["Content"]
    sent_datetime = generate_datetime_between(
        start=pd.to_datetime("2023-10-01T00:00:00"),
        end=HARDCODED_CURRENT_TIME,
        nearest_30_minutes=False,
    )
    sent_date = sent_datetime.strftime("%Y-%m-%d")
    # generate another date if it's already in the emails or if there is already an email with the same subject on the same day
    if (
        sent_date in existing_emails["sent_datetime"].apply(lambda x: x.strftime("%Y-%m-%d"))
        or subject
        in existing_emails[existing_emails["sent_datetime"].apply(lambda x: x.strftime("%Y-%m-%d")) == sent_date][
            "subject"
        ].values
    ):
        return create_email(existing_emails, email_content)

    return email_id, recipient, subject, sent_datetime, body


def get_natural_language_time(str_time):
    """Transforms a datetime string into just natural language time.

    For example: 09:30:00 -> 9:30am, 13:00:00 -> 1
    """
    dt = datetime.strptime(str_time, "%H:%M:%S")
    if dt.minute == 0:
        return dt.strftime("%-I%p").lower()[:-2]
    else:
        return dt.strftime("%-I:%M%p").lower()[:-2]
